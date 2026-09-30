# backend/database/enums.py
import enum

class TrainingStatusEnum(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
