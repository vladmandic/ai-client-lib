"""Unified provider facade."""

from __future__ import annotations

from typing import Any, Self

from .byteplus import BytePlus
from .core import ClientConfig, ProviderPoolRegistry
from .fal import Fal
from .kie import Kie
from .pixverse import Pixverse

PROVIDERS = {
    "fal": Fal,
    "kie": Kie,
    "pixverse": Pixverse,
    "byteplus": BytePlus,
}


class Client:
    """Select and forward calls to one provider adapter."""

    def __init__(
        self,
        provider: str,
        api_key: str | list[str] | None = None,
        config: ClientConfig | None = None,
    ):
        try:
            provider_class = PROVIDERS[provider.lower()]
        except KeyError as error:
            raise ValueError(f"unsupported provider: {provider}") from error
        self.provider = provider.lower()
        self.adapter = provider_class(api_key=api_key, config=config)

    def submit(self, *args: Any, **kwargs: Any) -> Any:
        return self.adapter.submit(*args, **kwargs)

    def submit_async(self, *args: Any, **kwargs: Any) -> Any:
        return self.adapter.submit_async(*args, **kwargs)

    def status(self, *args: Any, **kwargs: Any) -> Any:
        return self.adapter.status(*args, **kwargs)

    def cancel(self, *args: Any, **kwargs: Any) -> Any:
        return self.adapter.cancel(*args, **kwargs)

    def current_requests(self) -> int:
        return self.adapter.resources.stats.current_requests()

    def active_http_requests(self) -> int:
        return self.adapter.resources.stats.active_http_requests()

    def records(self) -> list[dict[str, Any]]:
        return self.adapter.resources.stats.records()

    def close(self) -> None:
        self.adapter.close()

    @staticmethod
    def close_all() -> None:
        ProviderPoolRegistry.close_all()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
