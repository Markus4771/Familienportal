# Familienportal 0.13.0 – Produktivbetrieb I

Status: Entwicklung (`0.13.0-dev`)

## Ziel

0.13.0 führt das Familienportal stärker in Richtung produktiver Eigenbetrieb. Schwerpunkte sind eine reproduzierbare Debian-Installation, ein natives `.deb`-Paket, sichere Updates und Backups, komfortablere Integrationen sowie eine bessere mobile Bedienung.

## Umsetzung

1. [x] Entwicklungsstand auf `0.13.0-dev` setzen und Roadmap dokumentieren.
2. [x] Debian-Installer für Debian 13 härten: Voraussetzungen, Systembenutzer, Verzeichnisse, Python-Umgebung, systemd-Dienste, Test-/Produktionsmodus und Gesundheitsprüfung.
3. [x] Native `.deb`-Paketbasis ergänzen: Debian-Metadaten, Build-Skript, Installations-/Upgrade-Skripte und systemd-Integration.
4. [ ] Browserbasierter Setup-Assistent für Familie, Administrator, Datenbank, Basis-URL und Grundkonfiguration.
5. [ ] Update-System mit Versionsprüfung, Backup vor Update, Paketaktualisierung, Alembic-Migration und Integritätsprüfung.
6. [ ] Backup & Restore für Datenbank, Konfiguration und lokale Daten vervollständigen.
7. [ ] Integrations-Assistent für Nextcloud, Mailcow, Paperless-ngx und Gramps Web mit Verbindungstest.
8. [ ] Mobile Oberfläche für Dashboard, Aufgaben, Listen, Notizen und Kalender weiter optimieren.
9. [ ] Navigation und Startseite vereinheitlichen; Schnellaktionen und personalisierbares Familien-Dashboard ausbauen.
10. [ ] Zentrale Systemdiagnose für Dienste, Datenbank, Speicher, Connectoren, Migrationen und Version.
11. [ ] Security-, Installer-, Update-, Backup- und Regressionstests; Upgrade-Pfad `0.12.0 -> 0.13.0` in CI prüfen.
12. [ ] Stable Release `0.13.0` nach vollständigem grünen CI und Upgrade-Test veröffentlichen.

## Zielplattform

- Debian 13
- systemd
- Python 3.12+
- SQLite für Test/kleine Installation, PostgreSQL für Produktion
- externer Reverse Proxy, insbesondere Nginx Proxy Manager
- Anwendung unter `/opt/familienportal`
- Konfiguration unter `/etc/familienportal`
- persistente Daten unter `/var/lib/familienportal`
- Backups unter `/var/backups/familienportal`

## Paketierung

Das native Debian-Paket wird im Repository aus `packaging/debian/` erzeugt. Der Build muss ohne Git-Metadaten reproduzierbar sein und darf keine Secrets in das Paket aufnehmen. Konfigurationsdateien werden bei Installation erzeugt bzw. als bestehende Konfiguration erhalten.
