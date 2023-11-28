import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

Engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
Session = sessionmaker(bind=Engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


async def create_database():
    async with Engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
