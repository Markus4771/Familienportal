# Debian-Installation und Paketierung – 0.13

## Ziel

Familienportal 0.13 unterstützt Debian 13 als primäre native Plattform. Die Anwendung läuft unter einem eigenen Systembenutzer und systemd. Ein externer Reverse Proxy wie Nginx Proxy Manager kann TLS und öffentliche Erreichbarkeit übernehmen.

## Installer aus dem Repository

Testinstallation:

```bash
sudo FAMILIENPORTAL_INSTALL_MODE=test bash deploy/install.sh
```

Produktionsinstallation:

```bash
sudo FAMILIENPORTAL_INSTALL_MODE=production bash deploy/install.sh
```

Im Produktionsmodus wird der Dienst nicht automatisch gestartet, bevor `/etc/familienportal/familienportal.env` für PostgreSQL, Domain, Proxy, SMTP und WebAuthn geprüft wurde.

## Debian-Paket bauen

Auf Debian 13:

```bash
chmod +x packaging/build_deb.sh
./packaging/build_deb.sh
```

Ausgabe:

```text
dist/familienportal_0.13.0~dev0_all.deb
```

Eine abweichende Paketversion kann gesetzt werden:

```bash
FAMILIENPORTAL_DEB_VERSION=0.13.0 ./packaging/build_deb.sh
```

## Installation

```bash
sudo apt install ./dist/familienportal_0.13.0~dev0_all.deb
```

Danach Konfiguration prüfen:

```bash
sudo editor /etc/familienportal/familienportal.env
sudo systemctl enable --now familienportal.service
familienportalctl status
```

## Verzeichnisse

- `/opt/familienportal`: Anwendung und Python-Umgebung
- `/etc/familienportal`: Konfiguration
- `/var/lib/familienportal`: persistente Daten
- `/var/backups/familienportal`: Backups
- `/etc/systemd/system`: systemd Units

## Upgrade- und Entfernungsverhalten

Das Paket erhält bestehende Konfiguration und persistente Daten. Bei normalem Entfernen werden `/etc/familienportal`, `/var/lib/familienportal` und `/var/backups/familienportal` absichtlich nicht gelöscht. Der sichere Upgrade-Pfad mit automatischem Backup und Alembic-Migration wird in Roadmap-Punkt 5 weiter ausgebaut.

## Sicherheit

Der Build schließt `.git`, virtuelle Umgebungen, lokale Datenbanken sowie `.env`/`familienportal.env` aus. Secrets dürfen niemals Bestandteil des `.deb`-Artefakts sein.
