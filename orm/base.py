import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

USERNAME = os.getenv("DB_USERNAME")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
DATABASE = os.getenv("DB_DATABASE")

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{USERNAME}:{PASSWORD}@{HOST}/{DATABASE}"
# SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:////home/rslow/PycharmProjects/idiot_diary/orm/db.db"

Engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
Session = sessionmaker(bind=Engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


async def create_database():
    async with Engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

