# Nextcloud-Connector 0.4.1

## Ziel

0.4.1 vervollständigt die Nextcloud-Verwaltung des Familienportals. Nextcloud bleibt ein eigenständiger Dienst und wird ausschließlich über standardisierte APIs und DAV angesprochen.

## Zugangsdaten

Das App-Passwort wird nicht in der Datenbank gespeichert. `connector_states.secret_reference` enthält nur den Namen einer Umgebungsvariable, standardmäßig `FAMILIENPORTAL_NEXTCLOUD_APP_PASSWORD`.

Beispiel für das Environment des systemd-Dienstes:

```text
FAMILIENPORTAL_NEXTCLOUD_APP_PASSWORD=<Nextcloud-App-Passwort>
```

## Verwaltung

- `/platform/nextcloud` – Basisstatus des Connectors
- `/platform/nextcloud/management` – Benutzer, Gruppen, Familienordner und DAV-Diagnose

## Benutzerzuordnung

`nextcloud_user_mappings` verbindet einen Benutzer des Familienportals eindeutig mit einer Nextcloud-Benutzer-ID. Eine Nextcloud-ID kann innerhalb einer Familie nur einmal zugeordnet werden.

## Gruppenzuordnung

`nextcloud_group_mappings` ordnet eine Nextcloud-Gruppe entweder der gesamten Familie oder einem Haushalt zu. Die Zuordnung ist zunächst deklarativ und bildet die Grundlage für spätere Synchronisationsjobs.

## Familienordner

Über WebDAV `MKCOL` kann das Portal einen Ordner im Dateibereich des konfigurierten Nextcloud-Servicekontos anlegen. Der Pfad wird anschließend in `nextcloud_family_folders` registriert und kann optional einem Haushalt zugeordnet werden.

## Diagnose

Die Diagnose prüft die OCS-Anmeldung und den WebDAV-Zugriff. Zusätzlich werden die berechneten CalDAV- und CardDAV-Endpunkte angezeigt. Dadurch lässt sich die Connector-Konfiguration vor der Kalenderphase 0.5 prüfen.

## Migration

Alembic-Migration `0004_nextcloud_mappings.py` legt folgende Tabellen an:

- `nextcloud_user_mappings`
- `nextcloud_group_mappings`
- `nextcloud_family_folders`

## Sicherheit

- keine App-Passwörter in Datenbank oder HTML
- Secret nur über Umgebungsvariable
- Mapping-Routen ausschließlich für Administratoren
- Familien- und Haushaltszugehörigkeit wird serverseitig geprüft
- Ordnerpfade werden vor DAV-Zugriff normalisiert
- relevante Änderungen werden im Audit protokolliert

## Nächster Schritt

Phase 0.5 kann auf den vorhandenen CalDAV-Endpunkten und Benutzerzuordnungen aufbauen. Der erste Schwerpunkt ist ein Familienkalender mit persönlicher und gemeinsamer Ansicht.
