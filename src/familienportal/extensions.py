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
    manifest: ExtensionManifest

    @abstractmethod
    def register(self, application: Any) -> None:
        """Register routers, permissions, widgets, events and jobs."""


class Connector(ABC):
    manifest: ExtensionManifest

    @abstractmethod
    async def health(self) -> HealthResult:
        """Check whether the configured external service is reachable."""


BUILTIN_MODULES: dict[str, dict[str, object]] = {
    "calendar": {
        "name": "Kalender",
        "icon": "bi-calendar3",
        "description": "Familien-, Geburtstags- und Veranstaltungskalender",
        "default": True,
        "menu": True,
        "permission": "calendar.read",
        "route": "/calendar",
    },
    "news": {
        "name": "Nachrichten",
        "icon": "bi-newspaper",
        "description": "Familiennachrichten und Mitteilungen",
        "default": False,
        "menu": True,
        "permission": "news.read",
        "route": "/modules/news",
    },
    "marketplace": {
        "name": "Kleinanzeigen",
        "icon": "bi-shop",
        "description": "Suchen, Tauschen und Verschenken",
        "default": False,
        "menu": True,
        "permission": "marketplace.read",
        "route": "/modules/marketplace",
    },
    "support": {
        "name": "Support",
        "icon": "bi-life-preserver",
        "description": "Tickets, Hilfe und Wissensdatenbank",
        "default": False,
        "menu": True,
        "permission": "support.read",
        "route": "/modules/support",
    },
    "genealogy": {
        "name": "Ahnenforschung",
        "icon": "bi-diagram-3",
        "description": "Integration von Gramps Web",
        "default": False,
        "menu": True,
        "permission": "genealogy.read",
        "route": "/modules/genealogy",
    },
    "documents": {
        "name": "Dokumente",
        "icon": "bi-file-earmark-text",
        "description": "Dokumente und Familienordner",
        "default": False,
        "menu": True,
        "permission": "documents.read",
        "route": "/modules/documents",
    },
}

BUILTIN_CONNECTORS: dict[str, dict[str, object]] = {
    "nextcloud": {"name": "Nextcloud", "icon": "bi-cloud", "description": "Dateien, Kalender und Kontakte"},
    "mailcow": {"name": "Mailcow", "icon": "bi-envelope", "description": "E-Mail, Postfächer und Verteiler"},
    "gramps": {"name": "Gramps Web", "icon": "bi-diagram-3", "description": "Ahnenforschung und Stammbaum"},
    "homeassistant": {"name": "Home Assistant", "icon": "bi-house-gear", "description": "Smart-Home-Integration"},
    "paperless": {"name": "Paperless-ngx", "icon": "bi-archive", "description": "Dokumentenarchiv"},
    "immich": {"name": "Immich", "icon": "bi-images", "description": "Familienfotos und Alben"},
}
