import logging
import os
import shlex
import subprocess
import tempfile

import requests
from app.storage import storage_manager


def create_srt_content(segments):
    """Create SRT subtitle content from transcript segments"""
    srt_content = ""

    for i, segment in enumerate(segments, 1):
        start_time = format_srt_time(segment.start_time)
        end_time = format_srt_time(segment.end_time)
        text = segment.edited_text or segment.original_text

        srt_content += f"{i}\n"
        srt_content += f"{start_time} --> {end_time}\n"
        srt_content += f"{text}\n\n"

    return srt_content


def format_srt_time(seconds):
    """Format seconds to SRT time format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


def hex_to_ass_color(hex_color):
    """Convert #RRGGBB to ASS format &H00BBGGRR"""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "&H00FFFFFF"  # default to white
    bgr = hex_color[4:6] + hex_color[2:4] + hex_color[0:2]
    return f"&H00{bgr.upper()}"


class FileLike:
    """Wrapper for reading and saving video file as file-like object"""

    def __init__(self, path, name):
        self.file = open(path, "rb")
        self.filename = name
        self.content_type = "video/mp4"

    def read(self, *args):
        return self.file.read(*args)

    def save(self, destination):
        with open(destination, "wb") as out:
            self.file.seek(0)
            out.write(self.file.read())

    def close(self):
        self.file.close()


def embed_subtitles_with_ffmpeg(video_url, srt_path, settings, job_id):
    """Use FFmpeg to embed subtitles into video"""
    input_path = None
    output_path = None

    try:
        # Download video file if it's a URL or load locally
        with tempfile.NamedTemporaryFile(
            suffix=".mp4", delete=False
        ) as temp_video:
            if video_url.startswith("http"):
                response = requests.get(video_url)
                response.raise_for_status()
                temp_video.write(response.content)
            else:
                local_path = os.path.join("app", video_url.lstrip("/"))
                with open(local_path, "rb") as f:
                    temp_video.write(f.read())

            input_path = temp_video.name

        # Create output file
        with tempfile.NamedTemporaryFile(
            suffix=".mp4", delete=False
        ) as temp_output:
            output_path = temp_output.name

        # Build FFmpeg subtitle filter
        font_size = settings.get("fontSize", "24")
        font_color = settings.get("fontColor", "#ffffff")
        outline = settings.get("outline", True)

        ass_color = hex_to_ass_color(font_color)
        quoted_srt = shlex.quote(srt_path)

        style = f"FontSize={font_size},PrimaryColour={ass_color}"
        if outline:
            style += ",OutlineColour=&H80000000,Outline=2"

        subtitle_filter = f"subtitles={quoted_srt}:force_style='{style}'"

        cmd = [
            "ffmpeg",
            "-i",
            input_path,
            "-vf",
            subtitle_filter,
            "-c:a",
            "copy",
            "-y",
            output_path,
        ]

        # Run FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            # Upload embedded video
            file_obj = FileLike(output_path, f"embedded_{job_id}.mp4")
            upload_result = storage_manager.upload_file(
                file_obj, str(job_id), "embedded"
            )
            file_obj.close()

            if upload_result["success"]:
                return {
                    "success": True,
                    "url": upload_result["url"],
                    "storage_key": upload_result.get("key"),
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to upload embedded video",
                }
        else:
            logging.error(f"FFmpeg error: {result.stderr}")
            return {
                "success": False,
                "error": "Video processing failed",
                "details": result.stderr,
            }

    except Exception as e:
        logging.error(f"Subtitle embedding error: {str(e)}")
        return {"success": False, "error": str(e)}

    finally:
        # Clean up temporary files
        try:
            if input_path and os.path.exists(input_path):
                os.unlink(input_path)
            if output_path and os.path.exists(output_path):
                os.unlink(output_path)
        except Exception as cleanup_err:
            logging.warning(f"Temporary file cleanup failed: {cleanup_err}")
