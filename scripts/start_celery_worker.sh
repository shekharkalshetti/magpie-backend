#!/bin/bash

# Celery worker startup script for asynchronous task processing
# This script starts a Celery worker that processes moderation tasks

set -e

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default values
CELERY_LOGLEVEL=${CELERY_LOGLEVEL:-info}
CELERY_CONCURRENCY=${CELERY_CONCURRENCY:-4}
CELERY_QUEUES=${CELERY_QUEUES:-default,moderation}

# Print startup info
echo "Starting Celery worker..."
echo "Log level: $CELERY_LOGLEVEL"
echo "Concurrency: $CELERY_CONCURRENCY"
echo "Queues: $CELERY_QUEUES"
echo ""

# Start Celery worker
# -A specifies the Celery app module
# worker starts the worker process
# -l sets log level
# -c sets concurrency (number of worker processes)
# -Q specifies which task queues to listen on
# --loglevel sets the log verbosity
celery -A src.tasks.celery_app worker \
    --loglevel=$CELERY_LOGLEVEL \
    -c $CELERY_CONCURRENCY \
    -Q $CELERY_QUEUES \
    --soft-time-limit=30 \
    --time-limit=60 \
    --max-tasks-per-child=1000
