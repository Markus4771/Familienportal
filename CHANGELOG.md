# Changelog

Alle wesentlichen Änderungen am Familienportal werden in dieser Datei dokumentiert.

## 0.9.0 – 2026-09-15

### Integration & Administration
- Zentrale Integrationsverwaltung für Nextcloud, Mailcow, Gramps Web und Paperless-ngx.
- Zentrale Systemstatus-Seite für Administratoren.
- Sichere Admin-Status-API ohne Ausgabe von Zugangsdaten oder Secret-Werten.
- Mehrstufige Connector-Diagnose für Konfiguration, Netzwerk, Secret-Verfügbarkeit und dienstspezifische API.
- Verbesserte Klassifizierung von HTTP-, Netzwerk- und Authentifizierungszuständen.
- Basis-URLs mit eingebetteten Zugangsdaten werden abgewiesen.
- HEAD 405/501 wird korrekt als erreichbarer Dienst behandelt.

### Sicherheit
- Rollenbasierte MFA-Prüfung gegen fehlende Session-Initialisierung gehärtet.
- Nextcloud-DAV-Pfade gegen einfache und mehrfach URL-kodierte Traversal-Versuche gehärtet.
- Genealogische Nextcloud-Dokumente auf konfigurierte Familienordner beschränkt.
- Nextcloud-Dateiauswahl auf Familienordner begrenzt; Navigation außerhalb des freigegebenen Bereichs verhindert.
- Geschützte Dokumente lebender Personen verwenden eine 404-Antwort, um Existenzinformationen nicht offenzulegen.

### Administration und Dokumentation
- Direkte Navigation zu Systemstatus und Integrationsverwaltung.
- Dokumentation `docs/INTEGRATION_ADMIN_0_9_0.md`.
- Roadmap für 0.9.0 und den folgenden 0.10.x-Familienalltag aktualisiert.
- Zusätzliche Regressionstests für MFA-Middleware, Connector-Diagnose, Nextcloud-Pfade und Familienordnergrenzen.

### Bekannte Betriebsanforderungen
- Externe Connectoren müssen vor Produktivbetrieb mit den tatsächlich eingesetzten Nextcloud-, Mailcow-, Gramps-Web- und Paperless-ngx-Versionen getestet werden.
- Die CI prüft die Softwarelogik, ersetzt jedoch keinen Live-Integrationstest.
- Native Debian-`.deb`-Paketierung bleibt ein eigener noch offener Plattformpunkt.

## 0.8.x
- Gramps-Web-Integration, Personensuche, Beziehungen, GEDCOM-Transfer und Kalender-Synchronisation.
- Medien- und Dokumentintegration mit Nextcloud und Paperless-ngx.
- Datenschutzregeln für lebende Personen sowie Gramps-API-Hardening.

## 0.7.x
- TOTP, Recovery-Codes, Passkeys/WebAuthn und Login-Schutz.
- CSRF- und Security-Header-Hardening sowie rollenbasierte 2FA.
- Backup-, Update- und Rollback-Lifecycle.

## 0.6.x
- Mailcow-Integration.

## 0.5.x
- Kalender und Nextcloud-CalDAV-Synchronisation.

## 0.4.x
- Nextcloud-Grundintegration.

## 0.3.x
- Modul-, Connector- und Plattformverwaltung.

## 0.2.x
- Benutzer, Familien, Haushalte, Rollen, Anmeldung und Audit.

## 0.1.x
- Plattformbasis, Deployment und Reverse-Proxy-Unterstützung.
