# Installation und Updates 0.7.3

## Überblick

0.7.3 führt einen vollständigen Lifecycle für Debian-Installationen ein:

- Erstinstallation
- Versionsanzeige
- manuelles Backup
- Update aus einem Quellverzeichnis
- Release-basierte Updates
- automatisches Backup vor Updates
- automatischer Rollback bei fehlgeschlagenem Healthcheck
- manueller Rollback
- Deinstallation mit oder ohne Datenlöschung
- GitHub-Releases mit SHA256-Prüfsumme

## Erstinstallation aus einem ausgecheckten Repository

Testinstallation:

```bash
sudo FAMILIENPORTAL_INSTALL_MODE=test bash deploy/install.sh
```

Produktionsinstallation:

```bash
sudo FAMILIENPORTAL_INSTALL_MODE=production bash deploy/install.sh
```

Der Installer installiert zusätzlich:

```text
/usr/local/sbin/familienportalctl
/usr/local/sbin/familienportal-release
```

## Verwaltung

Status:

```bash
sudo familienportalctl status
```

Version:

```bash
familienportalctl version
```

Backup:

```bash
sudo familienportalctl backup
```

Backups liegen standardmäßig unter:

```text
/var/backups/familienportal/
```

Ein Backup enthält Anwendung, Konfiguration, Datenverzeichnis und – abhängig vom Backend – ein SQLite-Abbild oder einen PostgreSQL-Custom-Dump.

## Update aus lokalem Quellverzeichnis

```bash
sudo familienportalctl update /pfad/zum/neuen/familienportal
```

Vor dem Update wird automatisch ein Backup erstellt. Danach werden virtuelle Umgebung, systemd-Units und Abhängigkeiten aktualisiert und Alembic-Migrationen ausgeführt. Anschließend startet der Dienst neu und `/health` wird geprüft.

Schlägt der Healthcheck fehl, wird automatisch auf das unmittelbar vorher erzeugte Backup zurückgerollt.

## Rollback

Letztes Backup:

```bash
sudo familienportalctl rollback
```

Bestimmtes Backup:

```bash
sudo familienportalctl rollback 20260914T150000Z
```

Bei PostgreSQL wird der gespeicherte Custom-Dump mit `pg_restore --clean --if-exists` wiederhergestellt. Bei SQLite wird die gesicherte Datenbankdatei zurückkopiert.

## Deinstallation

Nur Anwendung und systemd-Dienste entfernen; Konfiguration, Daten und Backups behalten:

```bash
sudo familienportalctl remove
```

Vollständig entfernen:

```bash
sudo familienportalctl remove --purge
```

`--purge` löscht zusätzlich `/etc/familienportal`, `/var/lib/familienportal`, `/var/backups/familienportal` und den Systembenutzer.

## GitHub Release-Kanal

Tags im Format `v*`, zum Beispiel `v0.7.3`, starten `.github/workflows/release.yml`.

Der Workflow:

1. führt die Test-Suite aus,
2. prüft die Deployment-Skripte,
3. schreibt die stabile Versionsnummer aus dem Git-Tag in das Release-Archiv,
4. erzeugt `familienportal-vX.Y.Z.tar.gz`,
5. erzeugt die SHA256-Datei,
6. erstellt ein GitHub Release und hängt beide Dateien an.

## Release-Version prüfen

```bash
familienportal-release check
```

Für ein privates GitHub-Repository wird ein Token benötigt:

```bash
export GITHUB_TOKEN='...'
familienportal-release check
```

Der Token muss nur Leserechte auf Releases/Repository-Inhalte besitzen.

## Release-Update

```bash
sudo -E familienportal-release update
```

Der Release-Updater lädt Archiv und Prüfsumme, kontrolliert SHA256 und übergibt die geprüfte Quelle an `familienportalctl update`. Dadurch gelten automatisch Backup und Rollback.

## Erstinstallation aus einem Release

`deploy/release-install.sh` kann als Bootstrap verwendet werden. Für private Repositories muss `GITHUB_TOKEN` gesetzt sein.

```bash
sudo -E FAMILIENPORTAL_INSTALL_MODE=test bash deploy/release-install.sh
```

## Release erstellen

Sobald ein Stand freigegeben werden soll:

```bash
git tag v0.7.3
git push origin v0.7.3
```

Der Release-Workflow übernimmt danach Test, Archivierung und Veröffentlichung.

## Sicherheit

- Release-Archive werden vor Installation mit SHA256 geprüft.
- Updates verändern die bestehende `/etc/familienportal/familienportal.env` nicht.
- Vor jeder Aktualisierung wird ein Backup erstellt.
- Secrets werden nicht in Release-Artefakte eingebettet.
- Für private Repositories sollte der GitHub-Token nicht dauerhaft in der Portal-Konfigurationsdatei gespeichert werden. Besser ist eine kurzzeitig gesetzte Umgebungsvariable oder später ein separates Credential-File mit restriktiven Rechten.

## Noch nicht Bestandteil von 0.7.3

Ein natives `.deb`-Paket ist vorbereitet, aber noch nicht Bestandteil des Release-Workflows. Das kann als nächster Packaging-Schritt ergänzt werden, sobald der Release-Lifecycle auf einer Test-LXC erfolgreich geprüft wurde.
