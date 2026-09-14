# Kalender 0.5.2

0.5.2 erweitert die Kalenderplattform um eine alltagstaugliche Oberfläche und eine explizite CalDAV-Konfliktauflösung.

## Ansichten

- `/calendar/view?mode=month` – Monatsansicht
- `/calendar/view?mode=week` – Wochenansicht
- `/calendar/view?mode=day` – Tagesansicht

Die Ansichten unterstützen Datumsnavigation, Kalenderfilter und kalenderbezogene Farben.

## Terminverwaltung

Termine können bearbeitet, in einen anderen Kalender verschoben, zeitlich verschoben und über die bestehende Tombstone-Logik gelöscht werden. Änderungen setzen `updated_at`, damit der CalDAV-Sync aus 0.5.1 sie erkennt.

## Kalenderfarben

`calendars.color` speichert die Farbe je Kalender. Migration `0007_calendar_ui.py` ergänzt die Spalte mit einem Standardwert.

## Konfliktauflösung

`/calendar/conflicts` zeigt offene CalDAV-Konflikte. Zwei Entscheidungen stehen zur Verfügung:

- Lokale Version behalten: zunächst wird das aktuelle Remote-ETag geladen, danach wird die lokale Version sicher erneut synchronisiert.
- Nextcloud übernehmen: das Remote-VEVENT wird geladen und ersetzt die lokale Terminversion.

Die API-Endpunkte sind:

- `POST /api/v1/calendar-sync/conflicts/{event_id}/local`
- `POST /api/v1/calendar-sync/conflicts/{event_id}/remote`

## Betrieb

Vor dem Start der neuen Version muss `alembic upgrade head` ausgeführt werden. Im vorgesehenen Debian-Service erfolgt dies bereits über den Migrationsschritt vor dem Dienststart.

## Noch offen

- automatische zeitgesteuerte Synchronisation
- serverseitige Erinnerungszustellung
- optionales Drag-and-drop im Browser
- Einladungen und Teilnehmer
