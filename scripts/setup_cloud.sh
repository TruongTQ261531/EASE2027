#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export UV_CACHE_DIR="${UV_CACHE_DIR:-/workspace/.cache/uv}"
uv --system-certs sync --frozen

# System coturn is preferred. The cloud image has no sudo/package-install helper;
# unpack Debian-signed packages into a user-owned prefix without installing services.
turn_prefix="${EASE_TURN_PREFIX:-/workspace/.local/ease-turn/root}"
if ! command -v turnserver >/dev/null && [[ ! -x "$turn_prefix/usr/bin/turnserver" ]]; then
  if [[ ! -x /usr/bin/apt-get || ! -r /usr/share/keyrings/debian-archive-keyring.pgp ]]; then
    echo 'Install coturn using your OS package manager, then rerun setup.' >&2
    exit 1
  fi
  apt_state="$(mktemp -d /tmp/ease-apt.XXXXXXXX)"
  trap 'rm -rf "$apt_state"' EXIT
  mkdir -p "$apt_state/parts" "$apt_state/lists/partial" "$apt_state/cache/archives/partial"
  mkdir -p "$apt_state/packages" "$turn_prefix"
  cat > "$apt_state/apt.conf" <<EOF
Dir::Etc::parts "$apt_state/parts";
Dir::Etc::main "/dev/null";
Dir::Etc::sourcelist "$apt_state/sources.list";
Dir::Etc::sourceparts "-";
Dir::State::lists "$apt_state/lists";
Dir::Cache "$apt_state/cache";
Dir::Cache::archives "$apt_state/cache/archives";
Acquire::Retries "0";
APT::Update::Error-Mode "any";
EOF
  cat > "$apt_state/sources.list" <<'EOF'
deb [signed-by=/usr/share/keyrings/debian-archive-keyring.pgp] https://deb.debian.org/debian trixie main
EOF
  APT_CONFIG="$apt_state/apt.conf" /usr/bin/apt-get update
  (
    cd "$apt_state/packages"
    APT_CONFIG="$apt_state/apt.conf" /usr/bin/apt-get download \
      coturn=4.6.1-2 libhiredis1.1.0=1.2.0-6+b3 \
      libevent-extra-2.1-7t64=2.1.12-stable-10+b1 \
      libevent-openssl-2.1-7t64=2.1.12-stable-10+b1
    sha256sum ./*.deb > "$turn_prefix/packages.sha256"
    for package in ./*.deb; do dpkg-deb -x "$package" "$turn_prefix"; done
  )
fi
if ! command -v chromium >/dev/null && [[ -z "${EASE_CHROMIUM_EXECUTABLE:-}" ]]; then
  uv run --frozen playwright install chromium
fi
uv run --frozen python - <<'PY'
from ease_rtc.relay import local_turn
with local_turn() as (_, binary_hash):
    print('Local TURN/TCP startup verified; binary SHA256:', binary_hash)
PY
