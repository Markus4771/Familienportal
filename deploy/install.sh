#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Bitte als root ausführen: sudo bash deploy/install.sh" >&2
  exit 1
fi

SOURCE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
APP_DIR=/opt/familienportal
CONFIG_DIR=/etc/familienportal
DATA_DIR=/var/lib/familienportal
BACKUP_DIR=/var/backups/familienportal
SYSTEMD_DIR=/etc/systemd/system
INSTALL_MODE=${FAMILIENPORTAL_INSTALL_MODE:-test}

if [[ "$INSTALL_MODE" != "test" && "$INSTALL_MODE" != "production" ]]; then
  echo "FAMILIENPORTAL_INSTALL_MODE muss test oder production sein." >&2
  exit 1
fi

apt-get update
apt-get install -y python3 python3-venv python3-pip postgresql-client curl ca-certificates tar

if ! id familienportal >/dev/null 2>&1; then
  useradd --system --home-dir "$DATA_DIR" --create-home --shell /usr/sbin/nologin familienportal
fi

install -d -o familienportal -g familienportal -m 0750 "$APP_DIR" "$CONFIG_DIR" "$DATA_DIR"
install -d -o root -g familienportal -m 0750 "$BACKUP_DIR"
cp -a "$SOURCE_DIR"/. "$APP_DIR"/
rm -rf "$APP_DIR/.git" "$APP_DIR/.venv"
chown -R familienportal:familienportal "$APP_DIR" "$DATA_DIR"

python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
"$APP_DIR/.venv/bin/python" -m pip install "$APP_DIR"

if [[ ! -f "$CONFIG_DIR/familienportal.env" ]]; then
  cp "$APP_DIR/.env.example" "$CONFIG_DIR/familienportal.env"
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

  chmod 0640 "$CONFIG_DIR/familienportal.env"
  chown root:familienportal "$CONFIG_DIR/familienportal.env"
fi

for unit in \
  familienportal.service \
  familienportal-calendar-sync.service \
  familienportal-calendar-sync.timer \
  familienportal-reminder-queue.service \
  familienportal-reminder-queue.timer \
  familienportal-security-cleanup.service \
  familienportal-security-cleanup.timer; do
  install -o root -g root -m 0644 "$APP_DIR/deploy/systemd/$unit" "$SYSTEMD_DIR/$unit"
done

install -o root -g root -m 0755 "$APP_DIR/deploy/familienportalctl" /usr/local/sbin/familienportalctl
install -o root -g root -m 0755 "$APP_DIR/deploy/familienportal-release" /usr/local/sbin/familienportal-release

systemctl daemon-reload
systemctl enable familienportal.service
systemctl enable --now familienportal-calendar-sync.timer
systemctl enable --now familienportal-reminder-queue.timer
systemctl enable --now familienportal-security-cleanup.timer

if [[ "$INSTALL_MODE" == "test" ]]; then
  systemctl enable --now familienportal.service
  sleep 2
  echo
  echo "Testinstallation abgeschlossen."
  systemctl --no-pager --full status familienportal.service || true
  echo
  curl --fail --silent --show-error http://127.0.0.1:8000/health && echo
else
  echo
  echo "Produktionsdateien installiert."
  echo "Vor dem Start $CONFIG_DIR/familienportal.env anpassen: PostgreSQL, Domain, Proxy, SMTP und WebAuthn."
  echo "Danach: systemctl enable --now familienportal.service"
fi

echo "Konfiguration: $CONFIG_DIR/familienportal.env"
echo "Anwendung:     $APP_DIR"
echo "Daten:         $DATA_DIR"
echo "Backups:       $BACKUP_DIR"
echo "Verwaltung:    familienportalctl status"
echo "Updates:       familienportal-release check"
