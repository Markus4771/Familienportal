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
- technische Dokumentation der Plattform 0.3

## Phase 0.4 – Nextcloud-Connector

- Verbindung und dienstspezifischer Healthcheck
- sichere Secret-Verwaltung für Zugangsdaten
- Benutzer-/Gruppenzuordnung
- Dateien und Familienordner
- WebDAV
- CalDAV
- CardDAV
- Freigaben

## Phase 0.5 – Kalenderplattform

- persönlicher Kalender
- Familienkalender
- Geburtstagskalender
- Veranstaltungskalender
- wiederkehrende Termine
- Erinnerungen
- Nextcloud-/CalDAV-Anbindung
- ICS Import/Export

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
