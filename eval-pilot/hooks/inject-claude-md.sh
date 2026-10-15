#!/bin/bash
# B の CLAUDE.md を近似する。plugin eval は隔離でプロジェクトの CLAUDE.md を読まないため、
# plugin の SessionStart hook で注入する（スキルなしの条件 A には入らない）
set -euo pipefail
cat "${CLAUDE_PLUGIN_ROOT}/hooks/project-claude-md.md"
