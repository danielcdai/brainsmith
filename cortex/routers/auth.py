import httpx
import logging
from fastapi import  HTTPException,  APIRouter, Request
from fastapi.responses import RedirectResponse

from cortex.config import settings


router = APIRouter(prefix="/api/v1/auth")
client_id = settings.github_client_id
client_secret = settings.github_client_secret
redirect_uri = "/api/v1/auth/callback"

# TODO: Extract the GitHub OAuth login and callback logic into a separate module
# TODO: Encap all the constants into a class
@router.get("/login")
def github_login(request: Request):
    """Redirect user to GitHub OAuth authorization page."""
    base_url = str(request.base_url).rstrip("/")
    github_authorize_url = (
        f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={base_url}{redirect_uri}&scope=user"
    )
    return github_authorize_url


@router.get("/callback")
async def github_callback(request: Request, code: str):
    """Handle GitHub OAuth callback and exchange code for access token."""
    token_url = "https://github.com/login/oauth/access_token"
    base_url = str(request.base_url).rstrip("/")
    print('request_url: ', base_url)
    headers = {"Accept": "application/json"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": f'{base_url}{redirect_uri}',
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, headers=headers, data=data)
        response_data = response.json()
    if "access_token" not in response_data:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    access_token = response_data["access_token"]

    logging.info(f"User logged in with access token, redirect to callback URL")
    # return RedirectResponse(f"{base_url}/callback?access_token={access_token}")
    return RedirectResponse(url=f"/ui/callback?access_token={access_token}")
     

@router.get("/user")
async def get_user(request: Request):
    """Return the current logged-in user's information."""
    access_token = request.query_params.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="User not logged in")
    # Fetch user info
    user_info_url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        user_response = await client.get(user_info_url, headers=headers)
        user_data = user_response.json()
    return {"user": user_data}
