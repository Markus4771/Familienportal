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

## 0.5.2 – Kalenderoberfläche und Konfliktauflösung – umgesetzt

- Monatsansicht
- Wochenansicht
- Tagesansicht
- Kalenderfarben
- Kalenderfilter
- Termine bearbeiten
- Termine zeitlich verschieben
- Termine zwischen Kalendern verschieben
- bestehende Tombstone-Löschlogik weiterverwenden
- grafische Konfliktliste
- Konfliktentscheidung „lokale Version behalten“
- Konfliktentscheidung „Nextcloud übernehmen“
- sicherer Remote-Abgleich über aktuelles ETag vor Konfliktauflösung
- Migration 0007
- Tests für Ansichtsperioden

## 0.5.3 – automatische Synchronisation und Erinnerungen – umgesetzt

- automatische CalDAV-Synchronisation über systemd-Timer
- Reminder-Queue als persistenter Jobstatus
- SMTP-Versand für fällige Erinnerungen
- Retry-Zähler und letzter Zustellversuch
- getrennte One-Shot-Dienste für Synchronisation und Reminder
- Debian-Installer aktiviert die Timer
- Migrationen 0008/0009

## 0.6.0 – Mailcow-Basis – umgesetzt

- API-Key-basierter Connector
- Domains lesen
- Postfächer lesen
- Aliase lesen
- Quota-Summen
- Healthcheck
- Statusseite unter `/platform/mailcow`

## 0.6.1 – Mailcow-Verwaltung – umgesetzt

- Portal-Benutzer einem Mailcow-Postfach zuordnen
- Postfächer über die Mailcow-API anlegen
- Anzeigename, Quota und Aktivstatus ändern
- Alias/Verteiler anlegen
- Alias-Ziel und Aktivstatus ändern
- Verwaltungsoberfläche unter `/platform/mailcow/management`
- SOGo/Webmail-Link
- Startpasswörter werden nicht im Familienportal gespeichert
- Migration 0009 für Mailcow-Zuordnungen und Reminder-Retry-State
- Tests für Mailbox-API-Payloads

## 0.6.2 – Benutzer-, Verteiler- und Passwortverwaltung – umgesetzt

- Administrator kann das Passwort eines Mailcow-Postfachs neu setzen
- neues Passwort wird nicht im Familienportal gespeichert
- Portal-Benutzer/Postfach-Zuordnung kann wieder gelöst werden
- Verteiler mit mehreren Empfängern komfortabel anlegen und bearbeiten
- Empfänger werden aus Komma, Semikolon oder Zeilenumbrüchen normalisiert
- doppelte Empfänger werden entfernt
- Alias/Verteiler aktivieren oder deaktivieren
- Alias/Verteiler aus der GUI löschen
- Capabilities für Passwort-Reset, Alias-Löschen, Verteiler und Unmapping
- keine zusätzliche Datenbankmigration erforderlich

## 0.7.0 – Sicherheitskern – umgesetzt

- TOTP-Zwei-Faktor-Authentifizierung
- verschlüsselte Speicherung der TOTP-Seeds
- einmalige Recovery-Codes mit Hash-Speicherung
- Login mit TOTP oder Recovery-Code
- Web- und REST-Login erzwingen 2FA bei aktiviertem Konto
- optionale Administrator-2FA-Richtlinie
- Passwort-Zurücksetzung per E-Mail
- neutrale Antwort beim Passwort-Reset-Antrag
- gehashte, zeitlich begrenzte Reset-Verifier
- serverseitige, widerrufbare Sitzungen
- Sitzungsübersicht und Abmelden einzelner/aller anderen Sitzungen
- Session-Widerruf bei Passwort-Reset und Kontosperre
- Passkey/WebAuthn-Datenmodell vorbereitet
- Migration 0010

## 0.7.1 – Passkeys, QR, Login-Schutz und 2FA-Notfallreset – umgesetzt

- WebAuthn-/Passkey-Registrierung
- Passkey-Anmeldung über Browser/Plattform-Authenticator
- mehrere Passkeys pro Benutzer verwalten und löschen
- RP-ID und Origin aus PUBLIC_URL ableiten oder explizit konfigurieren
- QR-Code bei der TOTP-Einrichtung
- persistente Login-Rate-Limits
- zeitweise Sperre nach wiederholten Fehlversuchen
- Rate-Limits für Passwort-, MFA-, REST- und Passkey-Anmeldung
- Administrator-Notfallreset für 2FA mit eigenem Passwort und optional eigenem 2FA-Code
- Zielkonto-Sessions werden beim Notfallreset widerrufen
- Migration 0011
- Tests für WebAuthn-Konfiguration und anonymisierte Throttle-Schlüssel

### Nächste Sicherheits-Ausbaustufe 0.7.2

- CSRF-Schutz für alle POST-Formulare und Fetch-Endpunkte
- Content-Security-Policy und weitere Security-Header
- feinere 2FA-Richtlinien pro Rolle
- Bereinigung alter Throttle- und Recovery-Datensätze
- optional passwortloser discoverable Passkey-Login ohne E-Mail-Vorabfrage

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
