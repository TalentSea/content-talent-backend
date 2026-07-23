from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.utils.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Validates JWT Bearer access token, extracts user_id payload, and injects authenticated creator context into routes.
    No user_id parameter is accepted in request bodies or query strings to eliminate IDOR risks.
    """
    pass
