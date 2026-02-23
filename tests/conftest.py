from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv

from dev2cloud.client import Dev2Cloud
from dev2cloud.asyncio import Dev2Cloud as AsyncDev2Cloud


def pytest_configure(config: pytest.Config) -> None:
    load_dotenv()


@pytest.fixture(scope="session")
def api_key() -> str:
    key = os.environ.get("D2C_API_KEY")
    if not key:
        pytest.skip("D2C_API_KEY not set — skipping integration tests")
    return key


@pytest.fixture(scope="session", autouse=True)
def _cleanup(api_key: str) -> None:  # noqa: N802
    """Delete all sandboxes before the test run."""
    Dev2Cloud(api_key=api_key).delete_all()


@pytest.fixture(scope="session")
def client(api_key: str) -> Dev2Cloud:
    return Dev2Cloud(api_key=api_key)


@pytest.fixture
def async_client(api_key: str) -> AsyncDev2Cloud:
    return AsyncDev2Cloud(api_key=api_key)
