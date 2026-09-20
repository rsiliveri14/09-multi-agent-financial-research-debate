from __future__ import annotations

from fastapi import Depends, Header

from config.settings import Settings, get_settings
from domain.errors import AuthenticationError, AuthorizationError


def parse_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def current_role(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> str:
    token = parse_bearer(authorization)
    if not token:
        raise AuthenticationError()
    role = settings.token_role_map.get(token)
    if not role:
        raise AuthenticationError("Invalid token")
    return role


def require_roles(*allowed: str):
    allowed_set = set(allowed)

    def dependency(role: str = Depends(current_role)) -> str:
        if role == "admin" or role in allowed_set:
            return role
        raise AuthorizationError()

    return dependency
