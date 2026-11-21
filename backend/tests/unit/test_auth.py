import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from forgetme.api.auth import Auth0TokenVerifier, AuthError, Principal, require_permission

DOMAIN = "tenant.eu.auth0.com"
AUDIENCE = "https://api.forgetme.test"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def token(key=KEY, **overrides) -> str:
    claims = {
        "iss": f"https://{DOMAIN}/",
        "aud": AUDIENCE,
        "sub": "auth0|123",
        "exp": int(time.time()) + 300,
        "permissions": ["forget:read"],
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256")


@pytest.fixture
def verifier() -> Auth0TokenVerifier:
    return Auth0TokenVerifier(DOMAIN, AUDIENCE, signing_key_provider=lambda _: KEY.public_key())


def test_valid_token_yields_principal_with_permissions(verifier):
    principal = verifier.verify(token())
    assert principal == Principal("auth0|123", frozenset({"forget:read"}))


def test_token_without_permissions_claim_has_none(verifier):
    claims = {
        "iss": f"https://{DOMAIN}/",
        "aud": AUDIENCE,
        "sub": "x",
        "exp": int(time.time()) + 60,
    }
    assert verifier.verify(jwt.encode(claims, KEY, algorithm="RS256")).permissions == frozenset()


@pytest.mark.parametrize(
    "bad",
    [
        token(exp=int(time.time()) - 10),
        token(aud="https://other-api"),
        token(iss="https://evil.example/"),
        token(key=OTHER_KEY),
        "not-a-token",
    ],
    ids=["expired", "wrong-audience", "wrong-issuer", "wrong-signature", "garbage"],
)
def test_invalid_tokens_are_rejected(verifier, bad):
    with pytest.raises(AuthError):
        verifier.verify(bad)


def test_hs256_tokens_are_rejected(verifier):
    forged = jwt.encode(
        {"iss": f"https://{DOMAIN}/", "aud": AUDIENCE, "sub": "x", "exp": int(time.time()) + 60},
        "secret-secret-secret-secret-secret-123",
        algorithm="HS256",
    )
    with pytest.raises(AuthError):
        verifier.verify(forged)


def protected_client(verifier) -> TestClient:
    app = FastAPI()
    app.state.verifier = verifier

    @app.get("/secret")
    def secret(principal: Principal = Depends(require_permission("forget:read"))):
        return {"sub": principal.subject}

    return TestClient(app)


def test_dependency_returns_401_without_token(verifier):
    response = protected_client(verifier).get("/secret")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_dependency_returns_401_for_bad_token(verifier):
    response = protected_client(verifier).get("/secret", headers={"Authorization": "Bearer nope"})
    assert response.status_code == 401


def test_dependency_returns_403_without_permission(verifier):
    bearer = {"Authorization": f"Bearer {token(permissions=[])}"}
    assert protected_client(verifier).get("/secret", headers=bearer).status_code == 403


def test_dependency_allows_token_with_permission(verifier):
    bearer = {"Authorization": f"Bearer {token()}"}
    response = protected_client(verifier).get("/secret", headers=bearer)
    assert response.json() == {"sub": "auth0|123"}
