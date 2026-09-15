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
- Betrieb hinter vorhandenem Nginx Proxy Manager

## Phase 0.2 – Benutzer und Rechte

- Benutzer und Haushalte
- Anmeldung und Sitzungen
- Rollen und Berechtigungen
- Administration und Auditprotokoll

## 0.3.x – Plattformoberfläche – umgesetzt

- dynamisches Dashboard und Navigation
- Modulrechte, Connector-Manager und Familieneinstellungen

## 0.4.x – Nextcloud – umgesetzt

- Healthcheck, OCS, WebDAV, CalDAV und CardDAV
- Benutzer-/Gruppenzuordnung und Familienordner

## 0.5.x – Kalender – umgesetzt

- persönliche und Familienkalender
- Erinnerungen, ICS und Ansichten
- bidirektionale Nextcloud-CalDAV-Synchronisation
- Konfliktauflösung und automatische Worker

## 0.6.x – Mailcow – umgesetzt

- Domains, Postfächer, Aliase, Quota und Benutzerzuordnung
- Passwort- und Verteilerverwaltung

## 0.7.x – Sicherheit und Betrieb – umgesetzt

- TOTP, Recovery-Codes, Passkeys/WebAuthn
- Login-Schutz, CSRF, Security-Header und rollenbasierte 2FA
- Lifecycle-Manager, Backup, Update und Rollback

### Nächste Ausbaustufe 0.7.4 / Packaging

- natives Debian-`.deb`-Paket
- signierte Release-Artefakte
- Backup-Retention und stable/beta-Kanal

## 0.8.0 – Gramps Web / Ahnenforschung – umgesetzt

- REST-Connector, Rechtezuordnung, Suche und Details
- GEDCOM Import/Export
- Migration 0012

## 0.8.1 – Gramps ↔ Kalender – umgesetzt

- Kalender `Familie & Ahnen`
- automatische Geburtstags-/Gedenktag-Synchronisation

## 0.8.2 – Personendetails und Beziehungen – umgesetzt

- Personendetailseite
- Eltern, Partner und Kinder
- klickbare Beziehungsübersicht

## 0.8.3 – Medien & Dokumente – umgesetzt

- Gramps-Medienreferenzen erkennen und auflösen
- Medien auf Personendetailseite anzeigen
- Originaldateien bleiben in Gramps Web

## 0.8.4 – Externe Familienfotos & Urkunden – umgesetzt

- externe Dokumentreferenzen je Gramps-Person
- Provider `nextcloud` für Familienfotos und Dateien
- Provider `paperless` für Urkunden und archivierte Dokumente vorbereitet
- Titel, Kategorie und externe Referenz werden im Portal gespeichert
- Dateien selbst werden nicht im Familienportal dupliziert
- Schreibzugriff nur mit `genealogy.write` oder Superadmin
- Anzeige gemeinsam mit Gramps-Medien auf der Personendetailseite
- Migration 0013 `genealogy_document_links`
- Alembic-Metadaten um Gramps- und Genealogy-Modelle ergänzt
- Tests für Nextcloud- und Paperless-Referenzen

### Nächste Gramps-Ausbaustufe 0.8.5

- Nextcloud-Picker statt manueller Pfadeingabe
- Paperless-ngx REST-Connector und Dokumentauswahl
- sichere Vorschau/Thumbnail-Auslieferung mit Rechteprüfung
- Links öffnen direkt das externe Dokument
- Datenschutzregeln für lebende Personen verfeinern

## Spätere Plattformausbaustufen

- Event-Bus und Manifest-Discovery
- Entwickler-SDK und App-Center
- Benachrichtigungszentrale
- PWA / Mobile Nutzung

## Version 1.0

Stabile Debian-Plattform mit Kleinfamilien- und Großfamilienprofil, Modulverwaltung, Kalender, Supportmodul, Nachrichtenportal, Kleinanzeigen sowie produktionsreifen Nextcloud- und Mailcow-Connectoren. Externe Dienste bleiben technisch und betrieblich getrennt und werden über standardisierte Connectoren eingebunden.
