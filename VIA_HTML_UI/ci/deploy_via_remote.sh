#!/usr/bin/env bash
# Deploy the complete VIA static package to a remote test server over SSH.
# Required: VIA_REMOTE_HOST
# Optional: VIA_REMOTE_USER, VIA_REMOTE_PORT, VIA_REMOTE_KEY, VIA_REMOTE_PATH,
#           VIA_HEALTH_URL, VIA_KEEP_RELEASES
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
: "${VIA_REMOTE_HOST:?Set VIA_REMOTE_HOST, e.g. test.example.com}"
VIA_REMOTE_USER="${VIA_REMOTE_USER:-$USER}"
VIA_REMOTE_PORT="${VIA_REMOTE_PORT:-22}"
VIA_REMOTE_PATH="${VIA_REMOTE_PATH:-/srv/via}"
VIA_KEEP_RELEASES="${VIA_KEEP_RELEASES:-5}"
if ! [[ "$VIA_KEEP_RELEASES" =~ ^[1-9][0-9]*$ ]]; then
  printf 'VIA_KEEP_RELEASES must be a positive integer\n' >&2
  exit 2
fi
VIA_SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=12 -p "$VIA_REMOTE_PORT")
if [[ -n "${VIA_REMOTE_KEY:-}" ]]; then VIA_SSH_OPTS+=(-i "$VIA_REMOTE_KEY"); fi
REMOTE="${VIA_REMOTE_USER}@${VIA_REMOTE_HOST}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RELEASE="${VIA_REMOTE_PATH%/}/releases/via-${STAMP}"
KEEP_FROM=$((VIA_KEEP_RELEASES + 1))

printf '[VIA deploy] local package: %s\n' "$PACKAGE_ROOT"
printf '[VIA deploy] remote release: %s:%s\n' "$REMOTE" "$RELEASE"

# Connectivity check before any write.
ssh "${VIA_SSH_OPTS[@]}" "$REMOTE" "printf '[remote] connected %s\\n' \"\$(hostname)\""

# Stream the package directly to a timestamped release directory. Existing
# releases are preserved, so rollback is a symlink switch rather than deletion.
tar -C "$PACKAGE_ROOT" --exclude='*.DS_Store' -czf - . \
  | ssh "${VIA_SSH_OPTS[@]}" "$REMOTE" \
    "set -e; mkdir -p '$RELEASE'; tar -xzf - -C '$RELEASE'; ln -sfn '$RELEASE' '${VIA_REMOTE_PATH%/}/current'; printf '[remote] current=%s\\n' \"\$(readlink -f '${VIA_REMOTE_PATH%/}/current')\""

# Verify the deployed entry points and package report remotely.
ssh "${VIA_SSH_OPTS[@]}" "$REMOTE" "set -e; test -s '${VIA_REMOTE_PATH%/}/current/ui/VIA-UI-Standalone-NoServer.html'; test -s '${VIA_REMOTE_PATH%/}/current/ui/VIA-SYNCHRONIZER-Standalone.html'; test -s '${VIA_REMOTE_PATH%/}/current/reports/VIA-CI-Matrix-Report.md'; printf '[remote] entrypoints=ok report=ok\\n'"

# Keep a bounded number of historical releases, never touching current first.
ssh "${VIA_SSH_OPTS[@]}" "$REMOTE" "set -e; cd '${VIA_REMOTE_PATH%/}/releases'; ls -1dt via-* 2>/dev/null | tail -n +$KEEP_FROM | xargs -r rm -rf"

if [[ -n "${VIA_HEALTH_URL:-}" ]]; then
  curl --fail --silent --show-error --max-time 15 "$VIA_HEALTH_URL" >/dev/null
  printf '[VIA deploy] health check: ok (%s)\n' "$VIA_HEALTH_URL"
fi

printf '[VIA deploy] complete: %s\n' "$RELEASE"
