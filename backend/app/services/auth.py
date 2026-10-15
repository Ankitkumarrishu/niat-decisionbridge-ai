from __future__ import annotations

import logging
from typing import Optional

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


class AuthUser:
    def __init__(self, user_id: str, email: str):
        self.user_id = user_id
        self.email = email


def _user_from_payload(payload: dict) -> AuthUser:
    email = (payload.get("email") or "").lower()
    user_id = payload.get("sub") or payload.get("user_id") or ""
    if not email or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")
    return AuthUser(user_id=str(user_id), email=email)


def _decode_hs256(token: str, secret: str) -> AuthUser:
    payload = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        audience="authenticated",
    )
    return _user_from_payload(payload)


def _verify_with_supabase_auth(token: str, settings: Settings) -> AuthUser:
    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured. Set SUPABASE_JWT_SECRET or SUPABASE_URL.",
        )
    api_key = settings.supabase_anon_key or settings.supabase_service_role_key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured. Set SUPABASE_JWT_SECRET or a Supabase API key.",
        )
    url = settings.supabase_url.rstrip("/") + "/auth/v1/user"
    try:
        response = httpx.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": api_key,
            },
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        logger.warning("Supabase Auth user lookup failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify counsellor session with Supabase Auth",
        ) from exc

    if response.status_code in {401, 403}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if response.status_code >= 400:
        logger.warning("Supabase Auth returned status %s", response.status_code)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    body = response.json()
    email = (body.get("email") or "").lower()
    user_id = body.get("id") or ""
    if not email or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")
    return AuthUser(user_id=str(user_id), email=email)


def verify_supabase_jwt(token: str, settings: Settings) -> AuthUser:
    if settings.supabase_jwt_secret:
        try:
            return _decode_hs256(token, settings.supabase_jwt_secret)
        except jwt.PyJWTError:
            if settings.supabase_configured():
                logger.info("HS256 JWT decode failed; trying Supabase Auth user endpoint")
                return _verify_with_supabase_auth(token, settings)
            logger.warning("JWT verification failed")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None

    if settings.supabase_configured():
        return _verify_with_supabase_auth(token, settings)

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authentication is not configured (SUPABASE_JWT_SECRET missing)",
    )


def require_counsellor(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings),
) -> AuthUser:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required")
    if not settings.counsellor_email_set:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Counsellor allowlist is empty. Set COUNSELLOR_EMAILS.",
        )
    user = verify_supabase_jwt(credentials.credentials, settings)
    if user.email not in settings.counsellor_email_set:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Counsellor access denied")
    return user
