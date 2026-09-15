# Familienportal 0.9.0 – Integration & Administration

## Ziel
0.9.0 bündelt den technischen Betriebszustand des Familienportals und seiner externen Dienste in einer zentralen Administration.

## Oberflächen
- `/admin/system` – Systemstatus mit Benutzer-, Haushalts-, Modul-, Integrations- und Auditübersicht.
- `/admin/integrations` – zentrale Integrationsverwaltung.
- `/admin/integrations/{connector_key}/diagnostics` – mehrstufige Diagnose eines Connectors.

## API
`GET /api/v1/admin/system/status` liefert eine administrative Statusübersicht. Zugangsdaten, Tokens und Secret-Werte werden nicht ausgegeben.

## Unterstützte Integrationen
- Nextcloud
- Mailcow
- Gramps Web
- Paperless-ngx

## Diagnose
Die Diagnose unterscheidet Konfiguration, Netzwerk/HTTP, Secret-Verfügbarkeit und dienstspezifischen API-Zugriff. Die API-Prüfung verwendet den vorhandenen Connector-Client und damit die tatsächlich konfigurierte Authentifizierung.

## Statuswerte
- `healthy`: Prüfung erfolgreich.
- `degraded`: erreichbar, aber mit Warnung.
- `error`: Konfigurations-, Netzwerk-, Authentifizierungs- oder API-Fehler.
- `disabled`: Connector deaktiviert.
- `not_checked`: noch nicht vollständig geprüft.

## Sicherheit
- Admin-Seiten verwenden die bestehende Administratorprüfung.
- Status-API liefert keine Secrets.
- Secret-Referenzen werden über Umgebungsvariablen aufgelöst; Werte werden nicht in ConnectorState gespeichert.
- Health- und Diagnosemeldungen dürfen keine Tokens oder Passwörter enthalten.

## Betrieb
Vor einer produktiven 0.9.0-Freigabe müssen alle Connectoren in einer Debian-Testinstallation mit realen Diensten geprüft werden. Die CI deckt die Softwarelogik ab, ersetzt aber keinen Live-Test der externen APIs.

## Nächster Versionsblock
Nach Abschluss von 0.9.0 beginnt 0.10.x mit den Familienalltagsmodulen: Aufgaben, Einkaufslisten, Notizen, Haushalt und deren Verknüpfung mit Kalender und Dashboard.
