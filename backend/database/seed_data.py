# ml_core/database/seed_data.py

from sqlalchemy import create_engine
from .models import User, NewsArticle
from .postgres_connection import get_db_session
from sqlalchemy.orm import sessionmaker
from backend.database.schema import Base, NewsArticle   # use same Base
from backend.utils.config import get_settings
from utils.logger import get_logger

settings = get_settings()

# PostgreSQL Engine
engine = create_engine(settings.DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Database schema create karega (tables banayega)."""
    Base.metadata.create_all(bind=engine)

def seed_data():
    """Fake/Real news ke sample data insert karega."""
    session = SessionLocal()
    try:
        articles = [
            NewsArticle(
                title="NASA confirms water on Mars",
                content="NASA scientists have confirmed traces of water on Mars surface...",
                source="NASA",
                label="REAL"
            ),
            NewsArticle(
                title="Aliens built the Pyramids",
                content="Social media rumors claim aliens constructed the pyramids...",
                source="Unknown Blog",
                label="FAKE"
            ),
            NewsArticle(
                title="COVID-19 vaccine success rate 95%",
                content="Pfizer announced the COVID-19 vaccine shows 95% effectiveness...",
                source="BBC",
                label="REAL"
            ),
        ]

        session.add_all(articles)
        session.commit()
        print("✅ Seed data inserted successfully!")
    except Exception as e:
        print("❌ Error seeding data:", e)
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    init_db()
    seed_data()