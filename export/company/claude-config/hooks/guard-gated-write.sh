#!/bin/bash
# PreToolUse(Bash) guard: 承認ゲート対象パスへの Bash 経由の書き込みを強制確認（ask）に落とす。
#
# なぜ要るか: permissions の ask は Edit / Write ツールにしか掛からない。allow に
# `Bash(git diff*)` / `Bash(git show*)` のような前置一致ルールがあると
# `git show HEAD:x > CLAUDE.md` が素通りし、Edit/Write を経由しないぶん ask が発火しない。
# ゲートしたいパスは、そこへ書ける全ツール分のルールを揃える必要がある。その Bash 側を担う。
#
# 脅威モデル: 敵対者ではなく「停止契約を滑った善意のエージェント」。実測された素通りは
# いずれも Edit/Write という自然な経路だったため、ここでは明示的な書き込みリダイレクト
# （> / >> / tee）だけを対象にする。sed -i や任意インタプリタ経由、および rm による削除までは
# 追わない（際限のない軍拡になり、脅威モデルが違う）。**完全な封鎖ではない**ことを前提に使う。
#
# 外部コマンドに依存しない（sh 組み込み + grep のみ）。標準入力の JSON を構造として
# 解析せず全文検査する。deny ではなく ask なので、誤検知の代償は一度余計に確認が出るだけ。

payload=$(cat)
[ -z "$payload" ] && exit 0

# 承認ゲート対象（settings.json の permissions.ask と対で維持する）
#   CLAUDE.md / docs/knowledge/ / docs/decisions/
targets='CLAUDE\.md|docs/knowledge/|docs/decisions/'

# 書き込みリダイレクト（> / >>）または tee の後に対象パスが現れるか。
# JSON エスケープされた引用符・空白を挟む形にも当たるよう緩めに見る。
if printf '%s' "$payload" | grep -qE ">>?[[:space:]\\\\\"']*[^|&;]*($targets)"; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"CLAUDE.md / docs/knowledge/ / docs/decisions/ への Bash 経由の書き込みを検出しました（guard-gated-write hook）。これらは承認制のパスです。knowledge-capture / compound がドラフト提示の停止を越えていないか確認してください。"}}
EOF
  exit 0
fi

if printf '%s' "$payload" | grep -qE "tee[[:space:]\\\\\"'-]+[^|&;]*($targets)"; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"CLAUDE.md / docs/knowledge/ / docs/decisions/ への tee 経由の書き込みを検出しました（guard-gated-write hook）。これらは承認制のパスです。"}}
EOF
fi

exit 0
