import base64
import logging
import mimetypes
import uuid

import aiohttp
from authlib.integrations.starlette_client import OAuth
from authlib.oidc.core import UserInfo
from fastapi import HTTPException
from starlette.responses import RedirectResponse
from cortex.config import settings, OAUTH_PROVIDERS
from cortex.constants import ERROR_MESSAGES
import re
import uuid
import jwt

from datetime import UTC, datetime, timedelta
from typing import Optional, Union
from cortex.models.users import Users






log = logging.getLogger(__name__)


def parse_duration(duration: str) -> Optional[timedelta]:
    if duration == "-1" or duration == "0":
        return None

    # Regular expression to find number and unit pairs
    pattern = r"(-?\d+(\.\d+)?)(ms|s|m|h|d|w)"
    matches = re.findall(pattern, duration)

    if not matches:
        raise ValueError("Invalid duration string")

    total_duration = timedelta()

    for number, _, unit in matches:
        number = float(number)
        if unit == "ms":
            total_duration += timedelta(milliseconds=number)
        elif unit == "s":
            total_duration += timedelta(seconds=number)
        elif unit == "m":
            total_duration += timedelta(minutes=number)
        elif unit == "h":
            total_duration += timedelta(hours=number)
        elif unit == "d":
            total_duration += timedelta(days=number)
        elif unit == "w":
            total_duration += timedelta(weeks=number)

    return total_duration


def create_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    payload = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
        payload.update({"exp": expire})

    encoded_jwt = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


class OAuthManager:
    def __init__(self):
        self.oauth = OAuth()
        for _, provider_config in OAUTH_PROVIDERS.items():
            provider_config["register"](self.oauth)

    def get_client(self, provider_name):
        return self.oauth.create_client(provider_name)
    
    # Here removed 2 functions about the user role and user groups

    async def handle_login(self, provider, request):
        if provider not in OAUTH_PROVIDERS:
            raise HTTPException(404)
        # If the provider has a custom redirect URL, use that, otherwise automatically generate one
        redirect_uri = OAUTH_PROVIDERS[provider].get("redirect_uri") or request.url_for(
            "oauth_callback", provider=provider
        )
        client = self.get_client(provider)
        if client is None:
            raise HTTPException(404)
        return await client.authorize_redirect(request, redirect_uri)


    async def handle_callback(self, provider, request, response):
        if provider not in OAUTH_PROVIDERS:
            raise HTTPException(404)
        client = self.get_client(provider)
        try:
            token = await client.authorize_access_token(request)
        except Exception as e:
            log.warning(f"OAuth callback error: {e}")
            raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)
        user_data: UserInfo = token.get("userinfo")
        if not user_data:
            user_data: UserInfo = await client.userinfo(token=token)
        if not user_data:
            log.warning(f"OAuth callback failed, user data is missing: {token}")
            raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)
        provider_sub = f"{provider}@{sub}"
        sub = user_data.get(OAUTH_PROVIDERS[provider].get("sub_claim", "sub"))
        if not sub:
            log.warning(f"OAuth callback failed, sub is missing: {user_data}")
            raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)

        email = user_data.get("email", "Non-Email User").lower()
        if not email:
            log.warning(f"OAuth callback failed, email is missing: {user_data}")
            raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)

        user = Users.get_user_by_oauth_sub(provider_sub)

        if not user:
            # Check if the user exists by email
            user = Users.get_user_by_email(email)
            if user:
                # Update the user with the new oauth sub
                Users.update_user_oauth_sub_by_id(user.id, provider_sub)
            else:
                picture_url = user_data.get(
                    "picture", 
                    # For Microsoft, the picture URL is different
                    OAUTH_PROVIDERS[provider].get("picture_url", "")
                )
                if picture_url:
                    # Download the profile image into a base64 string
                    try:
                        access_token = token.get("access_token")
                        get_kwargs = {}
                        if access_token:
                            get_kwargs["headers"] = {
                                "Authorization": f"Bearer {access_token}",
                            }
                        async with aiohttp.ClientSession() as session:
                            async with session.get(picture_url, **get_kwargs) as resp:
                                picture = await resp.read()
                                base64_encoded_picture = base64.b64encode(
                                    picture
                                ).decode("utf-8")
                                guessed_mime_type = mimetypes.guess_type(picture_url)[0]
                                if guessed_mime_type is None:
                                    # assume JPG, browsers are tolerant enough of image formats
                                    guessed_mime_type = "image/jpeg"
                                picture_url = f"data:{guessed_mime_type};base64,{base64_encoded_picture}"
                    except Exception as e:
                        log.error(
                            f"Error downloading profile image '{picture_url}': {e}"
                        )
                        picture_url = ""
                if not picture_url:
                    picture_url = "/user.png"

        jwt_token = create_token(
            data={"id": str(uuid.uuid4())},
            expires_delta=parse_duration(settings.jwt_expires_in),
        )

        # Hide the logic for creating customized JWT token
        # # Set the cookie token
        # response.set_cookie(
        #     key="token",
        #     value=jwt_token,
        #     httponly=True,  # Ensures the cookie is not accessible via JavaScript
        #     samesite="lax",
        #     secure=False,
        # )

        oauth_id_token = token.get("id_token")
        response.set_cookie(
            key="oauth_id_token",
            value=oauth_id_token,
            httponly=True,
            samesite="lax",
            secure=False,
        )
        # Redirect back to the frontend with the JWT token
        redirect_url = f"{request.base_url}auth#token={jwt_token}"
        print(f"OAuth callback success, redirecting to: {redirect_url}")
        return RedirectResponse(url=redirect_url, headers=response.headers)


oauth_manager = OAuthManager()
