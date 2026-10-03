"""
Auth0 JWT verification.

The backend verifies the JWT issued by Auth0 on every protected request.
We do NOT issue our own tokens, manage sessions, or hash passwords (DEC-038).

The verified token payload provides the caller's identity_provider_id (sub claim)
which is then used to look up or create the application-level User record.

Verification steps:
  1. Extract the Bearer token from the Authorization header.
  2. Fetch Auth0 JWKS (cached) to retrieve the signing public key.
  3. Verify the token signature, expiry, issuer, and audience.
  4. Return the decoded claims.

Required environment variables:
  AUTH0_DOMAIN   — e.g. your-tenant.auth0.com
  AUTH0_AUDIENCE — the API identifier registered in Auth0
"""
import threading
import time
from typing import Any

import httpx
from jose import JWTError, jwt
from jose.backends.rsa_backend import RSAKey
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

# ---------------------------------------------------------------------------
# JWKS cache — thread-safe in-memory cache with TTL
# ---------------------------------------------------------------------------
_JWKS_CACHE: dict[str, Any] = {}
_JWKS_CACHE_LOCK = threading.Lock()
_JWKS_TTL_SECONDS = 3600  # 1 hour


def _fetch_jwks(force_refresh: bool = False) -> dict[str, Any]:
    """Fetch JWKS from Auth0 with thread-safe in-memory TTL caching."""
    with _JWKS_CACHE_LOCK:
        now = time.monotonic()
        if (
            not force_refresh
            and _JWKS_CACHE.get("fetched_at")
            and (now - _JWKS_CACHE["fetched_at"] < _JWKS_TTL_SECONDS)
        ):
            return _JWKS_CACHE["keys"]

    url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable. Could not fetch signing keys.",
        ) from exc

    keys = response.json()
    with _JWKS_CACHE_LOCK:
        _JWKS_CACHE["keys"] = keys
        _JWKS_CACHE["fetched_at"] = time.monotonic()
    return keys


def _get_signing_key(token: str) -> RSAKey:
    """
    Determine the correct RSA public key for this token from Auth0 JWKS.
    Matches by the 'kid' (key ID) header in the JWT.
    """
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header.",
        ) from exc

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token header missing 'kid' claim.",
        )

    jwks = _fetch_jwks()

    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == kid:
            return RSAKey(key_data, algorithm="RS256")

    # Kid not found — the JWKS may have rotated; force refresh and retry once.
    jwks = _fetch_jwks(force_refresh=True)
    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == kid:
            return RSAKey(key_data, algorithm="RS256")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to find appropriate signing key.",
    )


# ---------------------------------------------------------------------------
# FastAPI security scheme
# ---------------------------------------------------------------------------
_bearer_scheme = HTTPBearer(auto_error=True)


def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict[str, Any]:
    """
    FastAPI dependency.  Verifies the Auth0 Bearer JWT and returns the decoded claims.

    Usage:
        @router.get("/protected")
        def protected_route(claims: dict = Depends(verify_jwt)):
            user_sub = claims["sub"]
    """
    if not settings.AUTH0_DOMAIN or not settings.AUTH0_AUDIENCE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured on this server.",
        )

    token = credentials.credentials
    signing_key = _get_signing_key(token)

    try:
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.AUTH0_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/",
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed.",
        ) from exc

    if not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required 'sub' claim.",
        )

    return payload

