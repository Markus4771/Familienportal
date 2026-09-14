# Plattform 0.3

Version 0.3 erweitert den Familienportal-Core um eine verwaltbare Modul- und Connector-Plattform.

## 0.3.1 – Dynamisches Dashboard und Navigation

Eingebaute Module werden zentral in `familienportal.extensions.BUILTIN_MODULES` beschrieben. Neben Name, Icon und Beschreibung enthält jedes Modul jetzt auch eine Route und das benötigte Leserecht.

Der Aktivierungszustand wird je Familie in `module_states` gespeichert. Dashboard und Navigation verwenden `familienportal.platform_runtime` und zeigen nur Module, die:

- für die Familie aktiviert sind und
- für den angemeldeten Benutzer freigegeben sind.

Direkte Modulaufrufe unter `/modules/{module_key}` prüfen ebenfalls Aktivierung und Berechtigung. Damit kann die Oberfläche nicht durch manuelles Aufrufen einer URL umgangen werden.

Aktivierte Connectoren erscheinen mit ihrem aktuellen Gesundheitsstatus im Dashboard.

## 0.3.2 – Rollen, Rechte und Benutzerzuordnung

Rollen besitzen eine kommaseparierte Berechtigungsliste. `familienportal.permissions` unterstützt:

- exakte Rechte wie `calendar.read`
- Namespace-Wildcards wie `calendar.*`
- globale Administratorberechtigung `*`
- Superadministrator-Bypass

Unter `/admin/roles` werden die von den eingebauten Modulen erwarteten Rechte angezeigt. Unter `/admin` können einem Benutzer mehrere Rollen zugewiesen werden. Änderungen werden im Audit protokolliert.

## 0.3.3 – Connector-Healthchecks und Einstellungen

Externe Dienste werden über `BUILTIN_CONNECTORS` beschrieben. Je Familie werden Aktivierung, Basis-URL und Gesundheitsstatus in `connector_states` gespeichert.

Die Plattformseite `/platform` erlaubt einen manuellen Verbindungstest. Der generische Healthcheck prüft die konfigurierte HTTP/HTTPS-Basis-URL mit kurzem Timeout und speichert Status und Meldung für das Dashboard. Dienstspezifische API-Prüfungen folgen mit den jeweiligen Connector-Releases.

`family_settings` speichert familienbezogene Einstellungen als Schlüssel/Wert-Paare. Die HTML-Oberfläche `/settings` verwaltet derzeit:

- Portalname
- Zeitzone
- Sprache
- Familienprofil Kleinfamilie/Großfamilie

Zugangsdaten werden bewusst noch nicht in `family_settings` oder `connector_states` gespeichert. Dafür ist eine separate Secret-Verwaltung vorgesehen.

## HTML-Verwaltung

- `/dashboard` – dynamische Module und Connectorstatus
- `/platform` – Module, Connectoren und Verbindungstests
- `/settings` – Familieneinstellungen
- `/admin` – Benutzer, Haushalte und Rollen-Zuordnung
- `/admin/roles` – Rollen und Berechtigungen
- `/modules/{module_key}` – berechtigungsgeprüfter Moduleinstieg

## Migration

`0002_platform_management.py` legt die Tabellen `module_states`, `connector_states` und `family_settings` an. Im Debian-Betrieb wird die Migration vor dem Dienststart automatisch ausgeführt.

## Stand nach 0.3.3-dev

Die Plattformbasis ist für den ersten echten Connector vorbereitet. Die nächsten technischen Themen sind bewusst aus 0.3 herausgenommen:

1. verschlüsselte Secret-Verwaltung
2. dienstspezifische API-Healthchecks
3. Manifest-Discovery für externe Module
4. Modulabhängigkeiten und Kompatibilitätsprüfung
5. App-Center und Installationsprozess

Der nächste geplante Produktblock ist der Nextcloud-Connector 0.4.x.
