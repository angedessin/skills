#!/bin/bash
# 条件 B・C の「スキルに触れる CLAUDE.md」を注入する。plugin eval は隔離でプロジェクトの
# CLAUDE.md を読まないため、plugin の SessionStart hook で入れる（plugin の無い条件 A には入らない）。
# 中身は prepare.sh が conditions/<条件>/skill-claude-md.md から複製する。無ければ何も出さない
set -euo pipefail
f="${CLAUDE_PLUGIN_ROOT}/hooks/skill-claude-md.md"
if [ -f "$f" ]; then cat "$f"; fi
