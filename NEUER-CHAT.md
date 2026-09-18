# Familienportal - Übergabe für neuen Chat

Stand: 18.09.2026

## Aktueller Stand

Stable: 0.13.0 - Produktivbetrieb I
In Vorbereitung: 0.13.1 - Härtung und Release-Vorbereitung
Letzter gemergter Fix-Commit auf main: 00e68e071f70996ae07695bfb3e19806901e9b60
PR #3 wurde erfolgreich gemergt.
CI #410 für PR #3: erfolgreich.

Das Familienportal ist eine modulare Plattform für kleine und große Familien. Technik: FastAPI, Jinja2, Bootstrap/HTMX, SQLAlchemy/Alembic, SQLite/PostgreSQL, Debian 13, systemd. Externe Dienste wie Nextcloud, Mailcow, Home Assistant, Paperless und Gramps Web sollen integriert statt ersetzt werden.

## In 0.13.1 bereits umgesetzt

- First-Run-Setup prüft die Passwort-Mindestlänge von 10 Zeichen jetzt auch serverseitig.
- Leere Pflichtfelder im Setup werden serverseitig abgewiesen.
- Regressionstests für die Setup-Validierung sind vorhanden.
- Die fehlende `security`-Capability wurde wieder ergänzt.
- Versionsnummer in Python-Paket und `pyproject.toml` auf 0.13.1 angehoben.
- Changelog für 0.13.1 ergänzt.

## Nächster Schritt

Der GitHub-Release `v0.13.0` enthält weiterhin kein Release-Asset. Der bisherige Workflow erzeugt nur ein Quellarchiv und ruft `packaging/build_deb.sh` nicht auf.

Als Erstes daher `.github/workflows/release.yml` so erweitern, dass beim Tag-Release zusätzlich `familienportal_<version>_all.deb` und SHA256-Prüfsummen erzeugt und an den Release angehängt werden.

Danach 0.13.1 als Release-Kandidat fertigstellen und auf einem frischen Debian 13 praktisch testen: Paketinstallation, systemd, First-Run-Setup, Login, Dashboard, Systemdiagnose, Backup, Restore sowie Update/Rollback.

## Bekannte Nacharbeiten

- Dashboard-Schnellaktionen für Aufgaben prüfen.
- Rechteprüfung der Task- und Kalender-Aktionen kontrollieren.
- Listen-Bearbeiten und Verschieben/Sortieren in der GUI prüfen.
- Timezone-Konvention vereinheitlichen.
- Migration 0023 auf historische Duplikate prüfen.
- zusätzliche Berechtigungs-, Rollback- und Audit-Tests ergänzen.
- mobile Navigation an Rechte und aktive Module koppeln.
- Integrations-URLs sicher validieren und später authentifizierte Connector-Tests ergänzen.
- Release-Updater um sauberen Rollback bei Fehlern erweitern.
- CI-Importprüfung wieder auf alle relevanten Module erweitern.
- echten Upgrade-Test von 0.12.0 auf 0.13.x ergänzen.

## Wichtige Dateien

`PROJECT.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `CHANGELOG.md`, `DEPLOYMENT.md`, `docs/ROADMAP_0_13_0.md`, `src/familienportal/main.py`, `src/familienportal/setup_web.py`, `src/familienportal/admin_status.py`, `src/familienportal/platform_web.py`, `deploy/familienportalctl`, `deploy/familienportal-release`, `packaging/build_deb.sh`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`.

## Anweisung für den neuen Chat

Zuerst diese Datei lesen. Danach immer den aktuellen GitHub-Stand, aktuellen HEAD, CI und Release-Assets prüfen, da das Repository neuer als diese Übergabe sein kann. Bei Abweichungen gilt der neuere verifizierte GitHub-Stand.

Die Entwicklung soll direkt im Repository fortgeführt werden, wenn der Benutzer die Umsetzung bestätigt. Zuerst den Debian-Paket-Releaseweg abschließen, danach den Debian-13-Praxistest. Anschließend die verbleibenden 0.13.1-Nacharbeiten abschließen und eine Roadmap für 0.14.0 erstellen.

Starttext für einen neuen Chat:

`Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Familienportal und führe die Entwicklung ab dem dort dokumentierten Stand weiter.`
