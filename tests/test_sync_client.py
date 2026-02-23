from __future__ import annotations

import uuid

import pytest

from dev2cloud.client import Dev2Cloud
from dev2cloud.exceptions import Dev2CloudApiError
from dev2cloud.models import (
    Sandbox,
    SandboxStatus,
    SandboxType,
    PostgresCredentials,
    RedisCredentials,
)


class TestCreateSandbox:
    def test_create_postgres(self, client: Dev2Cloud) -> None:
        sandbox = client.create_sandbox(SandboxType.POSTGRES)
        try:
            assert isinstance(sandbox, Sandbox)
            assert sandbox.sandbox_type == SandboxType.POSTGRES
            assert sandbox.status == SandboxStatus.RUNNING
            assert isinstance(sandbox.credentials, PostgresCredentials)
            assert sandbox.credentials.host
            assert sandbox.credentials.port == 5432
            assert sandbox.credentials.user
            assert sandbox.credentials.password
            assert sandbox.url is not None
            assert sandbox.url.startswith("postgresql://")
        finally:
            client.delete_sandbox(sandbox.id)

    def test_create_redis(self, client: Dev2Cloud) -> None:
        sandbox = client.create_sandbox(SandboxType.REDIS)
        try:
            assert isinstance(sandbox, Sandbox)
            assert sandbox.sandbox_type == SandboxType.REDIS
            assert sandbox.status == SandboxStatus.RUNNING
            assert isinstance(sandbox.credentials, RedisCredentials)
            assert sandbox.credentials.host
            assert sandbox.url is not None
            assert sandbox.url.startswith("redis://")
        finally:
            client.delete_sandbox(sandbox.id)

    def test_create_named_sandbox_is_idempotent(self, client: Dev2Cloud) -> None:
        name = f"test-{uuid.uuid4().hex[:8]}"
        first = client.create_sandbox(SandboxType.POSTGRES, name=name)
        try:
            second = client.create_sandbox(SandboxType.POSTGRES, name=name)
            assert first.id == second.id
            assert second.name == name
        finally:
            client.delete_sandbox(first.id)


class TestGetSandbox:
    def test_get_existing(self, client: Dev2Cloud) -> None:
        created = client.create_sandbox(SandboxType.POSTGRES)
        try:
            fetched = client.get_sandbox(created.id)
            assert fetched.id == created.id
            assert fetched.sandbox_type == created.sandbox_type
            assert fetched.status == SandboxStatus.RUNNING
        finally:
            client.delete_sandbox(created.id)

    def test_get_nonexistent_raises(self, client: Dev2Cloud) -> None:
        with pytest.raises(Dev2CloudApiError):
            client.get_sandbox("nonexistent-id-000")


class TestListSandboxes:
    def test_list_contains_created(self, client: Dev2Cloud) -> None:
        sandbox = client.create_sandbox(SandboxType.POSTGRES)
        try:
            sandboxes = client.list_sandboxes()
            assert isinstance(sandboxes, list)
            ids = [s.id for s in sandboxes]
            assert sandbox.id in ids
        finally:
            client.delete_sandbox(sandbox.id)

    def test_list_returns_sandbox_models(self, client: Dev2Cloud) -> None:
        sandboxes = client.list_sandboxes()
        for sb in sandboxes:
            assert isinstance(sb, Sandbox)


class TestDeleteSandbox:
    def test_delete_existing(self, client: Dev2Cloud) -> None:
        sandbox = client.create_sandbox(SandboxType.POSTGRES)
        client.delete_sandbox(sandbox.id)

        with pytest.raises(Dev2CloudApiError):
            client.get_sandbox(sandbox.id)

    def test_delete_nonexistent_raises(self, client: Dev2Cloud) -> None:
        with pytest.raises(Dev2CloudApiError):
            client.delete_sandbox("nonexistent-id-000")


class TestDeleteAll:
    def test_delete_all(self, client: Dev2Cloud) -> None:
        s1 = client.create_sandbox(SandboxType.POSTGRES)
        s2 = client.create_sandbox(SandboxType.REDIS)

        deleted = client.delete_all()
        assert s1.id in deleted
        assert s2.id in deleted

        remaining = client.list_sandboxes()
        remaining_ids = [s.id for s in remaining]
        assert s1.id not in remaining_ids
        assert s2.id not in remaining_ids


class TestClientInit:
    def test_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("D2C_API_KEY", raising=False)
        with pytest.raises(Dev2CloudApiError, match="API key is required"):
            Dev2Cloud()

    def test_explicit_api_key(self) -> None:
        c = Dev2Cloud(api_key="d2c_test_dummy_key")
        assert c._client.headers["X-Api-Key"] == "d2c_test_dummy_key"
