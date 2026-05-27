#!/usr/bin/env bash
set -euo pipefail

VOICEBOX_URL="${VOICEBOX_URL:-http://127.0.0.1:17493}"
PROFILE_ID=""
TEXT=""
OUTPUT=""
LANGUAGE="zh"
ENGINE="qwen"
MODEL_SIZE="1.7B"
TIMEOUT_SEC="${VOICEBOX_TIMEOUT_SEC:-300}"
SLEEP_SEC="${VOICEBOX_POLL_INTERVAL_SEC:-2}"
SEED=""
INSTRUCT=""
PERSONALITY="false"

usage() {
  cat <<'EOF'
Usage:
  voicebox_tts.sh --profile-id <id> --text <text> --output <wav>

Options:
  --profile-id <id>      Voice profile id (required)
  --text <text>          Text to speak (required)
  --output <path>        Output wav path (required)
  --language <code>      Language, default zh
  --engine <name>        Engine, default qwen
  --model-size <size>    1.7B, 0.6B, 1B, 3B (default 1.7B)
  --seed <n>             Optional seed
  --instruct <text>      Optional instruction prompt
  --personality          Enable personality rewrite
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile-id) PROFILE_ID="${2:-}"; shift 2 ;;
    --text) TEXT="${2:-}"; shift 2 ;;
    --output) OUTPUT="${2:-}"; shift 2 ;;
    --language) LANGUAGE="${2:-}"; shift 2 ;;
    --engine) ENGINE="${2:-}"; shift 2 ;;
    --model-size) MODEL_SIZE="${2:-}"; shift 2 ;;
    --seed) SEED="${2:-}"; shift 2 ;;
    --instruct) INSTRUCT="${2:-}"; shift 2 ;;
    --personality) PERSONALITY="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "${PROFILE_ID}" || -z "${TEXT}" || -z "${OUTPUT}" ]]; then
  usage
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"

PAYLOAD="$(jq -n \
  --arg profile_id "$PROFILE_ID" \
  --arg text "$TEXT" \
  --arg language "$LANGUAGE" \
  --arg engine "$ENGINE" \
  --arg model_size "$MODEL_SIZE" \
  --arg personality "$PERSONALITY" \
  --arg seed "$SEED" \
  --arg instruct "$INSTRUCT" \
  '{
    profile_id: $profile_id,
    text: $text,
    language: $language,
    engine: $engine,
    model_size: $model_size,
    personality: ($personality == "true")
  }
  + (if $seed != "" then {seed: ($seed | tonumber)} else {} end)
  + (if $instruct != "" then {instruct: $instruct} else {} end)')"

RESPONSE="$(curl -sS -X POST "${VOICEBOX_URL}/generate" \
  -H 'Content-Type: application/json' \
  -d "${PAYLOAD}")"

GEN_ID="$(jq -r '.id // empty' <<<"${RESPONSE}")"
if [[ -z "${GEN_ID}" ]]; then
  echo "VoiceBox did not return a generation id" >&2
  echo "${RESPONSE}" >&2
  exit 1
fi

deadline=$((SECONDS + TIMEOUT_SEC))
status=""
while (( SECONDS < deadline )); do
  status_json="$(curl -sS "${VOICEBOX_URL}/history/${GEN_ID}")"
  status="$(jq -r '.status // empty' <<<"${status_json}")"
  if [[ "${status}" == "completed" ]]; then
    break
  fi
  if [[ "${status}" == "failed" ]]; then
    echo "VoiceBox generation failed:" >&2
    echo "${status_json}" >&2
    exit 1
  fi
  sleep "${SLEEP_SEC}"
done

if [[ "${status}" != "completed" ]]; then
  echo "VoiceBox generation timed out after ${TIMEOUT_SEC}s" >&2
  exit 1
fi

curl -sS "${VOICEBOX_URL}/audio/${GEN_ID}" -o "${OUTPUT}"
echo "${OUTPUT}"
