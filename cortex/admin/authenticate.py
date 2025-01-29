import httpx
import warnings
from fastapi import Request, HTTPException
from cortex.config import settings
from jose import JWTError, jwt


async def get_github_auth_url(
    base_url: str,
    client_id: str,
    redirect_uri: str,
):
    return (
        f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={base_url}{redirect_uri}&scope=user"
    )


async def get_github_callback_response(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
):
    warnings.warn(
        "get_github_callback_response is deprecated and will be removed in a future version.",
        DeprecationWarning,
        stacklevel=2,
    )
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, headers=headers, data=data)
        response_data = response.json()
    if "access_token" not in response_data:
        raise ValueError("Failed to get access token")
    access_token = response_data["access_token"]
    return access_token


async def github_user_info(
    access_token: str,
):
    user_info_url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        user_response = await client.get(user_info_url, headers=headers)
        if user_response.status_code == 401:
            # Logic to refresh the bearer token
            # This is a placeholder, you need to implement the actual refresh logic
            raise HTTPException(status_code=401, detail="Token expired, please refresh the token")
        user_data = user_response.json()
    return user_data


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



async def verify_bearer_token(request: Request):
    from cortex.admin.authenticate import verify_jwt
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = verify_jwt(token)
            user_id = payload['sub']
            import redis
            r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=1)
            await verify_github_token(user_id, r)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
    else:
        raise HTTPException(status_code=401, detail="Invalid or missing token")


async def verify_github_token(user_id: str, redis_conn):
    """
    Step 3: Check the GitHub token from Redis is still valid.
    For demonstration, we do a test API call (to check if unauthorized).
    If invalid, refresh or raise an error.
    """
    tokens = redis_conn.hgetall(f"user:{user_id}")
    if not tokens:
        raise HTTPException(status_code=401, detail="User tokens not found in Redis.")

    github_access_token = tokens.get(b"github_access_token", b"").decode()
    github_refresh_token = tokens.get(b"github_refresh_token", b"").decode()

    # Test an API call
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {github_access_token}"}
        )
        # If unauthorized, try to refresh or reauthorize
        if resp.status_code == 401:
            # If we had a refresh token, we could attempt to refresh. GitHub typically doesn't do this.
            if github_refresh_token:
                # Example refresh logic (not standard for GitHub!)
                refresh_url = "https://github.com/login/oauth/access_token"
                data = {
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": github_refresh_token,
                }
                r = await client.post(refresh_url, data=data, headers={"Accept": "application/json"})
                refreshed_data = r.json()
                
                if "access_token" in refreshed_data:
                    # Store new token
                    redis_conn.hset(f"user:{user_id}", "github_access_token", refreshed_data["access_token"])
                else:
                    raise HTTPException(status_code=401, detail="Unable to refresh GitHub token.")
            else:
                # Force user to re-login
                raise HTTPException(status_code=401, detail="GitHub token invalid, re-login required.")