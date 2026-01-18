"""
Celery configuration and setup for asynchronous task processing.

Handles async output moderation, logging, and other background tasks.
"""
from celery import Celery
from kombu import Exchange, Queue
import os

# Initialize Celery app
app = Celery(__name__)

# Load configuration from environment
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Configure Celery
app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
)

# Define task queues
default_exchange = Exchange("celery", type="direct")
app.conf.task_queues = (
    Queue(
        "default",
        exchange=default_exchange,
        routing_key="default",
        durable=True,
    ),
    Queue(
        "moderation",
        exchange=default_exchange,
        routing_key="moderation",
        durable=True,
    ),
)

# Route tasks to specific queues
app.conf.task_routes = {
    "src.tasks.moderation_tasks.moderate_output": {"queue": "moderation"},
}

# Import tasks to register them
from . import moderation_tasks  # noqa: F401, E402
