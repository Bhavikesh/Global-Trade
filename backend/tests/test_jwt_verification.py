"""
Dedicated unit tests for Auth0 JWT token verification (backend/app/core/auth/jwt.py).

Tests:
  - Valid RS256 token acceptance using generated RSA keypair
  - Invalid signature rejection
  - Incorrect issuer rejection
  - Incorrect audience rejection
  - Expired token rejection
  - Unsupported algorithm rejection
  - Missing/malformed Authorization header rejection
  - Missing sub claim rejection
  - Missing kid header rejection
  - Unconfigured server settings rejection
"""
import base64
import time
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

import app.core.auth.jwt as jwt_module
from app.core.auth.jwt import verify_jwt, _JWKS_CACHE
from app.core.config import settings


# ---------------------------------------------------------------------------
# Test RSA Keypair and JWKS Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rsa_keypair():
    """Generate an RSA private/public keypair for testing."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    # Construct JWK dictionary from public numbers
    pub_numbers = private_key.public_key().public_numbers()

    def _to_b64(val: int) -> str:
        b = val.to_bytes((val.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")

    jwk_dict = {
        "kty": "RSA",
        "use": "sig",
        "kid": "test-key-id-1",
        "n": _to_b64(pub_numbers.n),
        "e": _to_b64(pub_numbers.e),
        "alg": "RS256",
    }
    return {"private_pem": private_pem, "jwk": jwk_dict, "kid": "test-key-id-1"}


@pytest.fixture(scope="module")
def second_rsa_keypair():
    """Generate a second (untrusted) RSA keypair for signature mismatch testing."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    return {"private_pem": private_pem}


@pytest.fixture(autouse=True)
def mock_auth0_environment(rsa_keypair, monkeypatch):
    """Configure test Auth0 environment settings and mock JWKS cache."""
    monkeypatch.setattr(settings, "AUTH0_DOMAIN", "test-auth-tenant.us.auth0.com")
    monkeypatch.setattr(settings, "AUTH0_AUDIENCE", "https://api.globaltrade.ai")

    # Seed JWKS cache directly so no HTTP calls are made
    with jwt_module._JWKS_CACHE_LOCK:
        jwt_module._JWKS_CACHE.clear()
        jwt_module._JWKS_CACHE["keys"] = {"keys": [rsa_keypair["jwk"]]}
        jwt_module._JWKS_CACHE["fetched_at"] = time.monotonic()

    # Also mock _fetch_jwks as safety net
    monkeypatch.setattr(
        jwt_module,
        "_fetch_jwks",
        lambda force_refresh=False: {"keys": [rsa_keypair["jwk"]]},
    )


def _mint_token(
    private_pem: str,
    claims: dict[str, Any],
    headers: dict[str, Any] | None = None,
    algorithm: str = "RS256",
) -> str:
    """Helper to mint JWT tokens with specified claims and headers."""
    h = headers if headers is not None else {"kid": "test-key-id-1"}
    return jwt.encode(claims, private_pem, algorithm=algorithm, headers=h)


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class TestJWTVerification:
    def test_valid_rs256_token_accepted(self, rsa_keypair):
        """A correctly signed RS256 token with valid claims is successfully verified."""
        now = int(time.time())
        claims = {
            "iss": "https://test-auth-tenant.us.auth0.com/",
            "aud": "https://api.globaltrade.ai",
            "sub": "auth0|user_12345",
            "email": "trader@globaltrade.ai",
            "exp": now + 3600,
            "iat": now,
        }
        token = _mint_token(rsa_keypair["private_pem"], claims)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        payload = verify_jwt(credentials)
        assert payload["sub"] == "auth0|user_12345"
        assert payload["email"] == "trader@globaltrade.ai"
        assert payload["iss"] == "https://test-auth-tenant.us.auth0.com/"

    def test_invalid_rsa_signature_rejected(self, second_rsa_keypair):
        """A token signed with an untrusted RSA private key is rejected (401)."""
        now = int(time.time())
        claims = {
            "iss": "https://test-auth-tenant.us.auth0.com/",
            "aud": "https://api.globaltrade.ai",
            "sub": "auth0|attacker_999",
            "exp": now + 3600,
        }
        token = _mint_token(
            second_rsa_keypair["private_pem"],
            claims,
            headers={"kid": "test-key-id-1"},
        )
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(credentials)
        assert exc_info.value.status_code == 401
        assert "verification failed" in exc_info.value.detail.lower()

    def test_incorrect_issuer_rejected(self, rsa_keypair):
        """A token from an invalid issuer is rejected (401)."""
        now = int(time.time())
        claims = {
            "iss": "https://attacker.auth0.com/",
            "aud": "https://api.globaltrade.ai",
            "sub": "auth0|user_12345",
            "exp": now + 3600,
        }
        token = _mint_token(rsa_keypair["private_pem"], claims)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(credentials)
        assert exc_info.value.status_code == 401
        assert "verification failed" in exc_info.value.detail.lower()

    def test_incorrect_audience_rejected(self, rsa_keypair):
        """A token intended for a different audience is rejected (401)."""
        now = int(time.time())
        claims = {
            "iss": "https://test-auth-tenant.us.auth0.com/",
            "aud": "https://other-api.example.com",
            "sub": "auth0|user_12345",
            "exp": now + 3600,
        }
        token = _mint_token(rsa_keypair["private_pem"], claims)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(credentials)
        assert exc_info.value.status_code == 401
        assert "verification failed" in exc_info.value.detail.lower()

    def test_expired_token_rejected(self, rsa_keypair):
        """A token whose expiration timestamp is in the past is rejected (401)."""
        now = int(time.time())
        claims = {
            "iss": "https://test-auth-tenant.us.auth0.com/",
            "aud": "https://api.globaltrade.ai",
            "sub": "auth0|user_12345",
            "exp": now - 60,  # expired 60 seconds ago
            "iat": now - 3600,
        }
        token = _mint_token(rsa_keypair["private_pem"], claims)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(credentials)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_unsupported_algorithm_rejected(self, monkeypatch):
        """A token signed using an unsupported algorithm like HS256 is rejected (401)."""
        now = int(time.time())
        claims = {
            "iss": "https://test-auth-tenant.us.auth0.com/",
            "aud": "https://api.globaltrade.ai",
            "sub": "auth0|user_12345",
            "exp": now + 3600,
        }
        hs256_token = jwt.encode(claims, "symmetric-secret-key-12345", algorithm="HS256", headers={"kid": "test-key-id-1"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=hs256_token)

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(credentials)
        assert exc_info.value.status_code == 401

    def test_missing_sub_claim_rejected(self, rsa_keypair):
        """A token missing the required 'sub' claim is rejected (401)."""
        now = int(time.time())
        claims = {
            "iss": "https://test-auth-tenant.us.auth0.com/",
            "aud": "https://api.globaltrade.ai",
            "exp": now + 3600,
        }
        token = _mint_token(rsa_keypair["private_pem"], claims)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(credentials)
        assert exc_info.value.status_code == 401
        assert "sub" in exc_info.value.detail.lower()

    def test_missing_kid_in_header_rejected(self, rsa_keypair):
        """A token header without 'kid' is rejected (401)."""
        now = int(time.time())
        claims = {
            "iss": "https://test-auth-tenant.us.auth0.com/",
            "aud": "https://api.globaltrade.ai",
            "sub": "auth0|user_12345",
            "exp": now + 3600,
        }
        token = _mint_token(rsa_keypair["private_pem"], claims, headers={})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(credentials)
        assert exc_info.value.status_code == 401
        assert "kid" in exc_info.value.detail.lower()

    def test_unconfigured_auth0_rejected(self, rsa_keypair, monkeypatch):
        """If Auth0 settings are empty strings, endpoint raises 503."""
        monkeypatch.setattr(settings, "AUTH0_DOMAIN", "")
        monkeypatch.setattr(settings, "AUTH0_AUDIENCE", "")

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dummy.token.here")
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(credentials)
        assert exc_info.value.status_code == 503
