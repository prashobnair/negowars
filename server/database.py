# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from server.config.settings import settings  # Updated import path
import logging

DATABASE_URL = settings.database_url  # Use the value defined in settings

engine = create_async_engine(DATABASE_URL, echo=True)  # echo=True logs SQL queries - useful for debugging
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

logger = logging.getLogger(__name__)

async def get_db():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    db = async_session()
    logger.info(f"Creating new session: {id(db)}")
    try:
        yield db
    finally:
        logger.info(f"Closing session: {id(db)}")
        await db.close()