#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VERSION=${FAMILIENPORTAL_DEB_VERSION:-0.13.0~dev0}
ARCH=${FAMILIENPORTAL_DEB_ARCH:-all}
BUILD_ROOT="$ROOT/build/deb"
PKG_ROOT="$BUILD_ROOT/familienportal_${VERSION}_${ARCH}"
OUT="$ROOT/dist"

command -v dpkg-deb >/dev/null || { echo "dpkg-deb fehlt (Paket dpkg)." >&2; exit 1; }
rm -rf "$PKG_ROOT"
mkdir -p "$PKG_ROOT/DEBIAN" "$PKG_ROOT/opt/familienportal" "$PKG_ROOT/etc/systemd/system" "$PKG_ROOT/usr/local/sbin" "$OUT"

# Application source. Exclude repository/build state and secrets.
tar -C "$ROOT" \
  --exclude=.git --exclude=.venv --exclude=build --exclude=dist \
  --exclude='*.db' --exclude='*.sqlite' --exclude='*.sqlite3' \
  --exclude='.env' --exclude='familienportal.env' \
  -cf - . | tar -C "$PKG_ROOT/opt/familienportal" -xf -

sed "s/^Version:.*/Version: $VERSION/; s/^Architecture:.*/Architecture: $ARCH/" \
  "$ROOT/packaging/debian/control" > "$PKG_ROOT/DEBIAN/control"
for script in postinst prerm postrm; do
  install -m 0755 "$ROOT/packaging/debian/$script" "$PKG_ROOT/DEBIAN/$script"
done

for unit in "$ROOT"/deploy/systemd/*.service "$ROOT"/deploy/systemd/*.timer; do
  install -m 0644 "$unit" "$PKG_ROOT/etc/systemd/system/$(basename "$unit")"
done
install -m 0755 "$ROOT/deploy/familienportalctl" "$PKG_ROOT/usr/local/sbin/familienportalctl"
install -m 0755 "$ROOT/deploy/familienportal-release" "$PKG_ROOT/usr/local/sbin/familienportal-release"

find "$PKG_ROOT" -type d -exec chmod 0755 {} +
dpkg-deb --root-owner-group --build "$PKG_ROOT" "$OUT/familienportal_${VERSION}_${ARCH}.deb"
echo "Erstellt: $OUT/familienportal_${VERSION}_${ARCH}.deb"
