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
SERVICE_FILE=/etc/systemd/system/familienportal.service

apt-get update
apt-get install -y python3 python3-venv python3-pip postgresql-client curl

if ! id familienportal >/dev/null 2>&1; then
  useradd --system --home-dir "$DATA_DIR" --create-home --shell /usr/sbin/nologin familienportal
fi

install -d -o familienportal -g familienportal -m 0750 "$APP_DIR" "$CONFIG_DIR" "$DATA_DIR"
cp -a "$SOURCE_DIR"/. "$APP_DIR"/
rm -rf "$APP_DIR/.git"
chown -R familienportal:familienportal "$APP_DIR" "$DATA_DIR"

python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install "$APP_DIR"

if [[ ! -f "$CONFIG_DIR/familienportal.env" ]]; then
  cp "$APP_DIR/.env.example" "$CONFIG_DIR/familienportal.env"
  SESSION_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
  sed -i "s|CHANGE_ME_WITH_A_LONG_RANDOM_VALUE|${SESSION_SECRET}|" "$CONFIG_DIR/familienportal.env"
  chmod 0640 "$CONFIG_DIR/familienportal.env"
  chown root:familienportal "$CONFIG_DIR/familienportal.env"
  echo "Konfiguration angelegt: $CONFIG_DIR/familienportal.env"
  echo "Bitte Datenbank, Domain und Proxy-IP dort anpassen."
fi

install -o root -g root -m 0644 "$APP_DIR/deploy/systemd/familienportal.service" "$SERVICE_FILE"
systemctl daemon-reload
systemctl enable familienportal.service

echo
echo "Installation abgeschlossen."
echo "1. $CONFIG_DIR/familienportal.env bearbeiten"
echo "2. systemctl start familienportal"
echo "3. curl http://127.0.0.1:8000/health"
