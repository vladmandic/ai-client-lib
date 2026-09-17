"""Helpers for provider APIs whose endpoint contract is not verified yet."""

from __future__ import annotations

from typing import Any

from .core import CapabilityError, ClientConfig, ProviderHttpClient, Response


class UnsupportedProvider(ProviderHttpClient):
    """Base class for an adapter that is documented but not endpoint-complete."""

    provider_label = "provider"

    def __init__(self, api_key: str | list[str], config: ClientConfig | None = None):
        super().__init__(self.provider_label, api_key, config)

    def _unsupported(self, operation: str) -> None:
        raise CapabilityError(
            f"{self.provider_label} {operation} is unavailable until its endpoint contract is verified"
        )

    def submit(self, *args: Any, **kwargs: Any) -> Response:
        del args, kwargs
        self._unsupported("submit")

    def submit_async(self, *args: Any, **kwargs: Any) -> Response:
        del args, kwargs
        self._unsupported("submit_async")

    def status(self, *args: Any, **kwargs: Any) -> Response:
        del args, kwargs
        self._unsupported("status")

    def cancel(self, *args: Any, **kwargs: Any) -> Response:
        del args, kwargs
        self._unsupported("cancel")
