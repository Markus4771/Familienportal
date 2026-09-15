#!/usr/bin/env bash
set -Eeuo pipefail

log(){ printf '[familienportal] %s\n' "$*"; }
die(){ printf '[familienportal] FEHLER: %s\n' "$*" >&2; exit 1; }
trap 'die "Installation in Zeile $LINENO abgebrochen."' ERR

[[ ${EUID} -eq 0 ]] || die "Bitte als root ausführen: sudo bash deploy/install.sh"

SOURCE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
APP_DIR=/opt/familienportal
CONFIG_DIR=/etc/familienportal
DATA_DIR=/var/lib/familienportal
BACKUP_DIR=/var/backups/familienportal
SYSTEMD_DIR=/etc/systemd/system
INSTALL_MODE=${FAMILIENPORTAL_INSTALL_MODE:-test}

[[ "$INSTALL_MODE" == "test" || "$INSTALL_MODE" == "production" ]] || die "FAMILIENPORTAL_INSTALL_MODE muss test oder production sein."
[[ -r /etc/os-release ]] || die "/etc/os-release fehlt."
. /etc/os-release
[[ "${ID:-}" == "debian" ]] || die "Unterstützte Zielplattform ist Debian 13."
[[ "${VERSION_ID:-}" == "13" ]] || die "Debian 13 erforderlich; erkannt: ${PRETTY_NAME:-unbekannt}."
command -v systemctl >/dev/null || die "systemd/systemctl fehlt."

log "Installiere Systemabhängigkeiten."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3 python3-venv python3-pip postgresql-client curl ca-certificates tar
python3 -c 'import sys; assert sys.version_info >= (3,12)' || die "Python >= 3.12 erforderlich."

if ! id familienportal >/dev/null 2>&1; then
  useradd --system --home-dir "$DATA_DIR" --create-home --shell /usr/sbin/nologin familienportal
fi

install -d -o familienportal -g familienportal -m 0750 "$APP_DIR" "$DATA_DIR"
install -d -o root -g familienportal -m 0750 "$CONFIG_DIR" "$BACKUP_DIR"

log "Installiere Anwendung nach $APP_DIR."
find "$APP_DIR" -mindepth 1 -maxdepth 1 ! -name '.venv' -exec rm -rf -- {} +
cp -a "$SOURCE_DIR"/. "$APP_DIR"/
rm -rf "$APP_DIR/.git" "$APP_DIR/.venv"
chown -R familienportal:familienportal "$APP_DIR" "$DATA_DIR"

python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
"$APP_DIR/.venv/bin/python" -m pip install "$APP_DIR"
chown -R familienportal:familienportal "$APP_DIR/.venv"

if [[ ! -f "$CONFIG_DIR/familienportal.env" ]]; then
  install -o root -g familienportal -m 0640 "$APP_DIR/.env.example" "$CONFIG_DIR/familienportal.env"
  SESSION_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
  SECURITY_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
  sed -i "s|CHANGE_ME_WITH_A_LONG_RANDOM_VALUE|${SESSION_SECRET}|" "$CONFIG_DIR/familienportal.env"
  sed -i "s|CHANGE_ME_WITH_ANOTHER_LONG_RANDOM_VALUE|${SECURITY_SECRET}|" "$CONFIG_DIR/familienportal.env"

  if [[ "$INSTALL_MODE" == "test" ]]; then
    sed -i 's|^FAMILIENPORTAL_ENVIRONMENT=.*|FAMILIENPORTAL_ENVIRONMENT=development|' "$CONFIG_DIR/familienportal.env"
    sed -i 's|^FAMILIENPORTAL_DATABASE_URL=.*|FAMILIENPORTAL_DATABASE_URL=sqlite:////var/lib/familienportal/familienportal.db|' "$CONFIG_DIR/familienportal.env"
    sed -i 's|^FAMILIENPORTAL_PUBLIC_URL=.*|FAMILIENPORTAL_PUBLIC_URL=http://127.0.0.1:8000|' "$CONFIG_DIR/familienportal.env"
    sed -i 's|^FAMILIENPORTAL_TRUSTED_HOSTS=.*|FAMILIENPORTAL_TRUSTED_HOSTS=localhost,127.0.0.1,testserver|' "$CONFIG_DIR/familienportal.env"
    sed -i 's|^FAMILIENPORTAL_TRUSTED_PROXIES=.*|FAMILIENPORTAL_TRUSTED_PROXIES=127.0.0.1|' "$CONFIG_DIR/familienportal.env"
    sed -i 's|^FAMILIENPORTAL_SECURE_COOKIES=.*|FAMILIENPORTAL_SECURE_COOKIES=false|' "$CONFIG_DIR/familienportal.env"
    sed -i 's|^FAMILIENPORTAL_WEBAUTHN_RP_ID=.*|FAMILIENPORTAL_WEBAUTHN_RP_ID=localhost|' "$CONFIG_DIR/familienportal.env"
    sed -i 's|^FAMILIENPORTAL_WEBAUTHN_ORIGIN=.*|FAMILIENPORTAL_WEBAUTHN_ORIGIN=http://localhost:8000|' "$CONFIG_DIR/familienportal.env"
  fi
fi
chmod 0640 "$CONFIG_DIR/familienportal.env"
chown root:familienportal "$CONFIG_DIR/familienportal.env"

for unit in \
  familienportal.service \
  familienportal-calendar-sync.service familienportal-calendar-sync.timer \
  familienportal-gramps-calendar-sync.service familienportal-gramps-calendar-sync.timer \
  familienportal-reminder-queue.service familienportal-reminder-queue.timer \
  familienportal-security-cleanup.service familienportal-security-cleanup.timer; do
  install -o root -g root -m 0644 "$APP_DIR/deploy/systemd/$unit" "$SYSTEMD_DIR/$unit"
done
install -o root -g root -m 0755 "$APP_DIR/deploy/familienportalctl" /usr/local/sbin/familienportalctl
install -o root -g root -m 0755 "$APP_DIR/deploy/familienportal-release" /usr/local/sbin/familienportal-release

systemctl daemon-reload
systemctl enable familienportal.service
for timer in familienportal-calendar-sync.timer familienportal-gramps-calendar-sync.timer familienportal-reminder-queue.timer familienportal-security-cleanup.timer; do
  systemctl enable --now "$timer"
done

if [[ "$INSTALL_MODE" == "test" ]]; then
  systemctl enable --now familienportal.service
  for _ in {1..15}; do
    if curl --fail --silent --show-error http://127.0.0.1:8000/health >/dev/null; then
      log "Healthcheck erfolgreich."
      break
    fi
    sleep 1
  done
  curl --fail --silent --show-error http://127.0.0.1:8000/health || die "Healthcheck fehlgeschlagen."
  echo
else
  log "Produktionsdateien installiert. Vor dem Start Konfiguration für PostgreSQL, Domain, Proxy, SMTP und WebAuthn prüfen."
  log "Danach: systemctl enable --now familienportal.service"
fi

log "Installation abgeschlossen."
echo "Konfiguration: $CONFIG_DIR/familienportal.env"
echo "Anwendung:     $APP_DIR"
echo "Daten:         $DATA_DIR"
echo "Backups:       $BACKUP_DIR"
echo "Verwaltung:    familienportalctl status"
echo "Updates:       familienportal-release check"
