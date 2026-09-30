#!/bin/bash
# Start Celery worker for Fake News Detection

cd "$(dirname "$0")/.."

# Create logs directory
mkdir -p logs

# Set Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Start worker
echo "Starting Celery worker..."
python -m task_queue.worker worker