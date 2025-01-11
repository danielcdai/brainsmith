from fastapi import  HTTPException,  APIRouter, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from pydantic import BaseModel
from typing import Optional
from cortex.config import settings
router = APIRouter(prefix="/auth")
client_id = settings.client_id
client_secret = settings.client_secret
redirect_uri = 'http://127.0.0.1:5173/callback'

class TokenRequest(BaseModel):
    client_id: str
    client_secret: str
    code: str

class AuthResponse(BaseModel):
    token: str

router.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@router.post("/login")
def github_login():
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
    )
    return {"auth_url": github_auth_url}

@router.post("/callback")
async def github_callback(token_request: TokenRequest = Depends()):
    if token_request.client_id != client_id or token_request.client_secret != client_secret:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": token_request.client_id,
                "client_secret": token_request.client_secret,
                "code": token_request.code
            },
            headers={"Accept": "application/json"}
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get GitHub access token")

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        user_info_url = f"https://api.github.com/user"
        user_response = requests.get(user_info_url, headers={"Authorization": f"token {access_token}"})

        if user_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get GitHub user info")

        user_info = user_response.json()

        return user_info

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")
     

