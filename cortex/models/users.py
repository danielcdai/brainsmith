from cortex.storage.session import Base, get_db
from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional
from contextlib import contextmanager
from cortex.storage.session import User


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


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    profile_image_url: Optional[str] = None
    last_active_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    oauth_sub: Optional[str] = None

    class Config:
        orm_mode = True