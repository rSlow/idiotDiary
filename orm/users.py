from sqlalchemy import Column, Integer, String, Boolean, Time
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

SQLALCHEMY_DATABASE_URL = "sqlite:///databases/users.db"

UsersEngine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
UsersSession = sessionmaker(autocommit=False, autoflush=False, bind=UsersEngine)

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
    def add_new_user(cls, user_data):
        with UsersSession.begin() as session:
            session.add(cls(user_id=user_data.id,
                            fullname=user_data.full_name,
                            username_mention=user_data.mention))

    @classmethod
    def get(cls, user_id, session):
        return session.query(cls).filter(cls.user_id == user_id).one()

    @classmethod
    def deactivate(cls, user_id):
        with UsersSession.begin() as session:
            user = session.query(cls).filter(cls.user_id == user_id).one()
            user.status = False

    @classmethod
    def disable_notifications(cls, user_id):
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
