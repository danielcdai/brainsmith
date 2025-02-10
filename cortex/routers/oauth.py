'''
Universal OAuth2.0 Authentication Router.
Currently supports Google, Microsoft, and GitHub OAuth2.0 providers.
Google, Microsoft OAuth2.0 providers are commented out as of now.
'''
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import RedirectResponse
from cortex.storage.session import get_db, User
from cortex.admin.oauth import oauth_manager
from cortex.config import settings
from cortex.admin.security import create_access_token
from datetime import datetime, timezone
import requests


router = APIRouter(prefix="/oauth",  tags=["OAuth Authentication"])
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API_URL = "https://api.github.com/user"


@router.get("/{provider}/login")
async def oauth_login(provider: str, request: Request):
    return await oauth_manager.handle_login(provider, request)


@router.get("/{provider}/callback")
def github_callback(code: str, response: Response, db=Depends(get_db)):
    # Disable the oauth_manager universal call back for now
    """
    Handle the GitHub OAuth callback: exchange the code for an access token,
    fetch user info, register/login the user, and issue a JWT.
    """
    # Exchange code for access token
    headers = {"Accept": "application/json"}
    data = {
        "client_id": settings.github_client_id,
        "client_secret": settings.github_client_secret,
        "code": code,
        "redirect_uri": settings.redirect_uri,
    }
    token_resp = requests.post(GITHUB_ACCESS_TOKEN_URL, headers=headers, data=data)
    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="GitHub token exchange failed")
    token_json = token_resp.json()
    github_access_token = token_json.get("access_token")
    if not github_access_token:
        raise HTTPException(status_code=400, detail="Failed to obtain access token from GitHub")

    # Fetch user info from GitHub
    headers = {"Authorization": f"token {github_access_token}"}
    user_resp = requests.get(GITHUB_USER_API_URL, headers=headers)
    if user_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from GitHub")
    github_user = user_resp.json()
    email = github_user.get("email")
    name = github_user.get("name") or github_user.get("login")
    profile_image_url = github_user.get("avatar_url")
    oauth_sub = str(github_user.get("id"))

    # In some cases, the user's email may not be public.
    # Optionally fetch the list of emails and choose the primary email.
    if not email:
        emails_resp = requests.get(GITHUB_USER_API_URL + "/emails", headers=headers)
        if emails_resp.status_code == 200:
            emails = emails_resp.json()
            primary_emails = [e for e in emails if e.get("primary")]
            if primary_emails:
                email = primary_emails[0].get("email")
            elif emails:
                email = emails[0].get("email")
    if not email:
        raise HTTPException(status_code=400, detail="GitHub email not found")

    # See if the user already exists; if not, create a new record (without a password)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name=name,
            email=email,
            hashed_password=None,  # No local password because this is an OAuth user.
            profile_image_url=profile_image_url,
            oauth_sub=oauth_sub,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update any changed details from GitHub
        user.name = name
        user.profile_image_url = profile_image_url
        user.oauth_sub = oauth_sub
        user.updated_at = datetime.utcnow()
        db.commit()

    # Issue JWT token and set it as a secure, HTTP‑only cookie.
    jwt_token = create_access_token(data={"sub": user.id})
    response.set_cookie(key="token", value=jwt_token, httponly=True)

    frontend_redirect_url = f"http://localhost:5173/ui/callback?access_token={jwt_token}"
    # Optionally, redirect to a frontend URL.
    return RedirectResponse(url=frontend_redirect_url)
