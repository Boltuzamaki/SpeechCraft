import json
import logging
import os
import tempfile
import requests as http_requests

from app.extensions import db
from app.main.utils import create_srt_content, embed_subtitles_with_ffmpeg

from app.models import TranscriptionJob, TranscriptSegment
from app.utils import process_file_upload, send_transcription_request
from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user, login_required
main = Blueprint("main", __name__)


@main.route("/health")
def health():
    """Health check endpoint for Docker."""
    return jsonify({"status": "ok"}), 200


@main.route("/api/services/health")
def services_health():
    """Check health of all services and return their status."""
    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")

    # Check backend
    backend_status = "offline"
    try:
        resp = http_requests.get(f"{backend_url}/health", timeout=3)
        backend_status = "online" if resp.status_code == 200 else "offline"
    except Exception:
        backend_status = "offline"

    # Check celery via backend worker endpoint (best-effort)
    celery_status = "unknown"
    try:
        resp = http_requests.get(f"{backend_url}/worker/health", timeout=3)
        celery_status = "online" if resp.status_code == 200 else "offline"
    except Exception:
        celery_status = "unknown"

    return jsonify({
        "frontend": "online",
        "backend": backend_status,
        "celery": celery_status,
    })


@main.route("/")
def index():
    """Renders the landing page."""
    return render_template("index.html", user=current_user)


@main.route("/workspace")
@login_required
def workspace():
    """Displays the user's workspace with all their transcription jobs."""
    user_jobs = (
        TranscriptionJob.query.filter_by(user_id=current_user.id)
        .order_by(TranscriptionJob.created_at.desc())
        .all()
    )
    return render_template(
        "workspace.html",
        user=current_user,
        jobs=user_jobs,
        current_job=None,
        segments=None,
    )


@main.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected for upload"}), 400

    try:
        # Extract audio, store files, return base64 audio_data
        result = process_file_upload(file, current_user.id)
        if not result["success"]:
            return jsonify({"error": result["error"]}), 400

        # Create transcription job
        job = TranscriptionJob(
            user_id=current_user.id,
            filename=result["filename"],
            file_type=result["file_type"],
            status="processing",
            original_file_url=result.get("original_url"),
            storage_type=result.get("storage_type"),
            storage_key=result.get("storage_key"),
            audio_file_url=result.get("audio_url"),
        )
        db.session.add(job)
        db.session.commit()

        # Send transcription request
        callback_url = (current_app.config.get("CALLBACK_URL") or "").rstrip("/") + "/callback"
        model_name = request.form.get("model_name") or request.json and request.json.get("model_name")
        api_result = send_transcription_request(
            result["audio_data"], callback_url, model_name=model_name
        )

        if api_result.get("success") and api_result.get("response", {}).get(
            "task_id"
        ):
            job.api_task_id = api_result["response"]["task_id"]
            db.session.commit()
            return jsonify(
                {
                    "success": True,
                    "job_id": job.id,
                    "file_type": job.file_type,
                    "original_url": job.original_file_url,
                    "message": "File uploaded successfully. Transcription started.",  # noqa
                }
            )
        else:
            job.status = "error"
            db.session.commit()
            return (
                jsonify(
                    {
                        "error": api_result.get(
                            "error", "Transcription API failed."
                        )
                    }
                ),
                500,
            )

    except Exception as e:
        logging.error(f"Unexpected error during upload: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": "Internal server error occurred."}), 500


@main.route("/callback", methods=["POST"])
def transcription_callback():
    """Handles the async callback from the transcription API."""
    callback_data = request.get_json()
    if not callback_data or "task_id" not in callback_data:
        logging.warning("Callback received with no data or task_id.")
        return jsonify({"error": "Invalid callback payload"}), 400

    api_task_id = callback_data["task_id"]
    logging.info(f"Received callback for api_task_id: {api_task_id}")

    job = TranscriptionJob.query.filter_by(
        api_task_id=api_task_id
    ).first_or_404()

    try:
        api_status = callback_data.get("status")
        job.transcription_data = json.dumps(callback_data)

        if api_status == "success":
            job.status = "completed"
            transcription_payload = callback_data.get("data", {})
            transcribed_text_data = transcription_payload.get(
                "transcribed_text", {}
            )
            segments = transcribed_text_data.get("segments", [])

            TranscriptSegment.query.filter_by(
                transcription_job_id=job.id
            ).delete()

            for segment_data in segments:
                db.session.add(
                    TranscriptSegment(
                        transcription_job_id=job.id,
                        segment_id=segment_data.get("id"),
                        start_time=segment_data.get("start"),
                        end_time=segment_data.get("end"),
                        original_text=segment_data.get("text", "").strip(),
                    )
                )
        else:
            job.status = "error"
            logging.error(f"Job {job.id} (API Task {api_task_id}) failed.")

        db.session.commit()
        return jsonify({"status": "callback_processed"})

    except Exception as e:
        logging.error(
            f"Error processing callback for api_task_id {api_task_id}: {e}",
            exc_info=True,
        )
        db.session.rollback()
        return (
            jsonify(
                {"error": "Internal server error during callback processing"}
            ),
            500,
        )


@main.route("/callback/<int:job_id>", methods=["POST"])
def transcription_callback_with_job_id(job_id):
    """Handle transcription completion callback from API with job ID in URL"""
    try:
        job = db.get_or_404(TranscriptionJob, job_id)

        # Get the transcription data from the callback
        callback_data = request.get_json()

        if callback_data.get("status") == "Transcription successful":
            job.status = "completed"
            job.transcription_data = json.dumps(callback_data)

            # Parse segments and save them for editing
            text_data = callback_data.get("text", {})
            segments = text_data.get("segments", [])

            # Clear existing segments
            TranscriptSegment.query.filter_by(
                transcription_job_id=job.id
            ).delete()

            for segment in segments:
                transcript_segment = TranscriptSegment(
                    transcription_job_id=job.id,
                    segment_id=segment["id"],
                    start_time=segment["start"],
                    end_time=segment["end"],
                    original_text=segment["text"],
                )
                db.session.add(transcript_segment)
        else:
            job.status = "error"

        db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        logging.error(f"Callback error: {str(e)}")
        return jsonify({"error": "Callback processing failed"}), 500


@main.route("/job/<int:job_id>")
@login_required
def view_job(job_id):
    """View transcription job details."""
    job = TranscriptionJob.query.filter_by(
        id=job_id,
        user_id=current_user.id,
    ).first_or_404()

    segments = (
        TranscriptSegment.query.filter_by(transcription_job_id=job.id)
        .order_by(TranscriptSegment.start_time)
        .all()
    )

    all_jobs = (
        TranscriptionJob.query.filter_by(user_id=current_user.id)
        .order_by(TranscriptionJob.created_at.desc())
        .all()
    )

    return render_template(
        "workspace.html",
        user=current_user,
        current_job=job,
        segments=segments,
        jobs=all_jobs,
    )


@main.route("/edit_segment/<int:segment_id>", methods=["POST"])
@login_required
def edit_segment(segment_id):
    """Edit a transcript segment."""
    segment = db.get_or_404(TranscriptSegment, segment_id)
    if segment.transcription_job.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    new_text = data.get("text", "").strip() if data else ""
    if not new_text:
        return jsonify({"error": "Text cannot be empty"}), 400

    segment.edited_text = new_text
    db.session.commit()
    return jsonify(
        {"success": True, "message": "Segment updated successfully"}
    )


@main.route("/job_status/<int:job_id>")
@login_required
def job_status(job_id):
    """Get job status for frontend polling."""
    job = TranscriptionJob.query.filter_by(
        id=job_id, user_id=current_user.id
    ).first_or_404()

    return jsonify(
        {
            "status": job.status,
            "filename": job.filename,
            "created_at": job.created_at.isoformat(),
        }
    )


@main.route("/embed_subtitles", methods=["POST"])
@login_required
def embed_subtitles():
    """Embed subtitles into video file"""
    try:
        data = request.get_json()
        job_id = data.get("job_id")
        settings = data.get("settings", {})

        if not job_id:
            return jsonify({"error": "Missing job ID"}), 400

        job = TranscriptionJob.query.filter_by(
            id=job_id, user_id=current_user.id
        ).first()

        if not job or job.file_type != "video":
            return jsonify({"error": "Video job not found"}), 404

        segments = (
            TranscriptSegment.query.filter_by(transcription_job_id=job.id)
            .order_by(TranscriptSegment.start_time)
            .all()
        )

        if not segments:
            return jsonify({"error": "No transcript segments found"}), 404

        srt_content = create_srt_content(segments)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".srt", delete=False
        ) as srt_file:
            srt_file.write(srt_content)
            srt_path = srt_file.name

        try:
            embedded_result = embed_subtitles_with_ffmpeg(
                job.original_file_url, srt_path, settings, job.id
            )

            if embedded_result["success"]:
                return jsonify(
                    {
                        "success": True,
                        "embedded_url": embedded_result["url"],
                        "message": "Subtitles embedded successfully",
                    }
                )
            else:
                return jsonify({"error": embedded_result["error"]}), 500

        finally:
            if os.path.exists(srt_path):
                os.unlink(srt_path)

    except Exception as e:
        logging.error(f"Subtitle embedding error: {str(e)}")
        return jsonify({"error": "Failed to embed subtitles"}), 500
