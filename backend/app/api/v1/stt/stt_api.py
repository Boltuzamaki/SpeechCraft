import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.tasks import stt_task
from app.src.main_driver import main

router = APIRouter()

logger = logging.getLogger(__name__)


class STTRequest(BaseModel):
    audio_data: str
    callback_url: str = None

    class Config:
        extra = "allow"


@router.post("/stt", summary="Transcribe Audio")
async def stt_endpoint(request: STTRequest):
    """
    Endpoint to transcribe audio using the STT pipeline.

    - **With `callback_url`**: Schedules a background task via Celery and
                               returns a `task_id`.
      The result will be sent to the callback URL upon completion.
    - **Without `callback_url`**: Processes the request synchronously and
                                  returns the transcription directly.
    """
    request_dict = request.dict()

    if request.callback_url:
        try:
            task = stt_task.apply_async(kwargs=request_dict)
            return {
                "message": (
                    "Transcription task has been scheduled " "successfully."
                ),
                "task_id": task.id,
            }
        except Exception as e:
            logger.error(f"Failed to schedule Celery task: {e}")
            raise HTTPException(
                status_code=500,
                detail=(
                    "Internal server error: Could not "
                    "schedule transcription task."
                ),
            )

    else:
        try:
            result = await main(**request_dict)
            logger.info("Synchronous STT processing successful.")
            return {
                "status": "success",
                "data": result,
            }
        except Exception as e:
            logger.error(f"Failed to transcribe audio synchronously: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to transcribe: {e}"
            )
