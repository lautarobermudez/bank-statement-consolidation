#!/usr/bin/env bash
# Install the skill into Claude Code (~/.claude/skills, or $CLAUDE_SKILLS_DIR).
#
#   ./install.sh            copy the skill (re-run it after every `git pull`)
#   ./install.sh --link     symlink to this repository instead (updates with `git pull`, but
#                           Claude Code may not auto-discover symlinked skills; the copy is the safe default)
#   ./install.sh --force    replace an existing installation (it is deleted: the repository is the source of truth)
set -euo pipefail

NAME="consolidar-extractos"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skills/${NAME}"
DEST_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
DEST="${DEST_DIR}/${NAME}"
MODE="copy"; FORCE=0
for arg in "$@"; do
  case "$arg" in
    --link) MODE="link" ;;
    --copy) MODE="copy" ;;
    --force) FORCE=1 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

[ -f "${SRC}/SKILL.md" ] || { echo "Cannot find ${SRC}/SKILL.md" >&2; exit 1; }
mkdir -p "${DEST_DIR}"

if [ -e "${DEST}" ] || [ -L "${DEST}" ]; then
  if [ "${FORCE}" -ne 1 ]; then
    echo "${DEST} already exists. Re-run with --force to replace it." >&2
    exit 1
  fi
  rm -rf "${DEST}"          # no .bak next to it: every folder inside skills/ is read as a skill
fi

if [ "${MODE}" = "link" ]; then
  ln -s "${SRC}" "${DEST}"
  echo "Linked ${DEST} -> ${SRC}"
else
  cp -r "${SRC}" "${DEST}"
  find "${DEST}" -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
  echo "Copied ${SRC} -> ${DEST}"
fi
echo "Python dependencies: pip install -r ${SRC}/scripts/requirements.txt"
