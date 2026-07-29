# Roadmap

## Phase 0.1 – Plattformbasis

- Projekt- und Architekturdokumentation
- FastAPI-Grundanwendung
- Konfiguration und Health-Endpunkt
- PostgreSQL-/SQLAlchemy-Grundlage
- Profile Kleinfamilie und Großfamilie
- Modul- und Connector-Verträge
- Testbasis
- Debian als verbindliche Zielplattform
- Betrieb hinter vorhandenem Nginx
- getrennte Dienste für Familienportal, Nextcloud und Mailcow

## Phase 0.2 – Benutzer und Rechte

- Benutzer, Haushalte und Familienzweige
- Anmeldung und Sitzungen
- Rollen und Berechtigungen
- Administration
- Auditprotokoll
- Dashboard

## Phase 0.3 – Module und Connectoren

- Modulmanager
- Connector-Manager
- Event-Bus
- dynamische Menüs und Widgets
- Modulberechtigungen
- Beispielmodul und Entwicklerdokumentation

## Phase 0.4 – Großfamilienbasis

- Nachrichtenportal
- Kleinanzeigen
- Familiengruppen
- Support- und Ticketsystem

## Phase 0.5 – Nextcloud

- Verbindungstest
- Benutzer-/Gruppenzuordnung
- Dateien und Familienordner
- WebDAV
- Freigaben
- Kalender und Kontakte
- unabhängige Installation und Sicherung

## Phase 0.6 – Mailcow

- Verbindungstest
- Postfachverwaltung
- Aliasse und Verteiler
- Quotas
- Passwortänderung
- Webmail-Verknüpfung
- unabhängige Installation und Sicherung

## Phase 0.7 – Debian-Betrieb

- systemd-Dienst für das Familienportal
- Betrieb unter eigenem Linux-Systembenutzer
- lokale Bindung hinter Nginx
- produktive Nginx-Beispielkonfiguration
- Debian-Paket
- optional eigener APT-Updatekanal
- Installations- und Einrichtungsassistent
- Systemprüfung vor Installation und Update
- Backup und Wiederherstellung
- Updatekonzept für getrennte Dienste
- Administrations- und Benutzerhandbuch

## Version 1.0

Stabile Debian-Plattform mit Kleinfamilien- und Großfamilienprofil, Modulverwaltung, Supportmodul, Nachrichtenportal, Kleinanzeigen sowie produktionsreifen Nextcloud- und Mailcow-Connectoren. Das Familienportal läuft als eigener Dienst hinter Nginx; Nextcloud und Mailcow bleiben technisch und betrieblich getrennt.
