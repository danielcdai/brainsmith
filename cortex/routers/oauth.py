'''
Universal OAuth2.0 Authentication Router.
Currently supports Google, Microsoft, and GitHub OAuth2.0 providers.
Google, Microsoft OAuth2.0 providers are commented out as of now.
'''
from fastapi import APIRouter, Request, Response
from cortex.admin.oauth import oauth_manager


router = APIRouter(prefix="/oauth",  tags=["OAuth Authentication"])


@router.get("/{provider}/login")
async def oauth_login(provider: str, request: Request):
    return await oauth_manager.handle_login(provider, request)


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, request: Request, response: Response):
    return await oauth_manager.handle_callback(provider, request, response)

