# task_queue/worker

#!/usr/bin/env python3
"""
Celery worker startup script for Fake News Detection tasks
"""

import os
import sys
import logging
from pathlib import Path
from celery import Celery
from celery.signals import after_setup_logger, after_setup_task_logger
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/celery_worker.log')
    ]
)

logger = logging.getLogger(__name__)

def setup_celery():
    """Initialize and configure Celery application"""
    try:
        # Create Celery app
        app = Celery('fake_news_worker')
        
        # Load configuration
        app.config_from_object('task_queue.celeryconfig')
        
        # Discover tasks
        app.autodiscover_tasks(['task_queue.tasks'])
        
        logger.info("Celery application configured successfully")
        return app
        
    except Exception as e:
        logger.error(f"Failed to configure Celery: {e}")
        raise

@after_setup_logger.connect
def setup_logger(logger, *args, **kwargs):
    """Configure logger for Celery"""
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    """Configure task logger for Celery"""
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def start_worker():
    """Start Celery worker"""
    try:
        app = setup_celery()
        
        logger.info("Starting Celery worker...")
        logger.info(f"Python path: {sys.path}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Worker options
        worker_options = {
            'hostname': 'fake-news-worker@%h',
            'loglevel': 'INFO',
            'traceback': True,
            'concurrency': 4,
            'queues': ['default', 'url_processing', 'model_training'],
            'without_mingle': False,
            'without_gossip': False,
            'pool': 'prefork',
        }
        
        # Start worker
        app.worker_main(
            argv=[
                'worker',
                '--loglevel=INFO',
                '--concurrency=4',
                '--queues=default,url_processing,model_training',
                '--hostname=fake-news-worker@%h',
                '--pool=prefork',
                '--without-mingle=False',
                '--without-gossip=False',
            ]
        )
        
    except Exception as e:
        logger.error(f"Failed to start Celery worker: {e}")
        sys.exit(1)

def start_beat():
    """Start Celery beat (scheduler)"""
    try:
        app = setup_celery()
        
        logger.info("Starting Celery beat scheduler...")
        
        # Start beat
        app.worker_main(
            argv=[
                'beat',
                '--loglevel=INFO',
                '--schedule=logs/celerybeat-schedule',
                '--pidfile=logs/celerybeat.pid'
            ]
        )
        
    except Exception as e:
        logger.error(f"Failed to start Celery beat: {e}")
        sys.exit(1)

def start_flower():
    """Start Flower monitoring (optional)"""
    try:
        app = setup_celery()
        
        logger.info("Starting Flower monitoring...")
        
        # Start Flower
        import subprocess
        subprocess.run([
            sys.executable, '-m', 'celery',
            '-A', 'task_queue.tasks',
            'flower',
            '--port=5555',
            '--loglevel=INFO'
        ])
        
    except Exception as e:
        logger.error(f"Failed to start Flower: {e}")
        sys.exit(1)

def show_queues():
    """Show current queue information"""
    try:
        app = setup_celery()
        
        # Inspect workers
        inspector = app.control.inspect()
        
        # Get active queues
        active_queues = inspector.active_queues()
        if active_queues:
            logger.info("Active queues:")
            for worker, queues in active_queues.items():
                for queue in queues:
                    logger.info(f"  {worker}: {queue['name']}")
        else:
            logger.info("No active queues found")
            
        # Get registered tasks
        registered_tasks = inspector.registered()
        if registered_tasks:
            logger.info("Registered tasks:")
            for worker, tasks in registered_tasks.items():
                for task in tasks:
                    logger.info(f"  {worker}: {task}")
        
    except Exception as e:
        logger.error(f"Failed to inspect queues: {e}")

def purge_queues():
    """Purge all messages from queues"""
    try:
        app = setup_celery()
        
        logger.warning("Purging all messages from queues...")
        
        # Purge all queues
        app.control.purge()
        
        logger.info("All queues purged successfully")
        
    except Exception as e:
        logger.error(f"Failed to purge queues: {e}")

if __name__ == '__main__':
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'worker':
            start_worker()
        elif command == 'beat':
            start_beat()
        elif command == 'flower':
            start_flower()
        elif command == 'queues':
            show_queues()
        elif command == 'purge':
            purge_queues()
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Available commands: worker, beat, flower, queues, purge")
            sys.exit(1)
    else:
        # Default: start worker
        start_worker()