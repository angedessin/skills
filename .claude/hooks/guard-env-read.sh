#!/bin/bash
# PreToolUse(Bash) guard: .env 系ファイルに触れるコマンドを強制確認（ask）に落とす。
# permissions.deny の Bash ルールは文字列前置一致で迂回が容易（head/sed/base64/リダイレクト等）なため、
# コマンド全文を検査して dotfile 形式の .env 参照を検出する。
#
# 外部コマンドに依存しない（sh 組み込み + grep のみ）。標準入力の JSON を構造として解析せず
# 全文検査する — 解析器が要らないうえ、フィールド名の変更や入れ子の違いで素通りしない。
# matcher が Bash 限定なのでペイロードは実質コマンド文字列であり、誤検知の代償は
# 「余計に一度確認が出る」だけ（deny ではなく ask のため安全側に倒している）。
#
# 注意: process.env や *.env（prod.env 等）には反応しない設計（誤検知防止とのトレードオフ）。

payload=$(cat)
[ -z "$payload" ] && exit 0

# 行頭・空白・引用符・=・/・( ・バックスラッシュ（JSON エスケープ）の直後に始まる
# 「.env」（.env.local 等を含む）を検出
if printf '%s' "$payload" | grep -qE "(^|[[:space:]\"'=/(\\\\])\.env"; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"コマンドが .env 系ファイルに触れる可能性があります（guard-env-read hook）。意図的な操作なら承認してください。"}}
EOF
fi

exit 0
