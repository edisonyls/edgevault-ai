from typing import Literal

from pydantic import BaseModel, Field

WorkspaceKey = Literal["owner", "demo"]


class LoginRequest(BaseModel):
    workspace: WorkspaceKey = "owner"
    password: str = Field(min_length=1, max_length=512)


class WorkspaceResponse(BaseModel):
    key: WorkspaceKey
    display_name: str
    read_only: bool


class SessionResponse(BaseModel):
    authenticated: bool
    workspace: WorkspaceResponse | None = None
