import httpx


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
        # raise HTTPException(status_code=400, detail="Failed to get access token")
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