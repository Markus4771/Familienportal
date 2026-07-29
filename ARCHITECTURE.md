# Architektur

## Technologiestack

- Backend: Python 3.12+, FastAPI, Pydantic
- Datenzugriff: SQLAlchemy 2, Alembic
- Datenbank: PostgreSQL; SQLite nur für Entwicklung und Tests
- Oberfläche: Jinja2, HTMX, Bootstrap
- Hintergrundaufgaben: zunächst interne Job-Schnittstelle; später optional Redis-Queue
- API: versionierte REST-API unter `/api/v1`

## Verbindliche Betriebsarchitektur

- Hauptplattform: Debian Stable
- Reverse Proxy: vorhandenes Nginx
- Familienportal, Nextcloud und Mailcow werden als getrennte Dienste betrieben.
- Jeder Dienst besitzt eigene Konfigurationen, Datenhaltung, Updates, Protokolle und Sicherungen.
- Integrationen erfolgen ausschließlich über dokumentierte Connectoren, APIs und standardisierte Protokolle.
- Das Familienportal bindet intern nur an eine lokale Adresse und wird ausschließlich über Nginx veröffentlicht.

Details stehen in `DEPLOYMENT.md`.

## Schichten

```text
Browser / PWA
    |
  Nginx
    |
FastAPI-Anwendung
    -> Core-Dienste
    -> Modul-API
    -> Connector-API
       -> PostgreSQL
       -> Nextcloud (getrennter Dienst)
       -> Mailcow (getrennter Dienst)
```

## Core

Der Core enthält ausschließlich Plattformfunktionen:

- Authentifizierung und Sitzungen
- Benutzer, Haushalte, Gruppen und Familienzweige
- Rollen und Berechtigungen
- Profile
- Modul- und Connector-Registrierung
- Konfiguration und Geheimnisreferenzen
- Event-Bus
- Benachrichtigungen
- Auditprotokoll
- Gesundheitsstatus

## Module

Module können registrieren:

- API-Router
- Menüpunkte
- Dashboard-Widgets
- Berechtigungen
- Datenbankmigrationen
- Hintergrundaufgaben
- Ereignis-Listener
- Einstellungen
- Übersetzungen
- Supportdiagnosen

Jedes Modul besitzt ein Manifest. Direkte Änderungen am Core sollen für neue Fachfunktionen nicht erforderlich sein.

## Connectoren

Connectoren kapseln externe Systeme. Sie stellen standardisierte Fähigkeiten bereit, zum Beispiel `files`, `calendar`, `contacts`, `mailboxes`, `aliases` oder `health`.

Erste Connectoren:

- Nextcloud
- Mailcow

Spätere Connectoren:

- Home Assistant
- Matrix
- Paperless-ngx
- Immich
- Jellyfin

## Datenhaltung

PostgreSQL speichert Benutzer, Rechte, Moduleinstellungen, Metadaten und Auditdaten. Cloud-Dateien werden nicht als große Binärdaten in PostgreSQL abgelegt. Sie verbleiben in Nextcloud oder einem angebundenen Dateispeicher.

Jeder externe Dienst verwendet seine eigene Datenbank und seine eigenen Speicherbereiche. Direkte Datenbankzugriffe zwischen Familienportal, Nextcloud und Mailcow sind nicht zulässig.

## Sicherheit

- geringstmögliche Rechte
- deklarative Modulberechtigungen
- verschlüsselte oder externe Geheimnisablage
- keine Geheimnisse in Diagnosepaketen
- Auditprotokoll für administrative Aktionen
- signierbare Module als spätere Ausbaustufe
- Schutz vor unsicheren Modulabhängigkeiten
- PostgreSQL nicht öffentlich erreichbar
- Connectorzugriffe ausschließlich verschlüsselt
- getrennte Dienstkonten und API-Schlüssel je Integration

## Profile

Profile sind vorkonfigurierte Modulsätze, keine getrennten Codebasen.

- `small_family`: schlanker Funktionsumfang für einen Haushalt
- `extended_family`: zusätzliche Dienste und Organisation für mehrere Haushalte

Module bleiben einzeln aktivierbar.
