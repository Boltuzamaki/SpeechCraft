import os

import uvicorn
from celery import Celery
from fastapi import FastAPI

from app.api.router import router

app = FastAPI()
app.include_router(router)


@app.get("/status")
def status():
    return {"status": "App is running healthy!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/worker/health")
def worker_health():
    """Ping the Celery broker to verify at least one worker is reachable."""
    try:
        _celery = Celery(
            broker=os.environ.get("CELERY_BROKER_URL"),
            backend=os.environ.get("CELERY_RESULT_BACKEND"),
        )
        inspect = _celery.control.inspect(timeout=2)
        active = inspect.ping()
        _celery.backend.client.close() if hasattr(_celery, "backend") else None
        if active:
            return {"status": "ok", "workers": list(active.keys())}
        return {"status": "no_workers"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/")
def index():
    """
    Root endpoint of the application.

    Returns:
        str: A string indicating the service name and version.
    """
    return "STT Service (0.1)"


if __name__ == "__main__":
    """
    Entry point for running the application using Uvicorn.

    Runs the FastAPI app on host 0.0.0.0 and port 8000.
    """
    uvicorn.run(app, host="0.0.0.0", port=8000)
