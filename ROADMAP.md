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
- getrennte Dienste für Familienportal, Nextcloud und Mailcow

## Phase 0.2 – Benutzer und Rechte

- Benutzer und Haushalte
- Anmeldung und Sitzungen
- Rollen und Berechtigungen
- Administration
- Auditprotokoll
- Dashboard-Grundlage

## 0.3.1 – Dynamische Plattformoberfläche – umgesetzt

- dynamisches Dashboard aus aktivierten Modulen
- dynamische Navigation
- Modulstatus je Familie
- Berechtigungsprüfung für Navigation und direkten Modulzugriff
- Connectorstatus im Dashboard
- generischer Moduleinstieg

## 0.3.2 – Rollen und Modulrechte – umgesetzt

- zentrale Modulrechte
- Namespace-Wildcards
- mehrere Rollen pro Benutzer
- Rollenverwaltung
- Modulrechte in der Verwaltung sichtbar
- Audit für Rechte- und Rollenanpassungen

## 0.3.3 – Connector-Manager und Einstellungen – umgesetzt

- Connectoren aktivieren/deaktivieren
- Basis-URLs je Familie
- manueller HTTP/HTTPS-Healthcheck
- Status und Fehlermeldung im Dashboard
- Portalname, Sprache und Zeitzone
- Profil Kleinfamilie/Großfamilie konfigurierbar

## 0.4.0 – Nextcloud-Basis – umgesetzt

- Nextcloud-spezifischer Healthcheck
- Secret-Referenz über Umgebungsvariable
- OCS-Benutzer und Gruppen lesen
- Freigaben lesen
- WebDAV-Dateiliste
- CalDAV-/CardDAV-Endpunkte

## 0.4.1 – Nextcloud-Verwaltung – umgesetzt

- Benutzer des Familienportals Nextcloud-Benutzern zuordnen
- Nextcloud-Gruppen Familie oder Haushalten zuordnen
- Familienordner per WebDAV anlegen und registrieren
- DAV-Diagnose
- eigene Verwaltungsoberfläche
- Audit für Zuordnungen und Ordneranlage
- Migration 0004 für Nextcloud-Zuordnungen

## 0.5.0 – Kalenderplattform – umgesetzt

- persönlicher Kalender je Benutzer
- Familienkalender
- Geburtstags-, Jahrestags- und Gedenktagsverwaltung
- Veranstaltungskalender
- zusätzliche Kalender für Schule, Arbeit und Verein
- Termine mit Beschreibung, Ort und Kategorie
- wiederkehrende Termine über RRULE
- Erinnerungsminuten und ICS-VALARM
- ICS Export und Import
- Nextcloud-CalDAV-Verbindungstest und Kalendererkennung
- Migration 0005

## 0.5.1 – Nextcloud-CalDAV-Synchronisation – umgesetzt

- lokale Kalender mit Nextcloud-Kalendern verknüpfen
- CalDAV REPORT zum Lesen von VEVENTs
- neue Remote-Termine lokal anlegen
- neue lokale Termine per PUT nach Nextcloud übertragen
- Remote-Änderungen anhand ETag erkennen
- lokale Änderungen anhand Zeitstempel erkennen
- Konfliktschutz bei gleichzeitigen Änderungen
- Sync-Token je Kalender speichern
- Remote-Löschungen erkennen
- lokale Löschungen über Tombstones nach Nextcloud übertragen
- bedingte PUT/DELETE-Aufrufe mit ETag
- API für Bindings, Konflikte und manuellen Sync
- Migration 0006

## 0.5.2 – Nextcloud-CalDAV-Oberfläche – umgesetzt

- Monats-, Wochen- und Tagesansicht
- Kalenderfarben und Filter
- Termine bearbeiten und verschieben
- grafische Konfliktauflösung
- Migration 0007

## 0.5.3 – automatische Synchronisation und Erinnerungen – umgesetzt

- automatische CalDAV-Synchronisation über systemd-Timer
- Reminder-Queue als persistenter Jobstatus
- SMTP-Versand und Retry
- Migrationen 0008/0009

## 0.6.x – Mailcow – umgesetzt

- API-Key-Connector, Domains, Postfächer, Aliase und Quota
- Benutzer-/Postfach-Zuordnung
- Passwortverwaltung und Verteiler
- Verwaltungsoberfläche und Healthcheck

## 0.7.x – Sicherheit und Betrieb – umgesetzt

- TOTP, Recovery-Codes und Passkeys/WebAuthn
- Login-Rate-Limits und Administrator-2FA-Notfallreset
- CSRF-/Same-Origin-Schutz und Security-Header
- rollenbasierte 2FA-Pflicht
- Security-Cleanup
- Lifecycle-Manager, Backup, Update und Rollback
- GitHub-Release-Workflow und SHA256-Prüfung

### Nächste Ausbaustufe 0.7.4 / Packaging

- natives Debian-`.deb`-Paket
- optional signierte Release-Artefakte
- Backup-Retention und automatische Rotation
- Update-Kanal stable/beta
- CSP ohne `unsafe-inline`

## 0.8.0 – Gramps Web / Ahnenforschung – umgesetzt

- Gramps-Web-Connector über REST-API
- Token über Secret-Referenz
- Benutzer-/Rechtezuordnung
- Personen-/Familiensuche und Details
- Geburtstage/Gedenktage
- GEDCOM Import/Export
- Migration 0012

## 0.8.1 – Gramps ↔ Kalender – umgesetzt

- Kalender `Familie & Ahnen`
- automatische Geburtstags-/Gedenktag-Synchronisation
- idempotentes Mapping und 30-Minuten-Timer
- keine zusätzliche Migration

## 0.8.2 – Personendetails und Beziehungen – umgesetzt

- Personendetailseite
- Eltern, Partner und Kinder
- klickbare Beziehungen und kompakte Stammbaumübersicht
- direkter Gramps-Web-Link
- keine zusätzliche Migration

## 0.8.3 – Medien & Dokumente – umgesetzt

- Medienreferenzen einer Gramps-Person erkennen und normalisieren
- Gramps-Medienobjekte über die REST-API auflösen
- Medien und Dokumente direkt auf der Personendetailseite anzeigen
- Titel, MIME-Typ, Beschreibung und Quellpfad darstellen
- direkter Sprung zum Originalobjekt in Gramps Web
- Originaldateien werden nicht im Familienportal dupliziert
- Tests für verschiedene Medienreferenz-Formate und Normalisierung
- keine zusätzliche Datenbankmigration erforderlich

### Nächste Gramps-Ausbaustufe 0.8.4

- Nextcloud-Verknüpfung für Familienfotos und Urkunden
- optional Paperless-ngx für Dokumente
- Vorschau/Thumbnail-Proxy mit Rechteprüfung
- Datenschutzregeln für lebende Personen weiter verfeinern
- optional OIDC/SSO mit Gramps Web

## Spätere Plattformausbaustufen

- Event-Bus für lose Modulkopplung
- Manifest-Discovery für externe Module
- Modulabhängigkeiten und Kompatibilitätsprüfung
- Entwickler-SDK und Beispielmodule
- App-Center / Modul-Store
- Benachrichtigungszentrale
- PWA / Mobile Nutzung

## Version 1.0

Stabile Debian-Plattform mit Kleinfamilien- und Großfamilienprofil, Modulverwaltung, Kalender, Supportmodul, Nachrichtenportal, Kleinanzeigen sowie produktionsreifen Nextcloud- und Mailcow-Connectoren. Externe Dienste bleiben technisch und betrieblich getrennt und werden über standardisierte Connectoren eingebunden.
