import os
from datetime import timedelta

from celery import Celery

celery = Celery(
    "stt_task",
    broker=os.environ.get("CELERY_BROKER_URL"),
    backend=os.environ.get("CELERY_BACKEND_URL"),
)

celery.conf.update(
    # Acknowledge tasks only after they have been processed successfully
    task_acks_late=True,
    # Retry a task 3 times on failure
    task_retries=3,
    task_retry_delay=timedelta(seconds=10),
    # Delay before retrying a failed task
    # Set a time limit for tasks (in seconds)
    task_time_limit=1500,
    # Set a soft time limit (in seconds)
    task_soft_time_limit=1200,
    # Default queue for tasks
    task_default_queue="stt_queue",
    # Custom route for specific tasks
    task_routes={
        "app.api.tasks.stt_task": {"queue": "stt_queue"},
    },
    # Ensure tasks are durable (won’t be lost if the broker crashes)
    task_durable=True,
    # Default exchange to use
    task_default_exchange="default",
    # Exchange type (direct, fanout, etc.)
    task_default_exchange_type="direct",
    # Routing key to use
    task_default_routing_key="default",
    # Track task start time
    task_track_started=True,
    # Store results in Redis (configure for your setup)
    result_backend=os.environ.get("CELERY_BACKEND_URL"),
    # Time (in seconds) before results expire
    result_expires=3600,
    # Limit the number of tasks sent to a worker at once
    worker_prefetch_multiplier=1,
    # Max number of tasks before the worker is replaced
    worker_max_tasks_per_child=100,
)

celery.autodiscover_tasks(["app.api.tasks"])
