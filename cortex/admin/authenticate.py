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



def verify_bearer_token(request: Request):
    from cortex.admin.authenticate import verify_jwt
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            return verify_jwt(token)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
    else:
        raise HTTPException(status_code=401, detail="Invalid or missing token")