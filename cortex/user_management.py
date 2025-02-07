import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests
import jwt
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Response,
    Cookie,
)
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
)
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from jwt import PyJWTError
from cortex.config import settings

# === CONFIGURATION ===

# Database configuration (adjust your connection string accordingly)

DATABASE_URL = f"postgresql+psycopg2://postgres:{settings.postgres_password}@{settings.postgre_host}:{settings.postgre_port}/postgres" 
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base: DeclarativeMeta = declarative_base()

# JWT configuration
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# GitHub OAuth configuration (set these in your environment)
GITHUB_CLIENT_ID = settings.github_client_id
GITHUB_CLIENT_SECRET = settings.github_client_secret
GITHUB_OAUTH_REDIRECT_URI = os.getenv(
    "GITHUB_OAUTH_REDIRECT_URI", "http://localhost:8000/oauth/github/callback"
)
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API_URL = "https://api.github.com/user"

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# === DATABASE MODEL ===

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    # Store the hashed password; it can be null if the user is registered via OAuth.
    hashed_password = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    last_active_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Stores the unique identifier provided by the OAuth provider (GitHub, etc.)
    oauth_sub = Column(String, nullable=True)


# Create the database tables
Base.metadata.create_all(bind=engine)

# === UTILITY FUNCTIONS ===

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT token with an expiry."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# === Pydantic Schemas ===

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
    profile_image_url: str = None
    last_active_at: datetime = None
    updated_at: datetime = None
    created_at: datetime = None
    oauth_sub: str = None

    class Config:
        orm_mode = True


# === DEPENDENCIES ===

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Cookie(None), db=Depends(get_db)) -> User:
    """
    Extract the current user from the JWT token stored in the cookie.
    """
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user: User = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    # Optionally update the last_active_at timestamp
    user.last_active_at = datetime.utcnow()
    db.commit()
    return user


# === FASTAPI APPLICATION ===

app = FastAPI()


# --- Local Authentication Endpoints ---

@app.post("/auth/signup", response_model=UserResponse)
def signup(user: UserCreate, response: Response, db=Depends(get_db)):
    """
    Create a new user with a hashed password.
    """
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = get_password_hash(user.password)
    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_pw,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Issue JWT and set it as an HTTP‑only cookie
    access_token = create_access_token(data={"sub": new_user.id})
    response.set_cookie(key="token", value=access_token, httponly=True)
    return new_user


@app.post("/auth/login", response_model=UserResponse)
def login(login_data: LoginRequest, response: Response, db=Depends(get_db)):
    """
    Log in an existing user by verifying credentials.
    """
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not user.hashed_password or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Update last active time
    user.last_active_at = datetime.utcnow()
    db.commit()

    access_token = create_access_token(data={"sub": user.id})
    response.set_cookie(key="token", value=access_token, httponly=True)
    return user


@app.get("/auth/user", response_model=UserResponse)
def get_user(current_user: User = Depends(get_current_user)):
    """
    Return the current authenticated user's details.
    """
    return current_user


# --- GitHub OAuth Endpoints ---

@app.get("/oauth/github/login")
def github_login():
    """
    Redirect the user to GitHub's OAuth login page.
    """
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_OAUTH_REDIRECT_URI,
        "scope": "user:email",
    }
    url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    # Option 1: return a JSON with the URL so the frontend can redirect
    # return {"url": url}
    # Option 2: immediately redirect:
    return RedirectResponse(url)


@app.get("/oauth/github/callback")
def github_callback(code: str, response: Response, db=Depends(get_db)):
    """
    Handle the GitHub OAuth callback: exchange the code for an access token,
    fetch user info, register/login the user, and issue a JWT.
    """
    # Exchange code for access token
    headers = {"Accept": "application/json"}
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": GITHUB_OAUTH_REDIRECT_URI,
    }
    token_resp = requests.post(GITHUB_ACCESS_TOKEN_URL, headers=headers, data=data)
    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="GitHub token exchange failed")
    token_json = token_resp.json()
    github_access_token = token_json.get("access_token")
    if not github_access_token:
        raise HTTPException(status_code=400, detail="Failed to obtain access token from GitHub")

    # Fetch user info from GitHub
    headers = {"Authorization": f"token {github_access_token}"}
    user_resp = requests.get(GITHUB_USER_API_URL, headers=headers)
    if user_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from GitHub")
    github_user = user_resp.json()
    email = github_user.get("email")
    name = github_user.get("name") or github_user.get("login")
    profile_image_url = github_user.get("avatar_url")
    oauth_sub = str(github_user.get("id"))

    # In some cases, the user's email may not be public.
    # Optionally fetch the list of emails and choose the primary email.
    if not email:
        emails_resp = requests.get(GITHUB_USER_API_URL + "/emails", headers=headers)
        if emails_resp.status_code == 200:
            emails = emails_resp.json()
            primary_emails = [e for e in emails if e.get("primary")]
            if primary_emails:
                email = primary_emails[0].get("email")
            elif emails:
                email = emails[0].get("email")
    if not email:
        raise HTTPException(status_code=400, detail="GitHub email not found")

    # See if the user already exists; if not, create a new record (without a password)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name=name,
            email=email,
            hashed_password=None,  # No local password because this is an OAuth user.
            profile_image_url=profile_image_url,
            oauth_sub=oauth_sub,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update any changed details from GitHub
        user.name = name
        user.profile_image_url = profile_image_url
        user.oauth_sub = oauth_sub
        user.updated_at = datetime.utcnow()
        db.commit()

    # Issue JWT token and set it as a secure, HTTP‑only cookie.
    jwt_token = create_access_token(data={"sub": user.id})
    response.set_cookie(key="token", value=jwt_token, httponly=True)
    # Optionally, redirect to a frontend URL.
    return RedirectResponse(url="/auth/user")  # Adjust as needed.


# === RUN THE APPLICATION ===
# You can run this service with:
#     uvicorn user_management:app --reload