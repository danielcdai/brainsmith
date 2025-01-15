from fastapi import  HTTPException,  APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx
from cortex.config import settings

router = APIRouter(prefix="/auth")
client_id = settings.github_client_id
client_secret = settings.github_client_secret
redirect_uri = "http://localhost:8000/auth/callback"


@router.get("/login")
def github_login():
    print("login")
    """Redirect user to GitHub OAuth authorization page."""
    github_authorize_url = (
        f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=user"
    )
    print(github_authorize_url)
    return github_authorize_url

@router.get("/callback")
async def github_callback(request: Request, code: str):
    """Handle GitHub OAuth callback and exchange code for access token."""
    print('callback')
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    print('client_secret: ', client_secret)
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }
    print('data: ', data)
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, headers=headers, data=data)
        response_data = response.json()
    print("GitHub response:", response_data) 
    if "access_token" not in response_data:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    access_token = response_data["access_token"]

    # Fetch user info
    # user_info_url = "https://api.github.com/user"
    # headers = {"Authorization": f"Bearer {access_token}"}
    # async with httpx.AsyncClient() as client:
    #     user_response = await client.get(user_info_url, headers=headers)
    #     user_data = user_response.json()

    # Store user info in session
    # request.session["user"] = user_data
    # request.session["access_token"] = access_token
    # return user_data
    return RedirectResponse(f"http://localhost:5173/callback?access_token={access_token}")
     
@router.get("/user")
async def get_user(request: Request):
    """Return the current logged-in user's information."""
    access_token = request.get("access_token")
    # user = request.session.get("user")
    # access_token = request.session.get("access_token")
    # if not user:
    #     raise HTTPException(status_code=401, detail="User not logged in")
    if not access_token:
        raise HTTPException(status_code=401, detail="User not logged in")
    # Fetch user info
    user_info_url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        user_response = await client.get(user_info_url, headers=headers)
        user_data = user_response.json()
    return {"user": user_data}
