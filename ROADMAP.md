# Roadmap

## Phase 0.1 – Plattformbasis
- Projekt- und Architekturdokumentation
- FastAPI-Grundanwendung
- Konfiguration, Health-Endpunkt, PostgreSQL/SQLAlchemy
- Profile Kleinfamilie und Großfamilie
- Modul- und Connector-Verträge
- Debian-Zielplattform und externer Nginx Proxy Manager

## 0.2.x – Benutzer und Rechte – umgesetzt
- Benutzer, Familien und Haushalte
- Anmeldung und Sitzungen
- Rollen/Berechtigungen, Administration und Audit

## 0.3.x – Plattformoberfläche – umgesetzt
- dynamisches Dashboard und Navigation
- Modulrechte, Connector-Manager und Familieneinstellungen

## 0.4.x – Nextcloud – umgesetzt
- Healthcheck, OCS, WebDAV, CalDAV und CardDAV
- Benutzer-/Gruppenzuordnung und Familienordner

## 0.5.x – Kalender – umgesetzt
- persönliche und Familienkalender, Erinnerungen, ICS und Ansichten
- bidirektionale Nextcloud-CalDAV-Synchronisation
- Konfliktauflösung und automatische Worker

## 0.6.x – Mailcow – umgesetzt
- Domains, Postfächer, Aliase, Quota und Benutzerzuordnung
- Passwort- und Verteilerverwaltung

## 0.7.x – Sicherheit und Betrieb – umgesetzt
- TOTP, Recovery-Codes, Passkeys/WebAuthn
- Login-Schutz, CSRF, Security-Header und rollenbasierte 2FA
- Lifecycle-Manager, Backup, Update und Rollback

### Noch offen: Packaging
- natives Debian-`.deb`-Paket
- signierte Release-Artefakte
- Backup-Retention und stable/beta-Kanal

## 0.8.x – Gramps Web / Ahnenforschung – umgesetzt
- REST-Connector, Suche, Personendetails und Beziehungen
- GEDCOM Import/Export und Kalender-Synchronisation
- Medien und externe Dokumentreferenzen
- Nextcloud-/Paperless-Dokumentanbindung
- Datenschutzregeln für lebende Personen
- Pagination und API-Hardening

## 0.9.0 – Integration & Administration – in Abschlussphase
- zentrale Integrationsverwaltung
- gemeinsame Statusübersicht für Nextcloud, Mailcow, Gramps Web und Paperless-ngx
- Sammel-Healthcheck
- mehrstufige Diagnose: Konfiguration, Netzwerk, Zugangsdaten und API
- dienstspezifische Healthchecks über die jeweiligen Connector-Clients
- zentrale Systemstatus-Seite für Administratoren
- sichere Admin-Status-API ohne Secrets
- Anzeige von Benutzern, Haushalten, Modulen, Integrationen und Audit-Ereignissen
- direkte Navigation zu Systemstatus und Integrationsverwaltung
- Tests und CI für Integrations- und Administrationsfunktionen

### Vor Freigabe 0.9.0
- Security-/Middleware-Abschlussprüfung
- Integrations-Hardening und Fehlerklassifizierung
- Dokumentation und Changelog vervollständigen
- komplette CI-Suite grün
- reale Debian-Testinstallation vorbereiten

## 0.10.x – Familienalltag
- 0.10.0 Aufgaben
- 0.10.1 Einkaufslisten
- 0.10.2 Notizen
- 0.10.3 Haushalt und wiederkehrende Arbeiten
- 0.10.4 Termine und Erinnerungen
- 0.10.5 Familien-Dashboard
- 0.10.6 Kinderaufgaben / optionale Punkte- und Taschengeldfunktionen
- 0.10.7 Rezepte, Essensplan und Einkaufslisten-Verknüpfung
- 0.10.8 Abstimmungen und Familienorganisation
- 0.10.9 Automatisierungen und externe Ereignisse

## Spätere Plattformausbaustufen
- Event-Bus und Manifest-Discovery
- Entwickler-SDK und App-Center
- Benachrichtigungszentrale
- PWA / Mobile Nutzung
- weitere Connectoren und optionale KI-Funktionen

## Version 1.0
Stabile Debian-Plattform mit Kleinfamilien- und Großfamilienprofil, sicherer Benutzer-/Rechteverwaltung, Familienalltagsmodulen, Kalender, zentraler Administration sowie produktionsreifen Connectoren. Externe Dienste bleiben technisch und betrieblich getrennt und werden über standardisierte Connectoren eingebunden.
