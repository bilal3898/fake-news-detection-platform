from fastapi import Depends
from backend.services.prediction import prediction_service
from backend.database.mongo_connection import get_database

async def get_prediction_service():
    return prediction_service

async def get_db():
    return get_database()
