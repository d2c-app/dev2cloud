from __future__ import annotations

import uuid

import pytest

from dev2cloud.asyncio import Dev2Cloud as AsyncDev2Cloud
from dev2cloud.exceptions import Dev2CloudApiError
from dev2cloud.models import (
    Sandbox,
    SandboxStatus,
    SandboxType,
    PostgresCredentials,
    RedisCredentials,
)


class TestCreateSandbox:
    async def test_create_postgres(self, async_client: AsyncDev2Cloud) -> None:
        sandbox = await async_client.create_sandbox(SandboxType.POSTGRES)
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
            await async_client.delete_sandbox(sandbox.id)

    async def test_create_redis(self, async_client: AsyncDev2Cloud) -> None:
        sandbox = await async_client.create_sandbox(SandboxType.REDIS)
        try:
            assert isinstance(sandbox, Sandbox)
            assert sandbox.sandbox_type == SandboxType.REDIS
            assert sandbox.status == SandboxStatus.RUNNING
            assert isinstance(sandbox.credentials, RedisCredentials)
            assert sandbox.credentials.host
            assert sandbox.url is not None
            assert sandbox.url.startswith("redis://")
        finally:
            await async_client.delete_sandbox(sandbox.id)

    async def test_create_named_sandbox_is_idempotent(
        self, async_client: AsyncDev2Cloud
    ) -> None:
        name = f"test-{uuid.uuid4().hex[:8]}"
        first = await async_client.create_sandbox(SandboxType.POSTGRES, name=name)
        try:
            second = await async_client.create_sandbox(SandboxType.POSTGRES, name=name)
            assert first.id == second.id
            assert second.name == name
        finally:
            await async_client.delete_sandbox(first.id)


class TestGetSandbox:
    async def test_get_existing(self, async_client: AsyncDev2Cloud) -> None:
        created = await async_client.create_sandbox(SandboxType.POSTGRES)
        try:
            fetched = await async_client.get_sandbox(created.id)
            assert fetched.id == created.id
            assert fetched.sandbox_type == created.sandbox_type
            assert fetched.status == SandboxStatus.RUNNING
        finally:
            await async_client.delete_sandbox(created.id)

    async def test_get_nonexistent_raises(self, async_client: AsyncDev2Cloud) -> None:
        with pytest.raises(Dev2CloudApiError):
            await async_client.get_sandbox("nonexistent-id-000")


class TestListSandboxes:
    async def test_list_contains_created(self, async_client: AsyncDev2Cloud) -> None:
        sandbox = await async_client.create_sandbox(SandboxType.POSTGRES)
        try:
            sandboxes = await async_client.list_sandboxes()
            assert isinstance(sandboxes, list)
            ids = [s.id for s in sandboxes]
            assert sandbox.id in ids
        finally:
            await async_client.delete_sandbox(sandbox.id)

    async def test_list_returns_sandbox_models(
        self, async_client: AsyncDev2Cloud
    ) -> None:
        sandboxes = await async_client.list_sandboxes()
        for sb in sandboxes:
            assert isinstance(sb, Sandbox)


class TestDeleteSandbox:
    async def test_delete_existing(self, async_client: AsyncDev2Cloud) -> None:
        sandbox = await async_client.create_sandbox(SandboxType.POSTGRES)
        await async_client.delete_sandbox(sandbox.id)

        with pytest.raises(Dev2CloudApiError):
            await async_client.get_sandbox(sandbox.id)

    async def test_delete_nonexistent_raises(
        self, async_client: AsyncDev2Cloud
    ) -> None:
        with pytest.raises(Dev2CloudApiError):
            await async_client.delete_sandbox("nonexistent-id-000")


class TestDeleteAll:
    async def test_delete_all(self, async_client: AsyncDev2Cloud) -> None:
        s1 = await async_client.create_sandbox(SandboxType.POSTGRES)
        s2 = await async_client.create_sandbox(SandboxType.REDIS)

        deleted = await async_client.delete_all()
        assert s1.id in deleted
        assert s2.id in deleted

        remaining = await async_client.list_sandboxes()
        remaining_ids = [s.id for s in remaining]
        assert s1.id not in remaining_ids
        assert s2.id not in remaining_ids


class TestClientInit:
    def test_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("D2C_API_KEY", raising=False)
        with pytest.raises(Dev2CloudApiError, match="API key is required"):
            AsyncDev2Cloud()

    def test_explicit_api_key(self) -> None:
        c = AsyncDev2Cloud(api_key="d2c_test_dummy_key")
        assert c._client.headers["X-Api-Key"] == "d2c_test_dummy_key"
