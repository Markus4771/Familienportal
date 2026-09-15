# Familienportal - Übergabe für neuen Chat

Stand: 15.09.2026

## Aktueller Stand

Stable: 0.13.0 - Produktivbetrieb I
Tag: v0.13.0
Stable-Commit: 4c7745f7c965fea8432f55a814ad26fe0230dbde
CI #408: erfolgreich.

Das Familienportal ist eine modulare Plattform für kleine und große Familien. Technik: FastAPI, Jinja2, Bootstrap/HTMX, SQLAlchemy/Alembic, SQLite/PostgreSQL, Debian 13, systemd. Externe Dienste wie Nextcloud, Mailcow, Home Assistant, Paperless und Gramps Web sollen integriert statt ersetzt werden.

## In 0.13.0 umgesetzt

Debian-Installer, Grundlage für Debian-Paket, Browser-Setup-Assistent, Update-System, Backup/Restore, Integrationsassistent, mobile Oberfläche, neues Dashboard, Systemdiagnose und erweiterte CI.

## Nächster Schritt

Der GitHub-Release v0.13.0 ist veröffentlicht. Beim letzten Check enthielt er noch kein Release-Asset. Das vorgesehene Paket `familienportal_0.13.0_all.deb` fehlt noch.

Als Erstes daher `.github/workflows/release.yml` und `packaging/build_deb.sh` prüfen, den automatischen Debian-Paket-Release vervollständigen und das 0.13.0-Paket bereitstellen.

Danach auf einem frischen Debian 13 einen Praxistest durchführen: Paketinstallation, systemd, First-Run-Setup, Login, Dashboard, Systemdiagnose, Backup, Restore sowie Update/Rollback testen.

## Bekannte Nacharbeiten

- `src/familienportal/main.py` auf verlorene Capability-Einträge für Nextcloud, Mailcow, Kalender und Security prüfen.
- Dashboard-Schnellaktionen für Aufgaben prüfen.
- Rechteprüfung der Task- und Kalender-Aktionen kontrollieren.
- Listen-Bearbeiten und Verschieben/Sortieren in der GUI prüfen.
- Timezone-Konvention vereinheitlichen.
- Migration 0023 auf historische Duplikate prüfen.
- zusätzliche Berechtigungs-, Rollback- und Audit-Tests ergänzen.
- mobile Navigation an Rechte und aktive Module koppeln.
- Passwort-Mindestlänge im Setup serverseitig prüfen.
- Integrations-URLs sicher validieren und später authentifizierte Connector-Tests ergänzen.
- Release-Updater um sauberen Rollback bei Fehlern erweitern.
- CI-Importprüfung wieder auf alle relevanten Module erweitern.
- echten Upgrade-Test von 0.12.0 auf 0.13.x ergänzen.

## Wichtige Dateien

`PROJECT.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `CHANGELOG.md`, `DEPLOYMENT.md`, `docs/ROADMAP_0_13_0.md`, `src/familienportal/main.py`, `src/familienportal/setup_web.py`, `src/familienportal/admin_status.py`, `src/familienportal/platform_web.py`, `deploy/familienportalctl`, `deploy/familienportal-release`, `packaging/build_deb.sh`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`.

## Anweisung für den neuen Chat

Zuerst diese Datei lesen. Danach immer den aktuellen GitHub-Stand, aktuellen HEAD, CI und Release-Assets prüfen, da das Repository neuer als diese Übergabe sein kann. Bei Abweichungen gilt der neuere verifizierte GitHub-Stand.

Die Entwicklung soll direkt im Repository fortgeführt werden, wenn der Benutzer die Umsetzung bestätigt. Zuerst den fehlenden Debian-Paket-Releaseweg abschließen, danach den Debian-13-Praxistest. Anschließend eine Roadmap für 0.14.0 erstellen.

Starttext für einen neuen Chat:

`Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Familienportal und führe die Entwicklung ab dem dort dokumentierten Stand weiter.`