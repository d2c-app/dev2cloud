from __future__ import annotations

import os
import time

import httpx

from dev2cloud.exceptions import Dev2CloudApiError
from dev2cloud.models import Sandbox, SandboxStatus, SandboxType


class Dev2Cloud:
    """Sync client for the Dev2Cloud sandbox management API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.dev2.cloud",
    ) -> None:
        resolved_key = api_key or os.environ.get("D2C_API_KEY")
        if not resolved_key:
            raise Dev2CloudApiError(
                0,
                "API key is required. Pass it directly or set the D2C_API_KEY environment variable.",
            )

        self._sandboxes_path = "/api/v1/sandboxes"
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"X-Api-Key": resolved_key},
        )

    @staticmethod
    def _raise_on_error(response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise Dev2CloudApiError(response.status_code, detail)

    def create_sandbox(
        self,
        sandbox_type: SandboxType,
        *,
        name: str | None = None,
        timeout: float = 180,
    ) -> Sandbox:
        """Create a new sandbox and wait until it is ready.

        Provisions a sandbox of the given *sandbox_type* and polls its
        status every second until it transitions to ``running`` or
        ``failed``.

        When *name* is provided the endpoint behaves as **get-or-create**:
        if a running or pending sandbox with the same name already exists
        it is returned directly; otherwise a new one is created.  A
        ``409 Conflict`` is raised when the existing sandbox has a
        different *sandbox_type*.

        Args:
            sandbox_type: ``"postgres"`` or ``"redis"``.
            name: Optional name for get-or-create semantics.
            timeout: Maximum seconds to wait. Defaults to 180.

        Returns:
            The sandbox with ``running`` status and connection credentials.

        Raises:
            Dev2CloudApiError: On API errors, provision failure, or timeout.
        """
        response = self._client.post(
            self._sandboxes_path,
            json={"sandbox_type": sandbox_type, "name": name},
        )
        self._raise_on_error(response)

        data = response.json()
        sandbox_id: str = data["id"]

        initial = Sandbox(**data)
        if initial.status == SandboxStatus.FAILED:
            raise Dev2CloudApiError(0, f"Sandbox {sandbox_id} failed to provision")
        if initial.status != SandboxStatus.PENDING:
            return initial

        deadline = time.monotonic() + timeout
        while True:
            if time.monotonic() >= deadline:
                raise Dev2CloudApiError(
                    0,
                    f"Sandbox {sandbox_id} did not become ready within {timeout}s",
                )
            time.sleep(1)
            sandbox = self.get_sandbox(sandbox_id)
            if sandbox.status == SandboxStatus.FAILED:
                raise Dev2CloudApiError(0, f"Sandbox {sandbox_id} failed to provision")
            if sandbox.status != SandboxStatus.PENDING:
                return sandbox

    def get_sandbox(self, sandbox_id: str) -> Sandbox:
        """Get a sandbox by its ID.

        Args:
            sandbox_id: Unique identifier of the sandbox.

        Raises:
            Dev2CloudApiError: If the API returns an error response.
        """
        response = self._client.get(f"{self._sandboxes_path}/{sandbox_id}")
        self._raise_on_error(response)
        return Sandbox(**response.json())

    def list_sandboxes(self) -> list[Sandbox]:
        """List all active sandboxes for the authenticated user.

        Raises:
            Dev2CloudApiError: If the API returns an error response.
        """
        response = self._client.get(self._sandboxes_path)
        self._raise_on_error(response)
        return [Sandbox(**item) for item in response.json()]

    def delete_sandbox(self, sandbox_id: str) -> None:
        """Permanently delete a sandbox.

        Connection credentials are revoked immediately.

        Args:
            sandbox_id: Unique identifier of the sandbox to delete.

        Raises:
            Dev2CloudApiError: If the API returns an error response.
        """
        response = self._client.delete(f"{self._sandboxes_path}/{sandbox_id}")
        self._raise_on_error(response)

    def delete_all(self) -> list[str]:
        """Delete all active sandboxes.

        Individual deletion errors are silently ignored so that one
        failure does not prevent the remaining sandboxes from being
        removed.

        Returns:
            IDs of successfully deleted sandboxes.
        """
        sandboxes = self.list_sandboxes()
        deleted: list[str] = []
        for sb in sandboxes:
            try:
                self.delete_sandbox(sb.id)
                deleted.append(sb.id)
            except Dev2CloudApiError:
                pass
        return deleted
