import logging
from typing import Optional
from fastapi import  HTTPException,  APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
import time
from jose import jwt
import redis
import httpx

from cortex.config import settings
from datetime import datetime
from cortex.admin.authenticate import (
    get_github_auth_url, 
    github_user_info,
    verify_jwt
)


router = APIRouter(prefix="/auth",  tags=["Authentication"])
client_id = settings.github_client_id
client_secret = settings.github_client_secret
redirect_uri = "/auth/github/callback"
r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=1)

# TODO: Extract the GitHub OAuth login and callback logic into a separate module
# TODO: Encap all the constants into a class

# TODO: Do not return url anymore, do the authentication request here
@router.get("/github/login")
async def github_login(request: Request):
    """Redirect user to GitHub OAuth authorization page."""
    base_url = str(request.base_url).rstrip("/")
    return await get_github_auth_url(base_url, settings.github_client_id, redirect_uri)


@router.get("/github/callback")
async def github_callback(request: Request, code: str, error: Optional[str] = None):
    """Handle GitHub OAuth callback and exchange code for access token."""
    if error:
        return JSONResponse(status_code=400,
                            content={"error": error})

    if not code:
        return JSONResponse(status_code=400,
                            content={"error": "Missing 'code' parameter"})

    # -- Exchange the authorization code for GitHub access token --
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": settings.github_client_id,
        "client_secret": settings.github_client_secret,
        "code": code,
        "redirect_uri": settings.redirect_uri,
    }

    with httpx.Client() as client:
        response = client.post(token_url, data=data, headers=headers)
        response.raise_for_status()
        token_json = response.json()
        # print(token_json)

    github_access_token = token_json.get("access_token")
    github_refresh_token = token_json.get("refresh_token", None)
    if not github_access_token:
        return JSONResponse(status_code=400,
                            content={"error": "Failed to obtain GitHub token"})

    # -- Use the GitHub token to fetch user info --
    user_api = "https://api.github.com/user"
    auth_header = {"Authorization": f"Bearer {github_access_token}"}
    with httpx.Client() as client:
        user_resp = client.get(user_api, headers=auth_header)
        user_resp.raise_for_status()
        user_info = user_resp.json()

    # For demonstration, let's assume user_info has an 'id' (GitHub numeric ID)
    github_user_id = user_info["id"]

    # ----------------------------------------------------------------
    # Store GitHub access token in Redis, keyed by GitHub user ID
    # (In a real app, you'd probably store a full user record, or
    #  match to an internal user ID, etc.)
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    # Generate YOUR OWN JWT token for the user to authenticate with
    # your application. This token is separate from the GitHub token.
    # ----------------------------------------------------------------
    now = int(time.time())
    payload = {
        "sub": str(github_user_id),        # subject = your user identifier
        "iat": now,
        "exp": now + 3600,                 # token valid for 1 hour
        "provider": "github",
    }

    my_app_jwt = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    r.hset(f'user:{github_user_id}', mapping={
        "github_access_token": github_access_token,
        "github_refresh_token": github_refresh_token if github_refresh_token else "",
        "user_jwt": my_app_jwt
    })

    # Optionally store the user’s JWT or user data in Redis (session approach)

    # ----------------------------------------------------------------
    # Return the JWT to the frontend.
    # You could either:
    #   - Redirect to frontend with the token in a query param, or
    #   - Return JSON with the token, or
    #   - Set an HTTP-only cookie (better for many cases).
    #
    # Here, we'll do a simple redirect with the token as a query param.
    # ----------------------------------------------------------------

    # For packaged frontend, use the following URL
    # frontend_redirect_url = f"/ui/callback?access_token={my_app_jwt}"
    # For standalone frontend, use the following URL
    frontend_redirect_url = f"http://localhost:5173/ui/callback?access_token={my_app_jwt}"
    logging.info(f"User logged in with access token, redirect to callback URL")
    return RedirectResponse(url=frontend_redirect_url)
     

@router.get("/user")
async def get_user(access_token: str = None):
    """Return the current logged-in user's information."""

    if not access_token:
        raise HTTPException(status_code=401, detail="User not logged in")
    # Fetch user info
    payload = verify_jwt(access_token)
    iat = datetime.fromtimestamp(payload["iat"]).strftime('%Y%m%d-%H:%M:%S')
    exp = datetime.fromtimestamp(payload["exp"]).strftime('%Y%m%d-%H:%M:%S')
    token_id = f'user:{payload["sub"]}'
    token_info = {k.decode(): v.decode() for k, v in r.hgetall(token_id).items()}
    github_access_token = token_info['github_access_token']
    if not token_info:
        raise HTTPException(status_code=401, detail="User not logged in")
    user_data = await github_user_info(github_access_token)
   
    result = {
        "user": {
            "name": user_data['login'],
            "email": user_data["email"] if user_data.get("email") else "Non-Email User",
            "avatar": user_data["avatar_url"],
        },
        "user_id": payload['sub'],
        "iat": iat,
        "exp": exp,
        "provider": payload["provider"],
    }
    return JSONResponse(content=result)

