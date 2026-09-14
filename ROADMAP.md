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
- ICS Export
- ICS Import mit UID-Duplikatschutz
- Nextcloud-CalDAV-Verbindungstest
- Erkennung vorhandener Nextcloud-Kalender über CalDAV
- Migration 0005 für Kalender, Termine und Geburtstage

### Noch nicht Bestandteil von 0.5.0

- vollautomatische bidirektionale CalDAV-Synchronisation
- serverseitige Zustellung von Erinnerungsbenachrichtigungen
- grafische Monats-/Wochenansicht mit Drag-and-drop

Diese Punkte bauen auf der jetzt vorhandenen Kalenderdatenbasis auf und können als 0.5.x-Erweiterungen umgesetzt werden.

## Phase 0.6 – Mailcow

- Verbindungstest
- Postfachverwaltung
- Aliasse und Verteiler
- Quotas
- Passwort-Zurücksetzung per E-Mail vorbereiten
- Webmail-Verknüpfung

## Phase 0.7 – Sicherheit

- TOTP-2FA
- Recovery-Codes
- 2FA-Richtlinien
- Passwort-Zurücksetzung
- Session-Verwaltung
- WebAuthn/Passkeys als Erweiterung

## Phase 0.8 – Gramps Web / Ahnenforschung

- Gramps-Web-Connector
- API- und Healthcheck
- Benutzer-/Rechtezuordnung
- Personen- und Familiensuche
- Geburtstage und Gedenktage
- GEDCOM Import/Export

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
