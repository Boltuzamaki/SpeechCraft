import base64
import io
import logging
import os
import subprocess
import tempfile

import ffmpeg
import requests
from app.storage import storage_manager
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

# Allowed file extensions
ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "ogg", "m4a", "flac", "aac", "webm"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm", "flv"}
ALLOWED_EXTENSIONS = ALLOWED_AUDIO_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS

# API endpoint
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_ENDPOINT = f"{BACKEND_URL}/stt"


def allowed_file(filename):
    """Check if file extension is allowed"""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS  # noqa
    )


def is_video_file(filename):
    """Check if file is a video file"""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()  # noqa
        in ALLOWED_VIDEO_EXTENSIONS  # noqa
    )


def extract_audio_from_video(
    video_path,
    output_path,
):
    """Extract audio from video file using FFmpeg"""
    try:
        (
            ffmpeg.input(video_path)
            .output(
                output_path,
                acodec="libmp3lame",
                ac=1,
                ar="16000",
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return True
    except ffmpeg.Error as e:
        logging.error(f"FFmpeg error: {e.stderr.decode()}")
        return False
    except Exception as e:
        logging.error(f"Audio extraction error: {str(e)}")
        return False


def file_to_base64(file_path):
    """Convert file to base64 string"""
    try:
        with open(file_path, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode("utf-8")
            return encoded_string
    except Exception as e:
        logging.error(f"Base64 encoding error: {str(e)}")
        return None


def process_file_upload(file, user_id):
    """Process uploaded file: handles storage and audio extraction for videos."""
    try:
        if not file or file.filename == "":
            return {"success": False, "error": "No file provided"}

        if not allowed_file(file.filename):
            return {"success": False, "error": "File type not supported"}

        filename = secure_filename(file.filename)
        file_type = "video" if is_video_file(filename) else "audio"

        # Upload original media file
        upload_result = storage_manager.upload_file(file, user_id, "media")
        if not upload_result["success"]:
            return {
                "success": False,
                "error": "Failed to upload file to storage",
            }

        response = {
            "success": True,
            "filename": filename,
            "file_type": file_type,
            "original_url": upload_result["url"],
            "storage_type": upload_result["storage_type"],
            "storage_key": upload_result.get("key")
            or f"media/{upload_result['filename']}",
        }

        # If video, extract audio using ffmpeg
        if file_type == "video":
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(filename)[1]
            ) as temp_input:
                file.stream.seek(0)
                temp_input.write(file.read())
                temp_input_path = temp_input.name

            audio_path = temp_input_path.replace(
                os.path.splitext(temp_input_path)[1], ".mp3"
            )

            try:
                # Extract audio using FFmpeg
                subprocess.run(
                    [
                        "ffmpeg",
                        "-i",
                        temp_input_path,
                        "-q:a",
                        "0",
                        "-map",
                        "a",
                        "-y",
                        audio_path,
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                # Read audio content
                with open(audio_path, "rb") as audio_file:
                    audio_content = audio_file.read()

                # Save to new temp file and wrap as FileStorage
                with tempfile.NamedTemporaryFile(
                    suffix=".mp3", delete=False
                ) as temp_audio:
                    temp_audio.write(audio_content)
                    temp_audio_path = temp_audio.name

                with open(temp_audio_path, "rb") as audio_fp:
                    wrapped_file = FileStorage(
                        stream=audio_fp,
                        filename=f"{os.path.splitext(filename)[0]}_extracted.mp3",
                        content_type="audio/mpeg",
                    )
                    audio_upload = storage_manager.upload_file(
                        wrapped_file, user_id, "audio"
                    )

                if audio_upload["success"]:
                    response["audio_url"] = audio_upload["url"]
                    response["audio_storage_key"] = audio_upload.get("key")
                    response["audio_data"] = base64.b64encode(
                        audio_content
                    ).decode("utf-8")
                else:
                    logging.warning("Audio extracted but failed to upload")
                    response["audio_url"] = None
                    response["audio_data"] = None

            finally:
                for path in [temp_input_path, audio_path, temp_audio_path]:
                    if path and os.path.exists(path):
                        os.remove(path)

        elif file_type == "audio":
            file.stream.seek(0)
            audio_bytes = file.read()
            response["audio_data"] = base64.b64encode(audio_bytes).decode(
                "utf-8"
            )
            response["audio_url"] = upload_result["url"]

        return response

    except Exception as e:
        logging.error(f"File processing error: {str(e)}", exc_info=True)
        return {"success": False, "error": "File processing failed"}


def process_audio_data(audio_base64, job_id):
    """Process base64 audio data from client-side extraction"""
    try:
        import io

        from storage import storage_manager

        # Decode base64 audio data
        audio_data = base64.b64decode(audio_base64)

        # Create file-like object
        audio_file = io.BytesIO(audio_data)
        audio_file.name = f"audio_{job_id}.wav"  # Default to WAV format

        # Upload audio to storage
        upload_result = storage_manager.upload_file(
            audio_file, str(job_id), "audio"
        )

        if upload_result["success"]:
            return {
                "success": True,
                "audio_url": upload_result["url"],
                "storage_key": upload_result.get("key")
                or f"audio/{upload_result['filename']}",
            }
        else:
            return {"success": False, "error": "Failed to store audio data"}

    except Exception as e:
        logging.error(f"Audio processing error: {str(e)}")
        return {"success": False, "error": "Audio processing failed"}


def send_transcription_request(audio_data, callback_url, model_name=None):
    """Send transcription request to API"""
    try:
        payload = {"audio_data": audio_data, "callback_url": callback_url}
        if model_name:
            payload["model_name"] = model_name

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            API_ENDPOINT, json=payload, headers=headers, timeout=30
        )

        if response.status_code == 200:
            return {"success": True, "response": response.json()}
        else:
            logging.error(
                f"API error: {response.status_code} - {response.text}"
            )
            return {
                "success": False,
                "error": f"API request failed: {response.status_code}",
            }

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout"}
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {str(e)}")
        return {
            "success": False,
            "error": "Failed to connect to transcription service",
        }
    except Exception as e:
        logging.error(f"Transcription request error: {str(e)}")
        return {"success": False, "error": "Transcription request failed"}
