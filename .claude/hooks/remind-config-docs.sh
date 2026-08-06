#!/bin/bash
# PostToolUse(Edit|Write) — 編集対象に応じて、該当する知識ファイルの「ルール本文」を注入する。
#
# なぜポインタではなく本文を注入するか:
#   CLAUDE.md には「settings.json・hooks 作業時: docs/knowledge/claude-code-config.md を読む」
#   という導線があるが、20260725 に settings.json と hooks を繰り返し編集しながら一度も読まず、
#   同ファイルに記録済みのルールを 3 つ破った（うち 2 つは欠陥として出荷された）。
#   同じセッションで、CLAUDE.md の @参照で全文がロードされていた skill-design-patterns.md の
#   ルールは一貫して守れていた。差は「内容が context にあったか否か」だけだった。
#   したがってここでは「読め」という新しいポインタを増やさず、要点そのものを渡す。
#
# なぜ PostToolUse か: PreToolUse の additionalContext はこのリポジトリで実績がない
#   （post-edit-lint.sh / session-start-check.sh はいずれも additionalContext を使うが
#   PostToolUse / SessionStart）。最初の 1 回は編集後の注入になるが、以降の編集には間に合う。
#
# なぜセッション 1 回だけか: このリポジトリの主作業は SKILL.md の編集であり、毎回注入すると
#   それ自体が新しいコンテキスト固定費になる（@参照を外した意味が薄れる）。
#
# **判定は file_path だけを見る。** guard-env-read.sh はペイロード全文を検査するが、
# あちらは「誤検知の代償が確認 1 回」の ask なので全文で妥当。こちらは内容注入なので、
# 誤発火＝無関係なルールの注入（コンテキストの無駄）になる。実際、全文検査版は
# docs/knowledge/claude-code-config.md の編集で誤発火した — 編集内容に
# ".claude/settings.json" という文字列が含まれていたため（20260725 実測）。
#
# 依存ゼロ（sh 組み込み + grep / sed）。

payload=$(cat)
[ -z "$payload" ] && exit 0

# file_path の値だけを取り出す（無ければ何もしない）
fp=$(printf '%s' "$payload" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
[ -z "$fp" ] && exit 0

# セッション ID を切り出す（無ければ日付で代替してその日 1 回にする）
sid=$(printf '%s' "$payload" | grep -o '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)"$/\1/')
[ -z "$sid" ] && sid="nosid-$(date +%Y%m%d)"

emit() { # $1=カテゴリ  $2=注入する本文
  marker="/tmp/claude-remind-${sid}-$1"
  [ -e "$marker" ] && return 0
  : > "$marker"
  printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}\n' "$2"
}

case "$fp" in
  *".claude/settings.json"|*".claude/hooks/"*)
    emit "config" "設定・hook を編集しました。docs/knowledge/claude-code-config.md の要点（このセッションで 1 回だけ通知）: (1) permissions のファイルパス規則は Edit(path)/Read(path) のみ（Write(path) は死んだ規則で起動時警告）。ゲートしたいパスは Bash / Read / Edit のうち到達可能な全ツール分を揃える。Edit だけの ask は Bash のリダイレクトで迂回される。(2) glob は形式を列挙する — ディレクトリ配下は */**/**/* の 3 形式。単一形式では直下のファイルを取りこぼす。(3) セッション中に追加した hook が効くかはイベント種別で割れる（PostToolUse は即座に効いたが PreToolUse の追加分は効かなかった実測がある・原因未解明）。PreToolUse でガードを足したらセッション再起動後に実効性を確認し、確認できるまで機械的な防御として数えない。書いたことを効いていることの証拠にしない。"
    ;;
esac

case "$fp" in
  *".claude/skills/"*"SKILL.md")
    emit "skills" "スキル本文を編集しました。docs/knowledge/skill-design-patterns.md の要点（このセッションで 1 回だけ通知）: (1) 停止・承認・前提条件の契約はハードストップの手順として書く — 説明文では守られない。停止は独立見出しにし、次の行動ステップは「承認後の〜」に分ける。(2) 同じ情報を持つ全箇所を直してから閉じる（片側修正の禁止）— 契約が値の集合の場合は producer と consumer を名指しで突合する。(3) 並列サブスキルの責務境界は各本文に相互明記する。(4) 配布可スキルの本文に日付付きの内部エピソードやこのリポジトリ固有の語を残さない。詳細が要る場合は同ファイルを読む。"
    ;;
esac

exit 0
