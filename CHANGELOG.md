# Changelog

Alle wesentlichen Änderungen am Familienportal werden in dieser Datei dokumentiert.

## 0.13.1 – 2026-09-18

### Härtung und Release-Vorbereitung
- First-Run-Setup erzwingt die Passwort-Mindestlänge von 10 Zeichen nun auch serverseitig.
- Leere Pflichtfelder für Familienname, Administratorname und E-Mail werden serverseitig abgewiesen.
- Regressionstests für die Setup-Validierung ergänzt.
- Fehlende `security`-Capability in der System-Capability-API wiederhergestellt.
- Versionsstand in Paketmetadaten und Python-Paket auf 0.13.1 angehoben.

### Noch offen vor Stable
- Automatischen GitHub-Release um Bau und Upload von `familienportal_0.13.1_all.deb` und Prüfsummen erweitern.
- Debian-13-Praxistest mit Paketinstallation, systemd, Setup, Login, Diagnose, Backup/Restore sowie Update/Rollback durchführen.

## 0.13.0 – 2026-09-15

### Produktivbetrieb I
- Debian-13-Installer gehärtet und native Debian-Paketbasis mit systemd-Integration ergänzt.
- First-Run-Setup-Assistent für Familie, Haushalt und ersten Superadministrator hinzugefügt.
- Update-Lifecycle auf Release-`.deb` mit Pflicht-Backup, Alembic-Migration und Readiness-Prüfung ausgerichtet.
- Backup & Restore für Anwendung, Konfiguration, lokale Daten, SQLite und PostgreSQL einschließlich Prüfsummen und Rollback erweitert.
- Geführter Integrations-Assistent für Nextcloud, Mailcow, Paperless-ngx und Gramps Web ergänzt.
- Mobile Navigation, Touch-Bedienung, responsive Karten/Formulare und Dashboard für Smartphones verbessert.
- Navigation und Verwaltungsbereiche vereinheitlicht sowie Schnellaktionen auf dem Dashboard ergänzt.
- Zentrale Systemdiagnose zeigt Version, Umgebung, Datenbank, Migration, Speicherbelegung, Integrationsstatus und Audit-Ereignisse.

### Qualität und Release
- CI prüft Python- und Shell-Syntax, Importintegrität, Regressionstests und die Alembic-Migrationskette bis 0023.
- Upgrade-Baseline von 0.12 auf 0.13 wird über die Migrationskette geprüft.
- Debian-`.deb` wird in CI gebaut und auf Paketinhalt geprüft.
- Secret-Leak-Prüfung verhindert versehentliches Verpacken von `.env`, `familienportal.env` und Git-Metadaten.
- CI #404 für den 0.13-Release-Kandidaten war vollständig erfolgreich.

### Betriebsanforderungen
- Externe Connectoren müssen weiterhin mit den tatsächlich eingesetzten Diensten und Zugangsdaten im Zielsystem getestet werden.
- Vor produktiver Freigabe sollte das Stable-`.deb` zusätzlich auf einer echten Debian-13-Instanz installiert und der Restore-Pfad praktisch geprüft werden.

## 0.12.0 – 2026-09-15

### Familienalltag III
- Dashboard-Integration für Notizen, Listen, offene Listeneinträge, Schnellzugriffe und zuletzt bearbeitete Inhalte erweitert.
- Listenrechte für bestehende Systemrollen ergänzt, ohne benutzerdefinierte Rollen zu überschreiben.
- Lebenszyklus für Notizen und Listen mit Archivieren, Wiederherstellen und kontrolliertem endgültigem Löschen vervollständigt.
- Private Notizen und Listen können gezielt für Familienmitglieder oder Haushalte freigegeben werden; Familiengrenzen werden serverseitig geprüft.
- Aus Notizen und Listen können Aufgaben und Kalenderereignisse erzeugt und als ContentLinks nachvollzogen werden.
- ContentLinks gegen inkonsistente Quelle/Ziel/Typ-Kombinationen und logische Duplikate gehärtet.
- Listeneinträge unterstützen komfortablere Bearbeitung von Menge, Einheit, Kategorie, Verantwortlichem, Fälligkeit, Notiz und Sortierposition.
- Administrative Zugriffe auf private Inhalte werden ohne vertrauliche Titel, Texte oder Listeneinträge auditiert.

### Datenbank und Qualität
- Migration 0021: Listenrechte für bestehende Systemrollen.
- Migration 0022: Freigaben für Notizen und Listen.
- Migration 0023: Content-Link-Hardening und partielle Eindeutigkeitsindizes.
- CI prüft Python-Syntax, Importintegrität, den vollständigen Testlauf und die Migrationskette 0013 bis 0023 einschließlich Downgrade und erneutem Upgrade.
- ContentLink-Validierung bleibt für ältere Strukturprüfungen kompatibel und erzwingt bei explizitem Link-Typ die korrekte Kombination aus Quelle und Ziel.

### Bekannte Betriebsanforderungen
- Externe Connectoren müssen weiterhin mit den tatsächlich eingesetzten Nextcloud-, Mailcow-, Gramps-Web- und Paperless-ngx-Versionen getestet werden.
- Native Debian-`.deb`-Paketierung und weiterer mobiler Bedienkomfort bleiben Plattform-/Folgeausbaupunkte.

## 0.11.0 – 2026-09-15

### Familienalltag II – Notizen und Listen
- Neues Notizsystem für Familien und Haushalte mit privaten Notizen, Eigentümermodell und Archivierung.
- Universelles Listensystem für allgemeine Listen, Einkaufslisten, Packlisten und Wunschlisten.
- Listeneinträge unterstützen Menge, Einheit, Kategorie, Verantwortliche, Fälligkeit, Erledigt-Status und Sortierposition.
- Mobile Web-Oberflächen unter `/notes` und `/lists` zum Anlegen und Bearbeiten von Notizen, Listen und Listeneinträgen.
- Listeneinträge können direkt als erledigt oder offen umgeschaltet werden.

### Verknüpfungen und Dashboard
- Notizen und Listen können technisch mit Aufgaben und Kalenderereignissen verknüpft werden.
- Datenbank-Constraints verhindern Links mit mehreren Quellen oder mehreren Zielen.
- Dashboard-Service liefert sichtbare Notizen, Listen, offene Listeneinträge und zuletzt bearbeitete Notizen.
- System-Capabilities melden `notes` und `lists` als verfügbare Module.

### Rechte, Datenschutz und Audit
- Familiengrenzen und Eigentümerrechte werden serverseitig für Notizen und Listen geprüft.
- Private Notizen und Listen sind standardmäßig nur für Eigentümer sowie ausdrücklich berechtigte Benutzer sichtbar.
- Neue Rechte für Lesen, Erstellen, Bearbeiten, Archivieren, Löschen, Teilen, Zuweisen und Verwalten.
- Bestehende Systemrollen erhalten Notizrechte über Migration 0018, ohne benutzerdefinierte Rollen zu verändern.
- Audit-Einträge für Notizen enthalten weder Titel noch Inhalt; vertraulicher Freitext wird nicht in Audit-Metadaten übernommen.
- Audit-Unterstützung für Listen und Listeneinträge ergänzt.

### Datenbank und Qualität
- Migration 0017: Familiennotizen.
- Migration 0018: Notizrechte für bestehende Systemrollen.
- Migration 0019: Universelle Familienlisten und Listeneinträge.
- Migration 0020: Verknüpfungen zwischen Notizen/Listen und Aufgaben/Kalenderereignissen.
- CI prüft die vollständige Migrationskette 0013 bis 0020 einschließlich Downgrade auf 0016 und anschließendem Upgrade auf Head.
- Zusätzliche Tests für Familiengrenzen, private Inhalte, Listenmodelle, Content-Links, Audit-Datenschutz und Web-Routen.
- Runtime-/Proxy- und Readiness-Kompatibilität aus 0.10.0 bleibt erhalten.

### Bekannte Betriebsanforderungen
- Die Web-Oberflächen sind die erste produktive Ausbaustufe; weiterführende Freigabe-, Sortier- und Komfortfunktionen können in 0.11.x ergänzt werden.
- Externe Connectoren müssen weiterhin mit den tatsächlich eingesetzten Nextcloud-, Mailcow-, Gramps-Web- und Paperless-ngx-Versionen getestet werden.
- Native Debian-`.deb`-Paketierung bleibt ein eigener offener Plattformpunkt.

## 0.10.0 – 2026-09-15

### Familienaufgaben
- Neues Aufgabenmodul für Familien und Haushalte mit Zuweisung, Priorität, Fälligkeit und privaten Aufgaben.
- Ansichten für eigene, Familien-, überfällige, erledigte und archivierte Aufgaben.
- Wiederkehrende Aufgaben täglich, wöchentlich, monatlich und jährlich mit korrekter Behandlung von Monatsenden und Schaltjahren.
- Dashboard-Integration für offene, heutige, kommende und überfällige Aufgaben sowie Schnell-Erledigen.
- Kalenderintegration mit stabilem Aufgaben-UID und standardmäßig 60 Minuten Erinnerung.
- Erledigte, abgebrochene und archivierte Aufgaben deaktivieren den Kalendertermin; Wiederöffnen oder Wiederherstellen aktiviert ihn wieder.

### Rechte, Datenschutz und Administration
- Aufgabenrechte für Administrator, Erwachsene, Kind und Gast.
- Bestehende Systemrollen erhalten fehlende Aufgabenrechte über Migration 0016, ohne benutzerdefinierte Rechte zu überschreiben.
- Zuweisungen sind serverseitig geschützt; Benutzer ohne Zuweisungsrecht können keine fremden Aufgaben übernehmen oder umverteilen.
- Normales Entfernen erfolgt über Archivierung; endgültiges Löschen ist nur für Aufgabenverwaltung bzw. Superadmin möglich und setzt vorherige Archivierung voraus.
- Sichtbarkeit privater Aufgaben und Dashboard-Auswertungen berücksichtigen Familien- und Aufgabenrechte.
- Audit-Einträge vermeiden vertrauliche Titel und Beschreibungen privater Aufgaben.

### Datenintegrität und Qualität
- Aufgabenänderung, Kalender-Synchronisation und Audit-Logging werden atomar in einer Datenbanktransaktion verarbeitet.
- Integrationstests decken Erstellen, Erledigen, Wiederöffnen, Archivieren, Wiederherstellen und wiederkehrende Aufgaben mit Kalenderereignissen ab.
- Web-Regressionstests schützen Setup, Login/Logout, Dashboard, Administration, System-API und Aufgaben-Routen.
- CI prüft zusätzlich Python-Syntax, Importintegrität und die Alembic-Migrationskette einschließlich Upgrade/Downgrade und Upgrade auf Head.
- Historische doppelte Alembic-Revision 0009 wurde durch eine kompatible Reconciliation-Migration bereinigt.

### Migrationen
- 0014: Familienaufgaben.
- 0015: Aufgabenarchivierung.
- 0016: Aufgabenrechte für bestehende Systemrollen.

### Bekannte Betriebsanforderungen
- Externe Connectoren müssen weiterhin mit den tatsächlich eingesetzten Nextcloud-, Mailcow-, Gramps-Web- und Paperless-ngx-Versionen getestet werden.
- Die CI prüft Softwarelogik und Migrationen, ersetzt aber keinen Live-Integrationstest der externen Systeme.
- Native Debian-`.deb`-Paketierung bleibt ein eigener offener Plattformpunkt.

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
