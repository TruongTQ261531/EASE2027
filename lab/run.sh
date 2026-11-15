#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/ease-uv-cache}"
protocol="${1:?Usage: bash lab/run.sh protocol.json NEW_OUTPUT_DIR HOST_LABEL}"
output="${2:?Missing output directory}"
host_label="${3:?Use an explicit observed host/runner label}"
if [[ -e "$output" ]]; then
  echo 'Use an output directory that does not already exist.' >&2
  exit 1
fi
docker_cmd=(env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS -u DOCKER_TLS_VERIFY \
  -u DOCKER_CERT_PATH docker --host=unix:///var/run/docker.sock)
code_commit="$(git rev-parse HEAD)"
code_dirty=false
if [[ -n "$(git status --porcelain)" ]]; then code_dirty=true; fi
code_sha="$(uv run --frozen python -c 'from ease_rtc.io import source_provenance; from pathlib import Path; print(source_provenance(Path.cwd())["source_tree_sha256"])')"
container="ease-live-$RANDOM-$$"
network="$container-net"
mkdir -p "$(dirname "$output")"
cleanup() {
  "${docker_cmd[@]}" rm -f "$container" >/dev/null 2>&1 || true
  "${docker_cmd[@]}" network rm "$network" >/dev/null 2>&1 || true
}
trap cleanup EXIT
"${docker_cmd[@]}" network create --internal "$network" >/dev/null
"${docker_cmd[@]}" create --init --name "$container" --network "$network" \
  --cap-add NET_ADMIN --cap-add NET_RAW --cpus=3 --memory=6g --pids-limit=1024 --shm-size=512m \
  -e "EASE_PARENT_NETNS=$(readlink /proc/self/ns/net)" \
  -e EASE_PRIVATE_INTERNAL_NETWORK=1 \
  -e "EASE_HOST_LABEL=$host_label" -e "EASE_CODE_COMMIT=$code_commit" \
  -e "EASE_CODE_DIRTY=$code_dirty" -e "EASE_EXPECTED_SOURCE_SHA256=$code_sha" \
  ease-rtc-lab:dev python -m ease_rtc.live_lab --protocol /protocol.json --output /results >/dev/null
"${docker_cmd[@]}" cp "$protocol" "$container:/protocol.json"
set +e
"${docker_cmd[@]}" start -a "$container"
status=$?
set -e
# Retrieve evidence even when the experiment fails; never turn a failure into success.
"${docker_cmd[@]}" cp "$container:/results" "$output" || status=1
if [[ -d "$output" ]]; then
  "${docker_cmd[@]}" inspect --format '{{json .Image}}' "$container" > "$output/container_image.json"
fi
exit "$status"
