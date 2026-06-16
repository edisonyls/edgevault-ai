from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.auth import (
    WORKSPACES,
    WorkspaceContext,
    create_session_token,
    get_optional_workspace,
    verify_workspace_password,
)
from app.core.config import Settings, get_settings
from app.schemas.auth import LoginRequest, SessionResponse, WorkspaceResponse

router = APIRouter(prefix="/auth", tags=["auth"])

type SettingsDep = Annotated[Settings, Depends(get_settings)]
type OptionalWorkspaceDep = Annotated[
    WorkspaceContext | None, Depends(get_optional_workspace)
]


def _workspace_response(workspace: WorkspaceContext) -> WorkspaceResponse:
    return WorkspaceResponse(
        key=workspace.key,
        display_name=workspace.display_name,
        read_only=workspace.read_only,
    )


def _set_session_cookie(
    response: Response,
    settings: Settings,
    workspace: WorkspaceContext,
) -> None:
    secure_cookie = settings.auth_cookie_secure or settings.environment == "production"
    response.set_cookie(
        key=settings.auth_session_cookie_name,
        value=create_session_token(settings, workspace),
        max_age=settings.auth_session_ttl_seconds,
        httponly=True,
        secure=secure_cookie,
        samesite=settings.auth_cookie_samesite,
        path="/",
    )


@router.get("/session", response_model=SessionResponse)
async def get_session(workspace: OptionalWorkspaceDep) -> SessionResponse:
    if workspace is None:
        return SessionResponse(authenticated=False)
    return SessionResponse(
        authenticated=True,
        workspace=_workspace_response(workspace),
    )


@router.post("/login", response_model=SessionResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    settings: SettingsDep,
) -> SessionResponse:
    if not verify_workspace_password(settings, payload.workspace, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid workspace password.",
        )

    workspace = WORKSPACES[payload.workspace]
    _set_session_cookie(response, settings, workspace)
    return SessionResponse(
        authenticated=True,
        workspace=_workspace_response(workspace),
    )


@router.post("/logout", response_model=SessionResponse)
async def logout(response: Response, settings: SettingsDep) -> SessionResponse:
    secure_cookie = settings.auth_cookie_secure or settings.environment == "production"
    response.delete_cookie(
        key=settings.auth_session_cookie_name,
        path="/",
        secure=secure_cookie,
        samesite=settings.auth_cookie_samesite,
    )
    return SessionResponse(authenticated=False)
