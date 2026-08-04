#!/bin/bash
# SessionStart hook（startup / resume / compact）: .steering/ を走査し、未処理フラグ
# （.capture-needed / .codify-needed）とアクティブタスク一覧、および rule-audit 月次ナッジを
# additionalContext で注入する。
# CLAUDE.md「セッション開始時: find を実行して確認」という説明文ルールの機械保証版。
# 根拠: 「停止・前提条件の契約は説明文では守られない」（skill-design-patterns.md の実証知見）。
# .steering/ が無いプロジェクトでは素通し（配置先自己完結）。
# compact 後（matcher: compact）にも発火するため .steering 再読リマインドを兼ねる。
#
# 外部コマンドは find / sed / sort など POSIX 標準ユーティリティを主とし、時刻だけ
# GNU/BSD 共通の `date +%s` を使う（失敗時は rule-audit ナッジ節のみスキップ＝フェイルオープン）。
# 出力 JSON のエスケープは json_escape() で行う。注入する文字列はこのスクリプトが組み立てた
# 固定文言とタスクのディレクトリ名だけなので、対象は " と \ と改行に限られる。

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$PROJECT_ROOT" ] && exit 0

STEERING_DIR="$PROJECT_ROOT/.steering"
[ -d "$STEERING_DIR" ] || exit 0

# フラグ検出 -> 該当タスク名（archived/ を除外）
capture_tasks=$(find "$STEERING_DIR" -name '.capture-needed' -not -path '*/archived/*' 2>/dev/null \
  | while read -r f; do basename "$(dirname "$f")"; done | sort)
codify_tasks=$(find "$STEERING_DIR" -name '.codify-needed' -not -path '*/archived/*' 2>/dev/null \
  | while read -r f; do basename "$(dirname "$f")"; done | sort)

# アクティブタスク一覧（archived を除く直下ディレクトリ）
tasks=$(find "$STEERING_DIR" -maxdepth 1 -mindepth 1 -type d ! -name archived 2>/dev/null \
  | sort | while read -r d; do echo "  - $(basename "$d")"; done)

msg=""
if [ -n "$capture_tasks" ]; then
  msg="${msg}【未保存ナレッジ】.capture-needed を検出。対象タスクごとに「今 / 後で / スキップ」で確認してください（一括スキップ禁止。この注入文が SessionStart の操作定義）:
対象タスク:
$(printf '%s\n' "$capture_tasks" | sed 's/^/  - /')
選択肢:
  - 今 → knowledge-capture を実行
  - 後で → フラグ残置（compact/resume で再確認可）
  - スキップ → 対象の .capture-needed を rm（capture_done は作らない。効果は次の Stop まで）

"
fi
if [ -n "$codify_tasks" ]; then
  msg="${msg}【未 codify の学び】.codify-needed を検出。ユーザーに「compound を実行しますか？」と確認してください。対象タスク:
$(printf '%s\n' "$codify_tasks" | sed 's/^/  - /')

"
fi

# rule-audit 月次ナッジ（capture / codify の後、アクティブタスクより前）
# スキル未配置・date 失敗時は本節だけスキップ（他注入は継続）。
RULE_AUDIT_SKILL="$PROJECT_ROOT/.claude/skills/rule-audit/SKILL.md"
if [ -f "$RULE_AUDIT_SKILL" ]; then
  now=$(date +%s 2>/dev/null) || now=""
  # 非数字・空は date 失敗と同等（本節スキップ）。先頭ゼロ付きも拒否（偽 date 対策）
  case "$now" in
    ''|*[!0-9]*|0[0-9]*) now="" ;;
  esac
  if [ -n "$now" ]; then
    marker="$STEERING_DIR/.last-rule-audit"
    nudge=1
    if [ -f "$marker" ]; then
      last=$(tr -d ' \t\n\r' < "$marker" 2>/dev/null)
      case "$last" in
        ''|*[!0-9]*|0[0-9]*)
          # 空・非数字・先頭ゼロ付き（八進 fatal の温床）→ 壊レ扱い＝ナッジ
          nudge=1
          ;;
        *)
          # 10# で十進強制。失敗時も壊レ扱い＝ナッジ（節外へ fatal を漏らさない）
          if age=$((10#$now - 10#$last)) 2>/dev/null; then
            # 未来時刻（age < 0）も含め、閾値未満なら非注入
            if [ "$age" -lt 2592000 ]; then
              nudge=0
            fi
          else
            nudge=1
          fi
          ;;
      esac
    fi
    if [ "$nudge" -eq 1 ]; then
      msg="${msg}【rule-audit 月次】最終 rule-audit から 30 日以上（または未実施）。「今 / 後で / スキップ」で確認してください（この注入文が SessionStart の操作定義。capture の三択とは別契約）:
選択肢:
  - 今 → rule-audit を実行（レポート提示 Step 5 到達時に .steering/.last-rule-audit を更新）
  - 後で → マーカー不変（次回 SessionStart で再確認可）
  - スキップ → .steering/.last-rule-audit を現在時刻で更新（監査せず 30 日再ナッジ。capture の次 Stop 寿命とは別）

"
    fi
  fi
fi

if [ -n "$tasks" ]; then
  msg="${msg}【アクティブタスク】作業開始前にすべて読み、複数ある場合はどれを再開するかユーザーに確認してください:
$tasks
"
fi

# 固定パスのバックログ。**存在と規模だけを知らせる**（中身は必要になってから読む）。
# なぜ必要か: 着手前のバックログをアーカイブ済みタスクの decisions.md に書くと、上の走査が
# archived/ を除外するため次セッションから構造的に見えない。アクティブタスクとして
# .steering/[task]/ に置くと毎セッションのコンテキスト固定費になるので、その中間として
# 1 枚のファイルを 1 行で知らせる。
# **「未着手 N 件」とは書かない** — 節には「既知の環境問題（タスクではない）」のような
# 非タスク項目も含まれるため、件数として数えると誤報になる。
BACKLOG="$STEERING_DIR/BACKLOG.md"
if [ -f "$BACKLOG" ]; then
  sections=$(grep -c '^## ' "$BACKLOG" 2>/dev/null)
  [ -z "$sections" ] && sections=0
  msg="${msg}【バックログ】.steering/BACKLOG.md（${sections} 節）— 着手前の候補。次のタスクを選ぶときに読んでください。
"
fi

[ -z "$msg" ] && exit 0

# JSON 文字列本体へのエスケープ（囲みの " は付けない）:
# \ と " をエスケープし、タブと改行を \t / \n に畳む。
# **改行の畳み込みは移植形の `$!{N;ba}` を使う。** よくある `:a;N;$!ba;s/\n/\\n/g` は
# **BSD sed（macOS）で入力が 1 行のとき何も出力しない**（N が EOF で打ち切る）。
# 従来は msg が「見出し + 項目」で必ず 2 行以上だったため到達しなかったが、1 行だけの
# 通知を足した瞬間に空の additionalContext を注入する（= 静かに何も伝えない）状態になる。
json_escape() {
  printf '%s' "$1" \
    | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/	/\\t/g' \
    | sed -e ':a' -e '$!{N;ba' -e '}' -e 's/\n/\\n/g'
}

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' \
  "$(json_escape "$msg")"
exit 0
