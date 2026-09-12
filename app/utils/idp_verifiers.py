import logging
from typing import Any

import requests
from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.config import get_settings

logger = logging.getLogger("uvicorn.error")


def verify_google_id_token(id_token_str: str) -> dict[str, Any]:
    """
    Verifies a Google OIDC id_token using official Google RSA public keys.
    Raises HTTPException(401) if token is invalid or expired.
    """
    if not id_token_str or not id_token_str.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google id_token must be provided",
        )

    # Mock testing token for local offline development
    if id_token_str.startswith("mock_google_"):
        mock_id = id_token_str.replace("mock_google_", "")
        return {
            "sub": f"google_user_{mock_id}",
            "email": f"google.user{mock_id}@gmail.com",
            "name": f"Google User {mock_id}",
            "picture": "https://lh3.googleusercontent.com/a/default_avatar",
        }

    settings = get_settings()
    client_id = settings.GOOGLE_CLIENT_ID or None

    try:
        id_info = google_id_token.verify_oauth2_token(
            id_token_str, google_requests.Request(), audience=client_id
        )
        return {
            "sub": str(id_info.get("sub")),
            "email": id_info.get("email"),
            "name": id_info.get("name"),
            "picture": id_info.get("picture"),
        }
    except ValueError as err:
        logger.warning("Google OIDC verification error: %s", err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired Google OIDC identity token: {err!s}",
        ) from err
    except Exception as err:
        logger.error("Unexpected Google auth verification failure: %s", err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to verify Google identity token with authentication provider",
        ) from err


def verify_facebook_access_token(access_token_str: str) -> dict[str, Any]:
    """
    Verifies a Facebook OAuth 2.0 access_token via Facebook Graph API /me.
    Raises HTTPException(401) if token is invalid or expired.
    """
    if not access_token_str or not access_token_str.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Facebook access_token must be provided",
        )

    # Mock testing token for local offline development
    if access_token_str.startswith("mock_facebook_"):
        mock_id = access_token_str.replace("mock_facebook_", "")
        return {
            "sub": f"facebook_user_{mock_id}",
            "email": f"facebook.user{mock_id}@example.com",
            "name": f"Facebook User {mock_id}",
            "picture": "https://platform-lookaside.fbsbx.com/platform/profilepic/default",
        }

    try:
        url = "https://graph.facebook.com/v20.0/me"
        params = {
            "fields": "id,name,email,picture.type(large)",
            "access_token": access_token_str,
        }
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200:
            raise ValueError(
                f"Facebook Graph API responded with status {res.status_code}: {res.text}"
            )

        data = res.json()
        fb_id = data.get("id")
        if not fb_id:
            raise ValueError("Facebook response payload missing user id")

        picture_url = None
        picture_obj = data.get("picture")
        if isinstance(picture_obj, dict):
            pic_data = picture_obj.get("data")
            if isinstance(pic_data, dict):
                picture_url = pic_data.get("url")

        return {
            "sub": str(fb_id),
            "email": data.get("email"),
            "name": data.get("name"),
            "picture": picture_url,
        }
    except ValueError as err:
        logger.warning("Facebook Graph API token validation error: %s", err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired Facebook access token: {err!s}",
        ) from err
    except Exception as err:
        logger.error("Unexpected Facebook verification failure: %s", err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to verify Facebook access token with authentication provider",
        ) from err
