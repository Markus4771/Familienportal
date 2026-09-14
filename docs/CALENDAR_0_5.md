# Kalenderplattform 0.5

Version 0.5.0-dev ergänzt das Familienportal um eine eigene Kalenderplattform.

## Kalenderarten

Beim ersten Aufruf werden pro Familie die Standardkalender `Familienkalender`, `Geburtstage` und `Veranstaltungen` angelegt. Zusätzlich erhält jeder Benutzer beim ersten Kalenderaufruf einen persönlichen Kalender. Weitere Kalender können für Schule, Arbeit, Verein oder andere Zwecke angelegt werden.

## Termine

Ein Termin kann Titel, Beschreibung, Ort, Kategorie, Beginn, Ende, Ganztagsstatus, Wiederholungsregel und Erinnerung enthalten. Wiederholungen werden als iCalendar-RRULE gespeichert. Die Erinnerungszeit wird beim ICS-Export als VALARM ausgegeben.

## Geburtstage und Gedenktage

Geburtstage, Jahrestage und Gedenktage werden separat gespeichert. Damit können später automatische Jahresansichten, Dashboard-Widgets und Erinnerungen aufgebaut werden.

## ICS

Jeder Kalender kann als ICS exportiert werden. Der Import akzeptiert VEVENT-Einträge mit UID, DTSTART, DTEND, SUMMARY, DESCRIPTION, LOCATION und RRULE. Bereits bekannte externe UIDs werden beim Import übersprungen.

## Nextcloud / CalDAV

Die bestehende Nextcloud-Servicekonto-Konfiguration wird wiederverwendet. Unter `/calendar/caldav` kann die CalDAV-Verbindung geprüft werden; vorhandene Kalender des Nextcloud-Servicekontos werden per PROPFIND erkannt.

0.5.0 führt noch keine automatische bidirektionale Synchronisation aus. Eine spätere 0.5.x-Version kann dafür lokale Kalender mit entfernten DAV-Kalendern verknüpfen und Sync-Token/ETags speichern.

## Rechte

- `calendar.read` erlaubt das Lesen.
- `calendar.write` erlaubt Änderungen.
- `calendar.*` umfasst alle Kalenderrechte.
- Superadministratoren besitzen wie bisher vollständigen Zugriff.

## Migration

`0005_calendar_platform.py` erzeugt die Tabellen `calendars`, `calendar_events` und `birthdays`.

## Routen

- `/calendar` – Kalenderoberfläche
- `/calendar/{calendar_id}.ics` – ICS-Export
- `/calendar/import` – ICS-Import
- `/calendar/caldav` – Nextcloud-CalDAV-Diagnose
