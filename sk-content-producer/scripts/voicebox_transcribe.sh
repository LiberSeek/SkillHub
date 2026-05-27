#!/usr/bin/env bash
set -euo pipefail

VOICEBOX_URL="${VOICEBOX_URL:-http://127.0.0.1:17493}"
INPUT=""

usage() {
  cat <<'EOF'
Usage:
  voicebox_transcribe.sh --input <audio-file>
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input) INPUT="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "${INPUT}" ]]; then
  usage
  exit 1
fi

curl -sS -X POST "${VOICEBOX_URL}/transcribe" \
  -F "file=@${INPUT}" | jq -r '.text'
