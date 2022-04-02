from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, Boolean, Time
from sqlalchemy import ForeignKey

SQLALCHEMY_DATABASE_URL = "sqlite:///databases/orm_database.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


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

    @staticmethod
    def get(user_id, session):
        return session.query(User).filter(User.user_id == user_id).one()

    @staticmethod
    def deactivate(user_id):
        with Session() as session:
            user = session.query(User).filter(User.user_id == user_id).one()
            user.status = False
            session.commit()

    @staticmethod
    def disable_notifications(user_id):
        with Session() as session:
            user = session.query(User).filter(User.user_id == user_id).one()
            user.notify_status = False
            session.commit()


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    time = Column(Time)
    user = relationship("User",
                        back_populates="notify_times")
