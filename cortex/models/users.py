from cortex.storage.session import Base, get_db
from sqlalchemy import BigInteger, Column, String, Text
from pydantic import BaseModel, ConfigDict
from typing import Optional
from contextlib import contextmanager


class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    # Disable role for now
    # role = Column(String)
    profile_image_url = Column(Text)

    last_active_at = Column(BigInteger)
    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)
    oauth_sub = Column(Text, unique=True)


class UserModel(BaseModel):
    id: str
    name: str
    email: str
    # Disable role for now
    # role: str = "pending"
    profile_image_url: str

    last_active_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch
    oauth_sub: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UsersTable:
    def get_user_by_email(self, email: str) -> Optional[UserModel]:
        try:
            manager = contextmanager(get_db)
            with manager() as db:
                user = db.query(User).filter_by(email=email).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def get_user_by_oauth_sub(self, sub: str) -> Optional[UserModel]:
        try:
            manager = contextmanager(get_db)
            with manager() as db:
                user = db.query(User).filter_by(oauth_sub=sub).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def update_user_oauth_sub_by_id(
        self, id: str, oauth_sub: str
    ) -> Optional[UserModel]:
        try:
            manager = contextmanager(get_db)
            with manager() as db:
                db.query(User).filter_by(id=id).update({"oauth_sub": oauth_sub})
                db.commit()

                user = db.query(User).filter_by(id=id).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

Users = UsersTable()