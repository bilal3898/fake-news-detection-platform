# task_queue/celeryconfig.py
"""
Celery configuration for Fake News Detection tasks
"""

import os
from datetime import timedelta
from backend.utils.config import get_settings

settings = get_settings()

# Broker and Result Backend settings
broker_url = settings.REDIS_URL
result_backend = settings.REDIS_URL

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Task routes
task_routes = {
    'task_queue.tasks.process_url_task': {'queue': 'url_processing'},
    'task_queue.tasks.train_model_task': {'queue': 'model_training'},
    'task_queue.tasks.*': {'queue': 'default'},
}

# Queue configuration
task_queues = {
    'default': {
        'exchange': 'default',
        'exchange_type': 'direct',
        'routing_key': 'default'
    },
    'url_processing': {
        'exchange': 'url_processing',
        'exchange_type': 'direct',
        'routing_key': 'url_processing'
    },
    'model_training': {
        'exchange': 'model_training',
        'exchange_type': 'direct',
        'routing_key': 'model_training'
    }
}

# Task timeouts
task_time_limit = 300  # 5 minutes
task_soft_time_limit = 240  # 4 minutes
task_always_eager = False  # Don't run tasks synchronously in development

# Result expiration
result_expires = 3600  # 1 hour

# Worker settings
worker_prefetch_multiplier = 1
worker_concurrency = 4
worker_max_tasks_per_child = 100
worker_max_memory_per_child = 200000  # 200MB

# Beat schedule (periodic tasks)
beat_schedule = {
    'scrape-news-every-hour': {
        'task': 'task_queue.tasks.scheduled_news_scraping',
        'schedule': timedelta(hours=1),
        'options': {'queue': 'url_processing'}
    },
    'clean-old-tasks-daily': {
        'task': 'task_queue.tasks.clean_old_tasks',
        'schedule': timedelta(days=1),
        'options': {'queue': 'default'}
    },
    'check-model-performance-daily': {
        'task': 'task_queue.tasks.check_model_performance',
        'schedule': timedelta(days=1),
        'options': {'queue': 'default'}
    },
}

# Task tracking
task_track_started = True
task_ignore_result = False
task_store_errors_even_if_ignored = True

# Security
worker_disable_rate_limits = True
broker_connection_retry_on_startup = True

# Monitoring
worker_send_task_events = True
task_send_sent_event = True

# Logging
worker_redirect_stdouts = True
worker_redirect_stdouts_level = 'INFO'

# Redis specific settings
broker_transport_options = {
    'visibility_timeout': 3600,  # 1 hour
    'socket_timeout': 30,
    'retry_on_timeout': True,
    'health_check_interval': 10,
}

# Task compression
task_compression = 'gzip'
result_compression = 'gzip'

# Task acks
task_acks_late = True
task_reject_on_worker_lost = True