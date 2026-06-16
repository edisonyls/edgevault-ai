import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings

WorkspaceKey = Literal["owner", "demo"]

OWNER_WORKSPACE_ID = UUID("00000000-0000-4000-8000-000000000001")
DEMO_WORKSPACE_ID = UUID("00000000-0000-4000-8000-000000000002")


@dataclass(frozen=True, slots=True)
class WorkspaceContext:
    id: UUID
    key: WorkspaceKey
    display_name: str
    read_only: bool = False


WORKSPACES: dict[WorkspaceKey, WorkspaceContext] = {
    "owner": WorkspaceContext(
        id=OWNER_WORKSPACE_ID,
        key="owner",
        display_name="Personal",
    ),
    "demo": WorkspaceContext(
        id=DEMO_WORKSPACE_ID,
        key="demo",
        display_name="Demo",
    ),
}


class AuthConfigurationError(RuntimeError):
    pass


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


def _session_secret(settings: Settings) -> str:
    if settings.auth_session_secret:
        return settings.auth_session_secret
    if settings.environment == "production":
        raise AuthConfigurationError(
            "AUTH_SESSION_SECRET must be set in production.")
    return "edgevault-local-development-session-secret"


def configured_password(settings: Settings, workspace_key: WorkspaceKey) -> str:
    password = (
        settings.auth_owner_password
        if workspace_key == "owner"
        else settings.auth_demo_password
    )
    if password:
        return password
    if settings.environment == "production":
        env_name = "AUTH_OWNER_PASSWORD" if workspace_key == "owner" else "AUTH_DEMO_PASSWORD"
        raise AuthConfigurationError(f"{env_name} must be set in production.")
    return "owner-local" if workspace_key == "owner" else "demo-local"


def verify_workspace_password(
    settings: Settings,
    workspace_key: WorkspaceKey,
    candidate: str,
) -> bool:
    expected = configured_password(settings, workspace_key)
    return secrets.compare_digest(candidate, expected)


def create_session_token(
    settings: Settings,
    workspace: WorkspaceContext,
    now: int | None = None,
) -> str:
    issued_at = int(time.time() if now is None else now)
    payload = {
        "workspace": workspace.key,
        "iat": issued_at,
        "exp": issued_at + settings.auth_session_ttl_seconds,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encoded_payload = _b64encode(payload_bytes)
    signature = hmac.new(
        _session_secret(settings).encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{encoded_payload}.{_b64encode(signature)}"


def parse_session_token(settings: Settings, token: str) -> WorkspaceContext | None:
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
        expected_signature = hmac.new(
            _session_secret(settings).encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()
        provided_signature = _b64decode(encoded_signature)
        if not hmac.compare_digest(provided_signature, expected_signature):
            return None

        payload = json.loads(_b64decode(encoded_payload))
        if not isinstance(payload, dict):
            return None
        if int(payload.get("exp", 0)) < int(time.time()):
            return None

        workspace_key = payload.get("workspace")
        if workspace_key not in WORKSPACES:
            return None
        return WORKSPACES[workspace_key]
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def get_optional_workspace(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> WorkspaceContext | None:
    token = request.cookies.get(settings.auth_session_cookie_name)
    if not token:
        return None
    return parse_session_token(settings, token)


def get_current_workspace(
    workspace: Annotated[WorkspaceContext | None, Depends(get_optional_workspace)],
) -> WorkspaceContext:
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return workspace


type CurrentWorkspaceDep = Annotated[WorkspaceContext, Depends(
    get_current_workspace)]
