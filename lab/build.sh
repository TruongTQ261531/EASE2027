#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
build_ca="${CODEX_PROXY_CERT:-/etc/ssl/certs/ca-certificates.crt}"
env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH \
  docker --host=unix:///var/run/docker.sock build \
  --secret "id=proxy_ca,src=$build_ca" -f lab/Dockerfile -t ease-rtc-lab:dev .
