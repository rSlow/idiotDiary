from sqlalchemy import Column, Integer, String, Boolean, Time
from sqlalchemy import ForeignKey
from sqlalchemy import select
from sqlalchemy.orm import relationship, selectinload

from .base import Base, Session


class User(Base):
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
    async def add_user(cls, user_data):
        async with Session() as session:
            async with session.begin():
                session.add(cls(user_id=user_data.id,
                                fullname=user_data.full_name,
                                username_mention=user_data.mention))

    @classmethod
    async def get(cls, user_id, session):
        result = await session.execute(
            select(cls).filter(cls.user_id == user_id).options(selectinload(cls.notify_times))
        )
        return result.scalars().one_or_none()

    @classmethod
    async def deactivate(cls, user_id):
        async with Session() as session:
            async with session.begin():
                q = select(cls).filter(cls.user_id == user_id)
                res = await session.execute(q)
                user = res.scalars().one()
                user.status = False

    @classmethod
    async def disable_notifications(cls, user_id):
        async with Session() as session:
            async with session.begin():
                q = select(cls).filter(cls.user_id == user_id)
                res = await session.execute(q)
                user = res.scalars().one()
                user.notify_status = False

    @classmethod
    async def enable_notifications(cls, user_id):
        async with Session() as session:
            async with session.begin():
                q = select(cls).filter(cls.user_id == user_id)
                res = await session.execute(q)
                user = res.scalars().one()
                user.notify_status = True


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    time = Column(Time)
    user = relationship("User",
                        back_populates="notify_times")

    @classmethod
    async def delete_notification(cls, user_id, time_obj, session):
        q = select(
            cls
        ).filter(
            Notification.user_id == user_id
        ).filter(
            Notification.time == time_obj
        )
        res = await session.execute(q)
        notification = res.scalars().one()
        await session.delete(notification)
