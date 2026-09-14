# Plattform 0.3

Version 0.3 erweitert den Familienportal-Core um eine verwaltbare Modul- und Connector-Plattform.

## Modulregistry

Eingebaute Module werden zentral in `familienportal.extensions.BUILTIN_MODULES` beschrieben. Die Registry enthält Name, Icon, Beschreibung, Standardstatus und Menüfähigkeit. Der Aktivierungszustand wird je Familie in `module_states` gespeichert.

## Connectorregistry

Externe Dienste werden über `BUILTIN_CONNECTORS` beschrieben. Je Familie werden Aktivierung, Basis-URL und Gesundheitsstatus in `connector_states` gespeichert. Zugangsdaten gehören nicht in diese Tabelle; dafür ist die spätere Secret-Verwaltung vorgesehen.

## Zentrale Einstellungen

`family_settings` speichert familienbezogene Einstellungen als Schlüssel/Wert-Paare. Die erste HTML-Oberfläche verwaltet Portalname, Zeitzone und Sprache.

## Rechte

Rollen besitzen weiterhin eine kommaseparierte Berechtigungsliste. `familienportal.permissions` stellt eine zentrale Auswertung bereit und unterstützt:

- exakte Rechte wie `calendar.read`
- Namespace-Wildcards wie `calendar.*`
- globale Administratorberechtigung `*`
- Superadministrator-Bypass

## HTML-Verwaltung

- `/platform` – Module und Connectoren
- `/settings` – Familieneinstellungen
- `/admin/roles` – Rollen und Berechtigungen

## Migration

`0002_platform_management.py` legt die Tabellen `module_states`, `connector_states` und `family_settings` an. Im Debian-Betrieb wird die Migration vor dem Dienststart automatisch ausgeführt.

## Nächste Schritte

1. Dashboard-Widgets vollständig aus aktiven Modulen generieren.
2. Dynamische Navigation nach Modulstatus und Benutzerrechten.
3. Connector-Health-Checks gegen reale APIs.
4. Verschlüsselte Secret-Verwaltung.
5. Manifest-Discovery für externe Module.
6. Modulabhängigkeiten und Kompatibilitätsprüfung.
7. App-Center und Installationsprozess.
