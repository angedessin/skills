#!/bin/bash
# PreToolUse(Bash) guard: 承認ゲート対象パスへの Bash 経由の書き込みを強制確認（ask）に落とす。
#
# GATED_PATHS: CLAUDE.md docs/ .claude/
#
# ↑ 対象パスの正本（この 1 行）。末尾 / はディレクトリ配下。permissions.ask の Edit(./...) と対で維持し、
#   tests/sandbox/check_settings.py が突合する。フィクスチャはこの行からケースを自動生成する。
#   guard-gated-delete.sh は `.claude/` を sandbox に任せるので対象が違い、突合の対象外。
#
# なぜ要るか: permissions のファイルパス ask は Edit(path) のみ（Write ツール呼び出しも Edit 規則が覆う）。
# Bash のリダイレクト先は Claude Code 自体も検査するが、見るのは Edit の allow / deny と作業ディレクトリで
# ask は見ない — acceptEdits では `git show HEAD:a > CLAUDE.md` が ask をすり抜けて上書きされた（20260927・
# 2.1.283 で実測。20261103 の公式 permissions でも検査の対象に ask は無いが、実測はしていない。結果によらずこの
# hook は残すので測らない）。sandbox は CLAUDE.md・docs/ を守らない（作業ディレクトリは書き込める・ask が無い）ので、
# sandbox を有効にしてもこの hook は要る。
#
# 守る形（ask）: 連鎖（&& || ; | 改行 { } ( )）のすべての部分について
#   - 出力リダイレクト（> >> &> 2> >| 等）の先が対象パス
#   - tee の書き込み先が対象パス
#   - git mv の引数に対象パス（settings.local.json の `Bash(git mv *)` で上書きできるため。-C の値と合成して見る）
#   先頭の代入・ラッパー（env / exec / sudo / timeout 等）は読み飛ばす。照合は大文字小文字を区別しない
#   （macOS の既定 FS は区別せず、`> CLAUDE.MD` でも実ファイルが書き換わる）。ヒアドキュメントの本文は見ない。
# 守らない形（沈黙）: cd 後の相対パス・変数展開・bash -c / eval の中身・cp・sed -i・任意インタプリタ。
#   これらは settings の `autoAllowBashIfSandboxed: false` により通常の確認に落ちる。
# 脅威モデルは敵対者ではなく「停止契約を滑った善意のエージェント」。**完全な封鎖ではない**。
#
# 判定は guard_gated.py（guard-gated-delete と共通の抽出）。tool_input.command だけを見る。全文検査はしない
# — 入力 JSON には transcript_path（~/.claude/projects/...）が常に入り、.claude/ の判定が恒常的に誤検知する。
# python3 が無い・解析に失敗したときは、下の全文 grep に縮退する（完全な沈黙にはしない）。
# 縮退中は .claude/ と git mv を守らない（python3 前提の防御）。
# 出力は ask の JSON を最大 1 つ（deny は出さない — 誤検知の代償を確認 1 回に抑える）。

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
