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

echo "== social-auto-upload =="
(
  cd "${SAU_ROOT}"
  "${SAU_PYTHON}" "${SAU_ENTRY}" douyin check --account "${ACCOUNT_NAME}" || true
  "${SAU_PYTHON}" "${SAU_ENTRY}" kuaishou check --account "${ACCOUNT_NAME}" || true
  "${SAU_PYTHON}" "${SAU_ENTRY}" xiaohongshu check --account "${ACCOUNT_NAME}" || true
  "${SAU_PYTHON}" "${SAU_ENTRY}" bilibili check --account "${ACCOUNT_NAME}" || true
)

echo
echo "== twitter-cli =="
twitter status || true

echo
echo "== bilibili-cli =="
bili status || true
