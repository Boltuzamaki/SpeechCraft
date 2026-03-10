import asyncio
import traceback

from app.api.worker import celery
from app.src.main_driver import main
from app.utils.callbackhandler import send_callback


@celery.task(name="app.api.tasks.stt_task", bind=True)
def stt_task(self, **kwargs):
    """
    Celery task that runs the STT pipeline and handles sending the callback.
    'bind=True' gives access to the task instance via 'self.request'.
    """
    task_id = self.request.id
    callback_url = kwargs.get("callback_url")

    if not callback_url:
        raise ValueError("Callback URL is required for the STT task.")

    try:
        transcription_result = asyncio.run(main(**kwargs))

        # On success, prepare and send the success payload
        success_payload = {
            "task_id": task_id,
            "status": "success",
            "data": transcription_result,
        }

        asyncio.run(send_callback(callback_url, success_payload))

    except Exception as e:
        failure_payload = {
            "task_id": task_id,
            "status": "failed",
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        }

        asyncio.run(send_callback(callback_url, failure_payload))
