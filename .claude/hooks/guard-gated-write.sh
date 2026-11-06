#!/bin/bash
# PreToolUse(Bash) guard: 承認制のパスへの Bash 経由の書き込み（リダイレクト・tee・cp・sed -i・git mv）を ask にする。
#
# GATED_PATHS: CLAUDE.md docs/ .claude/
#
# ↑ 対象パスの正本。末尾 / はディレクトリ配下。マスターの tests/sandbox/check_settings.py が permissions.ask と突き合わせる。
#
# なぜ要るか: permissions の ask は Bash の書き込みを見ない。acceptEdits では `git show HEAD:a > CLAUDE.md` が
# 上書きされた（20260927・2.1.283 で実測）。sandbox は作業ディレクトリの CLAUDE.md・docs/ を守らない。
# 脅威モデルは敵対者ではなく、止まるはずの場面で滑った善意のエージェント。完全な封鎖ではない。
#
# 守る形と守らない形の正本はマスターの tests/hooks/run_fixtures.py。判定は guard_gated.py。
# 全文は見ない: 入力の transcript_path（~/.claude/projects/...）が .claude/ に常に当たる。
# 判定できないときは下の全文 grep に縮退する（リダイレクトと tee だけ。.claude/・git mv・cp・sed -i は見ない）。
# deny にしないのは誤検知の代償を確認 1 回に抑えるため。

payload=$(cat)
[ -z "$payload" ] && exit 0

ask_json() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"%s"}}\n' "$1"
}

reason='承認制のパス（CLAUDE.md / docs/ / .claude/）への Bash 経由の書き込み・移動を検出しました（guard-gated-write hook）。承認制のパスは Edit / Write ツールで書きます。意図した操作か確認してください。'

# 構造判定。標準出力: ASK / SILENT。それ以外（python3 不在・例外）は縮退へ。
verdict=$(printf '%s' "$payload" | python3 "${0%/*}/guard_gated.py" write "$0" 2>/dev/null)
case "$verdict" in
  ASK) ask_json "$reason"; exit 0 ;;
  SILENT) exit 0 ;;
esac

# ---- 縮退: python3 不在・解析失敗。全文 grep（リダイレクトと tee のみ）----
# 全文検査なので誤検知はありうる（ask なので代償は確認 1 回）。.claude/ 系は transcript_path と衝突するため見ない。
targets='CLAUDE\.md|docs/'
if printf '%s' "$payload" | grep -qiE ">>?[[:space:]\\\\\"']*[^|&;]*($targets)"; then
  ask_json "$reason"
  exit 0
fi
if printf '%s' "$payload" | grep -qiE "tee[[:space:]\\\\\"'-]+[^|&;]*($targets)"; then
  ask_json "$reason"
fi

exit 0
