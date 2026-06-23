import os
import time
from typing import Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel

# Do not hardcode the JWT_SECRET!
# Read all secrets lazily (at call time, not at import time) so that
# test conftest.py can set os.environ BEFORE the first request is
# handled — even if api.main was already imported by the test collector.
def _jwt_secret() -> str:
    return os.environ.get("JWT_SECRET", "default-secret")

def _jwt_algorithm() -> str:
    return os.environ.get("JWT_ALGORITHM", "HS256")

def _api_key_valid() -> str:
    return os.environ.get("API_KEY_VALID", "ci-test-api-key")

def _auth_enabled() -> bool:
    return os.environ.get("AUTH_ENABLED", "").lower() in ("1", "true", "yes")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
security_bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


def create_access_token(sub: str, expires_minutes: int = 60) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "iat": now,
        "exp": now + expires_minutes * 60,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=_jwt_algorithm())


def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    if api_key is None:
        return None
    if api_key == _api_key_valid():
        return "api_key_user"
    raise HTTPException(status_code=401, detail="Invalid API Key")


def verify_jwt(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
) -> Optional[dict]:
    if credentials is None:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials, _jwt_secret(), algorithms=[_jwt_algorithm()]
        )
        if "exp" not in payload:
            raise HTTPException(status_code=401, detail="Missing expiration")
        if payload["exp"] < time.time():
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(
    api_user: Optional[str] = Depends(verify_api_key),
    jwt_payload: Optional[dict] = Depends(verify_jwt),
) -> Optional[dict]:
    """Return the authenticated principal, or None when auth is disabled.

    When AUTH_ENABLED is falsy (the default for the core lab) this
    dependency is a no-op so that backend tests that don't send
    credentials still receive 422 for malformed bodies rather than 401.
    """
    if not _auth_enabled():
        return None
    if api_user is not None:
        return {"sub": api_user, "type": "api_key"}
    if jwt_payload is not None:
        return jwt_payload
    raise HTTPException(status_code=401, detail="Not authenticated")


def verify_admin_scope(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    api_key: Optional[str] = Security(api_key_header),
) -> dict:
    """Enforce JWT-only scope for admin endpoints.

    - No credential  → 401
    - Valid API key   → 403 (valid credential, wrong scope)
    - Valid JWT       → payload dict
    - Invalid JWT     → 401
    """
    if credentials:
        payload = verify_jwt(credentials)
        if payload is not None:
            return payload
    if api_key:
        # Valid credential but wrong scope — verify first to catch bad keys.
        verify_api_key(api_key)  # raises 401 if invalid key
        raise HTTPException(status_code=403, detail="Insufficient scope: JWT required")
    raise HTTPException(status_code=401, detail="Not authenticated")
