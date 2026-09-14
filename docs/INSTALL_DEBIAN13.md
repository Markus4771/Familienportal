# Installation auf Debian 13

## Status

Familienportal 0.7.1-dev kann als Testinstallation auf einem frischen Debian-13-System installiert werden. Für Produktion müssen Domain, Reverse Proxy, PostgreSQL, SMTP und WebAuthn vor dem ersten Start konfiguriert werden.

Debian verwaltet das System-Python nach PEP 668. Der Installer verwendet deshalb ausschließlich `/opt/familienportal/.venv` und installiert keine Python-Pakete mit `--break-system-packages`.

## Empfohlen: Test-LXC

Voraussetzungen:

- Debian 13
- root/sudo
- systemd
- Netzwerkzugriff für APT und Python-Pakete
- Quellcode des privaten GitHub-Repositories lokal ausgecheckt

Installation aus einem Checkout:

```bash
cd Familienportal
sudo FAMILIENPORTAL_INSTALL_MODE=test bash deploy/install.sh
```

Der Testmodus verwendet SQLite unter `/var/lib/familienportal/familienportal.db`, erzeugt zufällige Session-/MFA-Schlüssel, installiert und startet den systemd-Dienst und prüft anschließend `/health`.

Danach:

```bash
systemctl status familienportal --no-pager
journalctl -u familienportal -n 100 --no-pager
curl http://127.0.0.1:8000/health
```

Browser im lokalen Netz: Vorher `FAMILIENPORTAL_PUBLIC_URL` und `FAMILIENPORTAL_TRUSTED_HOSTS` in `/etc/familienportal/familienportal.env` auf die Test-IP bzw. den Test-Host anpassen und den Dienst neu starten.

## Produktion

```bash
cd Familienportal
sudo FAMILIENPORTAL_INSTALL_MODE=production bash deploy/install.sh
```

Der Produktionsmodus startet den Hauptdienst absichtlich noch nicht. Zuerst `/etc/familienportal/familienportal.env` konfigurieren:

- PostgreSQL-Datenbank
- `PUBLIC_URL`
- `TRUSTED_HOSTS`
- IP des Nginx Proxy Managers in `TRUSTED_PROXIES`
- HTTPS / Secure Cookies
- WebAuthn RP-ID und Origin
- SMTP
- Connector-Secrets

Danach:

```bash
sudo systemctl enable --now familienportal
sudo systemctl status familienportal --no-pager
```

## Private GitHub-Repositories

Das Repository ist derzeit privat. Ein anonymer `wget .../install.sh`-Befehl ist deshalb absichtlich nicht dokumentiert: er würde ohne GitHub-Authentifizierung nicht funktionieren. Für einen echten Ein-Befehl-Installer sollte ein öffentlicher Release-Kanal bzw. ein separates öffentliches Installer-Repository eingerichtet werden, während der Anwendungscode privat bleiben kann.

## Updates

Aus einem neuen Checkout/Release kann `deploy/install.sh` erneut ausgeführt werden. Bestehende `/etc/familienportal/familienportal.env`-Konfigurationen werden nicht überschrieben. Der systemd-Dienst führt beim Start `alembic upgrade head` aus.
