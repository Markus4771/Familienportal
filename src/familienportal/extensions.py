from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ExtensionManifest:
    """Common metadata for installable modules and connectors."""

    identifier: str
    name: str
    version: str
    minimum_portal_version: str
    description: str = ""
    permissions: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()


@dataclass(slots=True)
class HealthResult:
    healthy: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


class PortalModule(ABC):
    """Base contract for independently developed Familienportal modules."""

    manifest: ExtensionManifest

    @abstractmethod
    def register(self, application: Any) -> None:
        """Register routers, permissions, widgets, events and jobs."""


class Connector(ABC):
    """Base contract for external service integrations."""

    manifest: ExtensionManifest

    @abstractmethod
    async def health(self) -> HealthResult:
        """Check whether the configured external service is reachable."""
