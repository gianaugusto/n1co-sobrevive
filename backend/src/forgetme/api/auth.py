"""Auth0 JWT verification and permission checks (Auth0 RBAC ``permissions`` claim)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

READ_PERMISSION = "forget:read"
WRITE_PERMISSION = "forget:write"


class AuthError(Exception):
    """The token is missing, malformed, expired or not meant for this API."""


@dataclass(frozen=True)
class Principal:
    subject: str
    permissions: frozenset[str]


class TokenVerifier(Protocol):
    def verify(self, token: str) -> Principal: ...


SigningKeyProvider = Callable[[str], Any]


class Auth0TokenVerifier:
    """Verifies RS256 access tokens issued by an Auth0 tenant for one API audience."""

    def __init__(
        self, domain: str, audience: str, signing_key_provider: SigningKeyProvider | None = None
    ) -> None:
        self._issuer = f"https://{domain}/"
        self._audience = audience
        if signing_key_provider is None:
            client = PyJWKClient(f"https://{domain}/.well-known/jwks.json", cache_keys=True)
            signing_key_provider = lambda token: client.get_signing_key_from_jwt(token).key  # noqa: E731
        self._signing_key_provider = signing_key_provider

    def verify(self, token: str) -> Principal:
        try:
            key = self._signing_key_provider(token)
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except jwt.PyJWTError as error:
            raise AuthError(str(error)) from error
        return Principal(claims["sub"], frozenset(claims.get("permissions", [])))


_bearer = HTTPBearer(auto_error=False)


def require_permission(permission: str) -> Callable[..., Principal]:
    """FastAPI dependency: 401 without a valid token, 403 without ``permission``.

    Declared ``def`` (not ``async``) on purpose: JWKS fetching is blocking I/O, so FastAPI
    runs it in a worker thread.
    """

    def dependency(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    ) -> Principal:
        unauthorized = HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or missing access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        if credentials is None:
            raise unauthorized
        verifier: TokenVerifier = request.app.state.verifier
        try:
            principal = verifier.verify(credentials.credentials)
        except AuthError as error:
            raise unauthorized from error
        if permission not in principal.permissions:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Missing permission '{permission}'")
        return principal

    return dependency
