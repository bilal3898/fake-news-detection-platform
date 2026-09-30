import logging
import sys
from loguru import logger
# Try relative imports first, fallback to absolute
try:
    from .config import get_settings
except ImportError:
    from utils.config import get_settings

settings = get_settings()

class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Map standard logging levels to loguru
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller frame
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    """Configure application logging (stdout + file + stdlib intercept)."""
    logger.remove()

    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level="DEBUG" if getattr(settings, "DEBUG", False) else "INFO",
        colorize=True,
    )

    # File handler
    logger.add(
        "logs/app.log",
        rotation="500 MB",
        retention="10 days",
        level="INFO"
    )

    # Redirect std logging → loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0)


def get_logger(name: str = None):
    """Return a logger instance. Optionally bind module name."""
    setup_logging()
    return logger if not name else logger.bind(module=name)
