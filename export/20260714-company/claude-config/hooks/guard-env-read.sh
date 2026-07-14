#!/bin/bash
# PreToolUse(Bash) guard: .env 系ファイルに触れるコマンドを強制確認（ask）に落とす
# permissions.deny の Bash ルールは文字列前置一致で迂回が容易（head/sed/base64/リダイレクト等）なため、
# コマンド全文を検査して dotfile 形式の .env 参照を検出する。
# 注意: process.env や *.env（prod.env 等）には反応しない設計（誤検知防止とのトレードオフ）。

# jq が無い環境ではコマンドを検査できない → フェイルクローズ（無言で素通しにしない）
if ! command -v jq >/dev/null 2>&1; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"guard-env-read hook: jq が未導入のためコマンドを検査できません（フェイルクローズ）。jq を導入するか、このコマンドが .env に触れないことを確認して承認してください。"}}
EOF
  exit 0
fi

cmd=$(jq -r '.tool_input.command // empty' 2>/dev/null)
[ -z "$cmd" ] && exit 0

# 行頭・空白・引用符・=・/・( の直後に始まる「.env」（.env.local 等を含む）を検出
if printf '%s' "$cmd" | grep -qE "(^|[[:space:]\"'=/(])\.env"; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"コマンドが .env 系ファイルに触れる可能性があります（guard-env-read hook）。意図的な操作なら承認してください。"}}
EOF
fi

exit 0
