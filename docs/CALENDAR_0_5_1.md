# Kalender 0.5.1 – Nextcloud-CalDAV-Synchronisation

0.5.1 erweitert die Kalenderplattform um eine bidirektionale Synchronisation mit Nextcloud-CalDAV.

## Datenmodell

`calendar_sync_bindings` verknüpft einen lokalen Kalender mit einem Remote-CalDAV-Kalender. Gespeichert werden Remote-Href, Name, Sync-Token, letzter Lauf und Status.

`calendar_event_sync_states` speichert je Termin Remote-Href, ETag, letzten lokalen Synchronisationsstand und Konfliktinformationen.

`calendar_events.deleted_at` dient als Tombstone. Dadurch bleibt ein lokal gelöschter Termin bis zum nächsten erfolgreichen CalDAV-Löschvorgang erhalten.

## Synchronisationslogik

Ein Lauf liest VEVENT-Objekte per CalDAV REPORT. Neue Remote-Termine werden lokal angelegt. Geänderte Remote-Termine werden anhand des ETags erkannt. Neue oder geänderte lokale Termine werden per PUT übertragen. Für bestehende Objekte wird `If-Match` verwendet; neue Objekte verwenden `If-None-Match: *`.

Wenn eine lokale und eine Remote-Version seit dem letzten erfolgreichen Sync geändert wurden, wird kein automatisches Überschreiben vorgenommen. Der Termin erhält stattdessen einen Konfliktstatus.

Remote-Löschungen werden lokal übernommen, sofern der lokale Termin seit dem letzten Sync nicht verändert wurde. Lokale Löschungen werden nach Nextcloud übertragen und anschließend endgültig aus der lokalen Datenbank entfernt.

## API

- `GET /api/v1/calendar-sync/bindings` – Zuordnungen und Status
- `POST /api/v1/calendar-sync/bindings` – lokalen und Remote-Kalender verknüpfen
- `GET /api/v1/calendar-sync/conflicts` – offene Konflikte
- `POST /api/v1/calendar-sync/{binding_id}/run` – manuellen Sync ausführen

Die API ist auf Administratoren beschränkt und verwendet die bereits konfigurierte Nextcloud-Verbindung einschließlich der Secret-Referenz.

## Migration

Migration `0006_calendar_caldav_sync.py` legt die Sync-Tabellen an und ergänzt `calendar_events.deleted_at`.

## Noch sinnvoll für 0.5.2

- grafische Konfliktauflösung mit „lokal behalten“ / „Nextcloud behalten“
- automatischer Scheduler für periodische Synchronisation
- Monats-, Wochen- und Tagesansicht
- serverseitige Zustellung von Erinnerungen

## Betrieb

Nach dem Update muss `alembic upgrade head` ausgeführt werden. Vor dem ersten Sync müssen Nextcloud-Connector, Servicekonto und App-Passwort funktionieren. Danach wird über die Sync-API ein lokaler Kalender mit dem gewünschten Remote-Kalender-Href verknüpft.
