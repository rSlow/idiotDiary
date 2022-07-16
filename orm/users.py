from sqlalchemy import Column, Integer, String, Boolean, Time
from sqlalchemy import ForeignKey
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

# USERNAME = "ktabelpb"
# PASSWORD = "Qt-MOrtH0FKw15GA80G5dQBWqgxK4BAA"
# HOST = "heffalump.db.elephantsql.com"
# DATABASE = "ktabelpb"
#
# SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{USERNAME}:{PASSWORD}@{HOST}/{DATABASE}"
SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///database.sqlite3"

UsersEngine = create_async_engine(SQLALCHEMY_DATABASE_URL)
UsersSession = sessionmaker(bind=UsersEngine, expire_on_commit=False, class_=AsyncSession)
UsersBase = declarative_base()


class User(UsersBase):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    fullname = Column(String)
    username_mention = Column(String)
    status = Column(Boolean, default=True)
    notify_status = Column(Boolean, default=False)
    notify_group = Column(String, default="")
    notify_times = relationship("Notification",
                                back_populates="user",
                                cascade="all, delete, delete-orphan")

    @classmethod
    async def add_new_user(cls, user_data):
        async with UsersSession() as session:
            async with session.begin():
                session.add(cls(user_id=user_data.id,
                                fullname=user_data.full_name,
                                username_mention=user_data.mention))

    @classmethod
    async def get(cls, user_id, session):
        result = await session.execute(
            select(cls).filter(cls.user_id == user_id)
            # options(selectinload(cls.image_ids))
        )
        return result.scalars().one()

    @classmethod
    async def deactivate(cls, user_id):
        with UsersSession.begin() as session:
            user = session.query(cls).filter(cls.user_id == user_id).one()
            user.status = False

    @classmethod
    async def disable_notifications(cls, user_id):
        with UsersSession.begin() as session:
            user = session.query(cls).filter(cls.user_id == user_id).one()
            user.notify_status = False


class Notification(UsersBase):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    time = Column(Time)
    user = relationship("User",
                        back_populates="notify_times")
