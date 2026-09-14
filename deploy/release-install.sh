#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Bitte als root ausführen." >&2
  exit 1
fi

apt-get update
apt-get install -y curl ca-certificates python3 tar coreutils

REPOSITORY=${FAMILIENPORTAL_GITHUB_REPOSITORY:-Markus4771/Familienportal}
TOKEN=${GITHUB_TOKEN:-${FAMILIENPORTAL_GITHUB_TOKEN:-}}
API="https://api.github.com/repos/${REPOSITORY}/releases/latest"
headers=(-H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28")
[[ -n "$TOKEN" ]] && headers+=(-H "Authorization: Bearer $TOKEN")

json=$(curl --fail --silent --show-error -L "${headers[@]}" "$API")
tag=$(printf '%s' "$json" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tag_name", ""))')
[[ -n "$tag" ]] || { echo "Kein GitHub Release gefunden." >&2; exit 2; }
archive="familienportal-${tag}.tar.gz"
checksum="${archive}.sha256"

get_asset() {
  local name=$1
  printf '%s' "$json" | python3 -c 'import json,sys
name=sys.argv[1]
for asset in json.load(sys.stdin).get("assets", []):
    if asset.get("name") == name:
        print(asset.get("browser_download_url", ""))
        break' "$name"
}

archive_url=$(get_asset "$archive")
checksum_url=$(get_asset "$checksum")
[[ -n "$archive_url" && -n "$checksum_url" ]] || { echo "Release $tag enthält keine Installations-Assets." >&2; exit 2; }

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl --fail --silent --show-error -L "${headers[@]}" -o "$tmp/$archive" "$archive_url"
curl --fail --silent --show-error -L "${headers[@]}" -o "$tmp/$checksum" "$checksum_url"
(cd "$tmp" && sha256sum -c "$checksum")
mkdir -p "$tmp/source"
tar -C "$tmp/source" -xzf "$tmp/$archive"

echo "Familienportal $tag wird installiert."
FAMILIENPORTAL_INSTALL_MODE=${FAMILIENPORTAL_INSTALL_MODE:-test} bash "$tmp/source/deploy/install.sh"
