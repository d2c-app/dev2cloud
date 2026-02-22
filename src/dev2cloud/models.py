from __future__ import annotations

from enum import Enum
from typing import Optional, Union

from typing import Any, Dict

from pydantic import BaseModel, model_validator


class SandboxType(str, Enum):
    POSTGRES = "postgres"
    REDIS = "redis"


class SandboxStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"


class PostgresCredentials(BaseModel):
    user: str
    password: str
    host: str = "connect.dev2.cloud"
    port: int = 5432
    database: str = "postgres"


class RedisCredentials(BaseModel):
    user: Optional[str] = None
    password: Optional[str] = None
    host: str = "connect.dev2.cloud"
    port: int = 6379
    database: int = 0


class Sandbox(BaseModel):
    id: str
    sandbox_type: SandboxType
    status: SandboxStatus
    credentials: Union[PostgresCredentials, RedisCredentials, None] = None
    url: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def parse_credentials(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(data, dict):
            creds = data.get("credentials")
            if isinstance(creds, dict):
                sandbox_type = data.get("sandbox_type")
                if sandbox_type == "postgres":
                    data["credentials"] = PostgresCredentials(**creds)
                elif sandbox_type == "redis":
                    data["credentials"] = RedisCredentials(**creds)
        return data

    @model_validator(mode="after")
    def try_build_url(self) -> Sandbox:
        if self.credentials:
            if self.sandbox_type == "postgres":
                self.url = f"postgresql://{self.credentials.user}:{self.credentials.password}@{self.credentials.host}:{self.credentials.port}/{self.credentials.database}"
            elif self.sandbox_type == "redis":
                auth = ""
                if self.credentials.password:
                    user = self.credentials.user or ""
                    auth = f"{user}:{self.credentials.password}@"
                self.url = f"redis://{auth}{self.credentials.host}:{self.credentials.port}/{self.credentials.database}"
        return self
