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

echo "Using account: ${ACCOUNT_NAME}"
echo

(
  cd "${SAU_ROOT}"
  "${SAU_PYTHON}" "${SAU_ENTRY}" douyin login --account "${ACCOUNT_NAME}" --headed
  "${SAU_PYTHON}" "${SAU_ENTRY}" kuaishou login --account "${ACCOUNT_NAME}" --headed
  "${SAU_PYTHON}" "${SAU_ENTRY}" xiaohongshu login --account "${ACCOUNT_NAME}" --headed
  "${SAU_PYTHON}" "${SAU_ENTRY}" bilibili login --account "${ACCOUNT_NAME}"
)

echo
echo "Twitter/X uses browser cookies."
echo "Run: twitter status"
