import time
import httpx
import redis
from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse, JSONResponse
from jose import jwt, JWTError
from typing import Optional
from cortex.config import settings


router = APIRouter(prefix="/auth")


r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=1)


@router.get("/github/login")
def github_login():
    github_auth_url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.redirect_uri}"
        "&scope=user:email"
    )
    return RedirectResponse(url=github_auth_url)



@router.get("/github/callback")
def github_callback(code: Optional[str] = None, error: Optional[str] = None):
    if error:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": error})

    if not code:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
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

    github_access_token = token_json.get("access_token")
    if not github_access_token:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
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
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
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
    frontend_redirect_url = f"{settings.frontend_url}/login-success?access_token={my_app_jwt}"
    return RedirectResponse(url=frontend_redirect_url)


def verify_jwt(token: str) -> dict:
    """
    A simple dependency to verify your app's JWT.
    In practice, you'll probably want a more robust approach,
    plus handle token revocation, expiration, etc.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload  # e.g. { "sub": "...", "exp": "...", ... }
    except JWTError:
        raise ValueError("Invalid or expired JWT")


# @router.get("/protected-resource")
# def protected_endpoint(token: str) -> dict:
#     """
#     Example usage:
#     The frontend must send the token in query param or in header, etc.
#     e.g. GET /protected-resource?token=<my_app_jwt>

#     In real-world usage, you'd do something like:
#       def protected_endpoint(payload: dict = Depends(verify_jwt)):
#           return ...
#     """
#     try:
#         payload = verify_jwt(token)
#         return {"message": "You are authorized!", "payload": payload}
#     except ValueError as e:
#         return JSONResponse(status_code=401, content={"detail": str(e)})