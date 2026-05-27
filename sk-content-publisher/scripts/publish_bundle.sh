#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLHUB_ROOT="$(cd "${ROOT_DIR}/../../.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
fi

ACCOUNT_NAME="${ACCOUNT_NAME:-studio-main}"
DEFAULT_SAU_ROOT="${SKILLHUB_ROOT}/vendors/mirrors/social-auto-upload"
if [[ ! -d "${DEFAULT_SAU_ROOT}" ]]; then
  DEFAULT_SAU_ROOT="${ROOT_DIR}/tools/social-auto-upload"
fi
SAU_ROOT="${SAU_ROOT:-${DEFAULT_SAU_ROOT}}"
SAU_PYTHON="${SAU_ROOT}/.venv/bin/python"
SAU_ENTRY="${SAU_ROOT}/sau_cli.py"
DEFAULT_PLATFORMS="xiaohongshu,douyin,kuaishou,x,bilibili"
PLATFORMS_CSV="${DEFAULT_PLATFORMS}"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--platforms xiaohongshu,douyin,kuaishou,x,bilibili] <bundle_dir>
EOF
}

BUNDLE_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platforms)
      if [[ $# -lt 2 ]]; then
        echo "--platforms requires a comma-separated value"
        exit 1
      fi
      PLATFORMS_CSV="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
    *)
      if [[ -n "${BUNDLE_DIR}" ]]; then
        echo "Bundle directory already provided: ${BUNDLE_DIR}"
        usage
        exit 1
      fi
      BUNDLE_DIR="$1"
      shift
      ;;
  esac
done

if [[ -z "${BUNDLE_DIR}" ]]; then
  usage
  exit 1
fi

if [[ ! -d "${BUNDLE_DIR}" ]]; then
  echo "Bundle directory not found: ${BUNDLE_DIR}"
  exit 1
fi

TITLE_FILE="${BUNDLE_DIR}/title.txt"
NOTE_FILE="${BUNDLE_DIR}/note.txt"
TWITTER_FILE="${BUNDLE_DIR}/twitter.txt"
TWITTER_ARTICLE_FILE="${BUNDLE_DIR}/twitter-article.md"
BILIBILI_FILE="${BUNDLE_DIR}/bilibili.txt"
IMAGES_DIR="${BUNDLE_DIR}/images"
DEFAULT_X_POST_TO_X_DIR="${SKILLHUB_ROOT}/vendors/mirrors/baoyu-skills/skills/baoyu-post-to-x"
if [[ ! -d "${DEFAULT_X_POST_TO_X_DIR}" ]]; then
  DEFAULT_X_POST_TO_X_DIR="${HOME}/.codex/skills/baoyu-post-to-x"
fi
X_POST_TO_X_DIR="${X_POST_TO_X_DIR:-${DEFAULT_X_POST_TO_X_DIR}}"
DOUYIN_MANUAL_FINALIZE="${DOUYIN_MANUAL_FINALIZE:-1}"

IFS=',' read -r -a RAW_PLATFORMS <<< "${PLATFORMS_CSV}"
SELECTED_PLATFORMS=()

for raw_platform in "${RAW_PLATFORMS[@]}"; do
  platform="$(echo "${raw_platform}" | xargs)"
  if [[ -z "${platform}" ]]; then
    continue
  fi
  case "${platform}" in
    xiaohongshu|douyin|kuaishou|x|bilibili)
      SELECTED_PLATFORMS+=("${platform}")
      ;;
    *)
      echo "Unsupported platform: ${platform}"
      exit 1
      ;;
  esac
done

if [[ ${#SELECTED_PLATFORMS[@]} -eq 0 ]]; then
  echo "No valid platforms selected"
  exit 1
fi

has_platform() {
  local needle="$1"
  local item
  for item in "${SELECTED_PLATFORMS[@]}"; do
    if [[ "${item}" == "${needle}" ]]; then
      return 0
    fi
  done
  return 1
}

require_path() {
  local required="$1"
  if [[ ! -e "${required}" ]]; then
    echo "Missing required bundle item: ${required}"
    exit 1
  fi
}

if has_platform "xiaohongshu" || has_platform "douyin" || has_platform "kuaishou"; then
  require_path "${TITLE_FILE}"
  require_path "${NOTE_FILE}"
  require_path "${IMAGES_DIR}"
fi

if has_platform "bilibili"; then
  require_path "${BILIBILI_FILE}"
fi

if has_platform "x" && [[ ! -f "${TWITTER_ARTICLE_FILE}" && ! -f "${TWITTER_FILE}" ]]; then
  echo "Missing X bundle item: provide either ${TWITTER_ARTICLE_FILE} or ${TWITTER_FILE}"
  exit 1
fi

IMAGE_FILES=()
if [[ -d "${IMAGES_DIR}" ]]; then
  while IFS= read -r image; do
    IMAGE_FILES+=("${image}")
  done < <(find "${IMAGES_DIR}" -maxdepth 1 -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.webp' \) | sort)
fi

if (( ${#IMAGE_FILES[@]} == 0 )) && (has_platform "xiaohongshu" || has_platform "douyin" || has_platform "kuaishou"); then
  echo "No images found in ${IMAGES_DIR}"
  exit 1
fi

TITLE=""
NOTE=""
BILIBILI_TEXT=""
if [[ -f "${TITLE_FILE}" ]]; then
  TITLE="$(cat "${TITLE_FILE}")"
fi
if [[ -f "${NOTE_FILE}" ]]; then
  NOTE="$(cat "${NOTE_FILE}")"
fi
if [[ -f "${BILIBILI_FILE}" ]]; then
  BILIBILI_TEXT="$(cat "${BILIBILI_FILE}")"
fi
TWITTER_ARGS=()
TWITTER_MODE="legacy-post"

for image in "${IMAGE_FILES[@]}"; do
  TWITTER_ARGS+=(-i "${image}")
done

if [[ -f "${TWITTER_ARTICLE_FILE}" ]]; then
  TWITTER_MODE="article"
else
  TWITTER_TEXT="$(cat "${TWITTER_FILE}")"
fi

if [[ "${TWITTER_MODE}" == "article" ]]; then
  if [[ ! -d "${X_POST_TO_X_DIR}" ]]; then
    echo "X article skill directory not found: ${X_POST_TO_X_DIR}"
    exit 1
  fi
  if command -v bun >/dev/null 2>&1; then
    BUN_X=(bun)
  elif command -v npx >/dev/null 2>&1; then
    BUN_X=(npx -y bun)
  else
    echo "bun or npx is required for X Article publishing"
    exit 1
  fi
fi

echo "Publishing bundle: ${BUNDLE_DIR}"
echo "Using account: ${ACCOUNT_NAME}"
echo "Platforms: ${SELECTED_PLATFORMS[*]}"
echo "Images: ${#IMAGE_FILES[@]}"
if has_platform "x"; then
  echo "X mode: ${TWITTER_MODE}"
fi
echo

if has_platform "xiaohongshu" || has_platform "douyin" || has_platform "kuaishou"; then
  (
    cd "${SAU_ROOT}"
    if has_platform "xiaohongshu"; then
      "${SAU_PYTHON}" "${SAU_ENTRY}" xiaohongshu upload-note \
        --account "${ACCOUNT_NAME}" \
        --images "${IMAGE_FILES[@]}" \
        --title "${TITLE}" \
        --note "${NOTE}"
    fi

    if has_platform "douyin"; then
      DOUYIN_ARGS=()
      if [[ "${DOUYIN_MANUAL_FINALIZE}" == "1" ]]; then
        DOUYIN_ARGS+=(--manual-finalize)
      fi
      "${SAU_PYTHON}" "${SAU_ENTRY}" douyin upload-note \
        --account "${ACCOUNT_NAME}" \
        --images "${IMAGE_FILES[@]}" \
        --title "${TITLE}" \
        --note "${NOTE}" \
        "${DOUYIN_ARGS[@]}"
    fi

    if has_platform "kuaishou"; then
      "${SAU_PYTHON}" "${SAU_ENTRY}" kuaishou upload-note \
        --account "${ACCOUNT_NAME}" \
        --images "${IMAGE_FILES[@]}" \
        --title "${TITLE}" \
        --note "${NOTE}"
    fi
  )
fi

if has_platform "x"; then
  if [[ "${TWITTER_MODE}" == "article" ]]; then
    echo "Opening X Article draft from: ${TWITTER_ARTICLE_FILE}"
    echo "The script fills the article and leaves final publish to you."
    "${BUN_X[@]}" "${X_POST_TO_X_DIR}/scripts/x-article.ts" "${TWITTER_ARTICLE_FILE}"
  else
    twitter post "${TWITTER_TEXT}" "${TWITTER_ARGS[@]}"
  fi
fi

if has_platform "bilibili"; then
  bili dynamic-post --from-file "${BILIBILI_FILE}"
fi
