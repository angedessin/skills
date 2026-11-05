#!/bin/bash
# PreToolUse(Bash) guard: プロジェクトの中の CLAUDE.md とルートの docs/ への素の rm / mv を deny する。
#
# なぜ要るか: 書き込みの ask（permissions と guard-gated-write）は rm / mv を塞がない。
# 脅威モデルは敵対者ではなく、止まるはずの場面で滑った善意のエージェント。完全な封鎖ではない。
# `.claude/` の素の rm / mv は sandbox が止める。
#
# 守る形と守らない形の正本はマスターの tests/hooks/run_fixtures.py。判定は guard_gated.py。
# 新しい変種の扱い: 普段の書き方で承認制のパスが実際に消える形は直す。それ以外は判定を増やさず、沈黙のケースに足す
# （シェルの解析で全部は防げず、沈黙しても通常の確認は残る）。
# python3 か guard_gated.py が無いと沈黙する（deny に倒すと通常の Bash が広く死ぬ）。

payload=$(cat)
[ -z "$payload" ] && exit 0

verdict=$(printf '%s' "$payload" | python3 "${0%/*}/guard_gated.py" delete 2>/dev/null)
if [ "$verdict" = "DENY" ]; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"CLAUDE.md / docs/ への rm / mv を検出しました（guard-gated-delete hook）。これらは承認制のパスで、削除・移動は書き込みゲートの迂回になります。消す必要があるなら、理由を示してユーザーに頼みます（追跡済みのファイルは git rm でも消せます）。"}}
EOF
fi

exit 0
