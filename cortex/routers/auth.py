import logging
from fastapi import  HTTPException,  APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse

from cortex.config import settings
from cortex.admin.authenticate import (
    get_github_auth_url, 
    get_github_callback_response, 
    github_user_info
)


router = APIRouter(prefix="/api/v1/auth")
client_id = settings.github_client_id
client_secret = settings.github_client_secret
redirect_uri = "/api/v1/auth/callback"

# TODO: Extract the GitHub OAuth login and callback logic into a separate module
# TODO: Encap all the constants into a class

# TODO: Do not return url anymore, do the authentication request here
@router.get("/login")
async def github_login(request: Request):
    """Redirect user to GitHub OAuth authorization page."""
    base_url = str(request.base_url).rstrip("/")
    return await get_github_auth_url(base_url, settings.github_client_id, redirect_uri)


@router.get("/callback")
async def github_callback(request: Request, code: str):
    """Handle GitHub OAuth callback and exchange code for access token."""
    base_url = str(request.base_url).rstrip("/")
    full_base = f'{base_url}{redirect_uri}'
    try:
        access_token = await get_github_callback_response(client_id, client_secret, full_base, code)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    logging.info(f"User logged in with access token, redirect to callback URL")
    return RedirectResponse(url=f"/ui/callback?access_token={access_token}")
     

@router.get("/user")
async def get_user(access_token: str = None):
    """Return the current logged-in user's information."""
    if not access_token:
        raise HTTPException(status_code=401, detail="User not logged in")
    # Fetch user info
    user_data = await github_user_info(access_token)
    return JSONResponse(content={"user": user_data})
