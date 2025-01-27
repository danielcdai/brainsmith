import logging
from typing import Optional
from fastapi import  HTTPException,  APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
import time
from jose import jwt, JWTError
import redis
import httpx

from cortex.config import settings
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
    print(await get_github_auth_url(base_url, settings.github_client_id, redirect_uri))
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
    r.set(f"github_token:{github_user_id}", github_access_token)

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

    # Optionally store the user’s JWT or user data in Redis (session approach)
    r.set(f"user_jwt:{github_user_id}", my_app_jwt)

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
    user_data = await github_user_info(access_token)
    return JSONResponse(content={"user": user_data})


# TODO: Do the verification for all the requests towards the protected endpoints
@router.get("/verify")
async def verify_token(token: str):
    """Verify the JWT token and return the saved user info from Redis."""
    try:
        payload = verify_jwt(token)
        github_user_id = payload.get("sub")
        if not github_user_id:
            raise HTTPException(status_code=400, detail="Invalid token payload")

        # Retrieve the GitHub access token from Redis
        github_access_token = r.get(f"github_token:{github_user_id}")
        if not github_access_token:
            raise HTTPException(status_code=404, detail="Token not found in Redis")

        # Retrieve the user info from Redis
        user_jwt = r.get(f"user_jwt:{github_user_id}")
        if not user_jwt:
            raise HTTPException(status_code=404, detail="User info not found in Redis")

        return JSONResponse(content={"user_id": github_user_id, "jwt": user_jwt.decode()})
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

