#!/usr/bin/env bash
# 差分の中で足したテストの免除（test-exemptions.md の行）を並べる。読むだけで、何も書かない。
# 同じファイルを frontend-code-review と pr-create の scripts/ に置く（一致は test:skills で見る）。
#
# Usage: list-exemptions.sh [--base <ref> [--worktree]]
#   指定なし            HEAD と作業ツリーを比べる（未追跡の免除ファイルも見る）
#   --base <ref>        <ref> との分岐点と HEAD を比べる
#   --worktree          --base と一緒に。分岐点と作業ツリーを比べる
#   GIT=<path>          使う git（PATH の先頭の git が動かない環境で、動く git を渡す）
#
# 出力: exemptions: <件数> と、1 件ごとの「  [節] パス — 理由 (免除ファイル)」
#       分からないときは exemptions: unknown (<理由>)
# 終了コード: 0 = 数えた、または分からないと出した / 2 = 引数の誤り・git が動かない・リポジトリの外
set -u
set -o pipefail

die() {
  printf 'list-exemptions: %s\n' "$1" >&2
  exit 2
}
# 免除が読めないことでレビューや PR を止めないよう、0 で終わる
unknown() {
  printf 'exemptions: unknown (%s)\n' "$1"
  exit 0
}

base=""
worktree=0
while [ $# -gt 0 ]; do
  case "$1" in
    --base)
      [ $# -ge 2 ] || die "--base には ref が要る"
      base=$2
      shift 2
      ;;
    --worktree)
      worktree=1
      shift
      ;;
    --) die "パスでの絞り込みは受けない（免除ファイルは常に全部見る）" ;;
    *) die "知らない引数: $1" ;;
  esac
done
if [ "$worktree" = 1 ] && [ -z "$base" ]; then
  die "--worktree は --base と一緒に使う"
fi

# macOS の /usr/bin/git は sandbox の中でキャッシュの警告を stderr に出すので、成否は終了コードで見る
git=${GIT:-git}
"$git" rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "git が動かないか、git の作業ツリーの外にいる（動く git は GIT=<パス> で渡す）"
"$git" rev-parse --verify -q HEAD >/dev/null 2>&1 || die "HEAD が無い（コミットが 1 つも無い）"
top=$("$git" rev-parse --show-toplevel 2>/dev/null) || die "リポジトリの最上位が分からない"
cd "$top" || die "リポジトリの最上位に移れない: ${top}"

if [ -z "$base" ]; then
  prev=HEAD
  now=worktree
else
  "$git" rev-parse --verify -q "${base}^{commit}" >/dev/null 2>&1 || die "ベースが見つからない: ${base}"
  prev=$("$git" merge-base "$base" HEAD 2>/dev/null) || die "merge-base が見つからない: ${base}"
  if [ "$worktree" = 1 ]; then now=worktree; else now=HEAD; fi
fi

nl=$'\n'
tab=$'\t'

# 場所の規則は stop-test-gate.sh と同じ（タスクの直下か .steering の直下。archived は見ない）
is_ex_path() {
  local task
  case "$1" in
    .steering/test-exemptions.md) return 0 ;;
    .steering/archived/*) return 1 ;;
    .steering/*/test-exemptions.md)
      task=${1#.steering/}
      task=${task%/test-exemptions.md}
      case "$task" in */*) return 1 ;; esac
      return 0
      ;;
  esac
  return 1
}

disk_files=""
for f in .steering/test-exemptions.md .steering/*/test-exemptions.md; do
  [ -f "$f" ] || continue
  is_ex_path "$f" || continue
  disk_files="${disk_files}${f}${nl}"
done

# ここから先は、改行区切りの一覧を for で回す。here-string とプロセス置換は sandbox で落ちることがある
IFS=$nl
set -f

# 無視されている免除ファイルは git から見えず、足したかどうかを比べられない
for f in $disk_files .steering/test-exemptions.md; do
  "$git" check-ignore -q -- "$f" >/dev/null 2>&1
  case $? in
    0) unknown "免除ファイルが gitignore で無視されている: ${f}" ;;
    1) ;;
    *) unknown "git check-ignore が失敗した" ;;
  esac
done

# 行の判定は stop-test-gate.sh の exempt_paths と同じ規則。出力は 節<TAB>パス<TAB>理由
entries() {
  local line on=0 sec="" path reason
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      "## "*)
        sec=${line#"## "}
        case "$sec" in
          "テスト不要" | "失敗を残す" | "テストを弱める") on=1 ;;
          *) on=0 ;;
        esac
        continue
        ;;
    esac
    [ "$on" = 1 ] || continue
    case "$line" in "- "*" — "*) ;; *) continue ;; esac
    line=${line#- }
    path=${line%% — *}
    reason=${line#* — }
    path=${path#\`}
    path=${path%\`}
    path=${path#./}
    [ -n "${reason//[[:space:]]/}" ] || continue
    printf '%s\t%s\t%s\n' "$sec" "$path" "$reason"
  done
}

tree_files() { # $1 = コミット
  local out p
  out=$("$git" -c core.quotepath=false ls-tree -r --name-only "$1" -- .steering 2>/dev/null) || return 1
  for p in $out; do
    is_ex_path "$p" && printf '%s\n' "$p"
  done
  return 0
}
has_line() { printf '%s\n' "$1" | grep -qxF -- "$2"; }

count=0
out=""
emit_new() { # $1 = 今の行  $2 = 前の行  $3 = 出どころの表示
  local l sec rest
  for l in $1; do
    has_line "$2" "$l" && continue
    has_line "$shown" "$l" && continue
    shown="${shown}${l}${nl}"
    sec=${l%%"$tab"*}
    rest=${l#*"$tab"}
    out="${out}  [${sec}] ${rest%%"$tab"*} — ${rest#*"$tab"} ($3)${nl}"
    count=$((count + 1))
  done
}
prev_entries() { # $1 = 免除ファイル。結果は PE に入れる
  PE=""
  if has_line "$prev_files" "$1"; then
    PE=$("$git" show "${prev}:$1" 2>/dev/null | entries) || unknown "git show が失敗した: ${prev}:$1"
  fi
}

head_files=$(tree_files HEAD) || unknown "git ls-tree が失敗した: HEAD"
if [ "$prev" = HEAD ]; then
  prev_files=$head_files
else
  prev_files=$(tree_files "$prev") || unknown "git ls-tree が失敗した: ${prev}"
fi
if [ "$now" = worktree ]; then now_files=$disk_files; else now_files=$head_files; fi

for f in $now_files; do
  if [ "$now" = worktree ]; then
    ne=$(entries <"$f") || unknown "免除ファイルを読めない: ${f}"
  else
    ne=$("$git" show "HEAD:${f}" 2>/dev/null | entries) || unknown "git show が失敗した: HEAD:${f}"
  fi
  prev_entries "$f"
  shown=""
  emit_new "$ne" "$PE" "$f"
done

# タスクを閉じると免除ファイルごと消え、上の比較からは見えなくなる
if [ -n "$base" ]; then
  closed=""
  if [ "$now" = worktree ]; then
    # 閉じる途中（git rm の後、コミットの前）は、HEAD の版が消える直前の版
    for f in $head_files; do
      has_line "$disk_files" "$f" && continue
      closed="${closed}${f}${nl}"
      ne=$("$git" show "HEAD:${f}" 2>/dev/null | entries) || unknown "git show が失敗した: HEAD:${f}"
      prev_entries "$f"
      shown=""
      emit_new "$ne" "$PE" "閉じたタスク: ${f}"
    done
  fi
  # 同じコミットで似た免除ファイルを足すと、削除が改名と判定されて D から落ちる
  log=$("$git" -c core.quotepath=false log --no-renames --diff-filter=D --name-only --format='C %H' "${prev}..HEAD" -- .steering 2>/dev/null) || unknown "git log が失敗した"
  commit=""
  for l in $log; do
    case "$l" in
      "C "*)
        commit=${l#C }
        continue
        ;;
    esac
    is_ex_path "$l" || continue
    has_line "$now_files" "$l" && continue
    # 新しい順に並ぶので、同じパスは最後に消したコミットだけを見る
    has_line "$closed" "$l" && continue
    closed="${closed}${l}${nl}"
    ne=$("$git" show "${commit}^:${l}" 2>/dev/null | entries) || unknown "git show が失敗した: ${commit}^:${l}"
    prev_entries "$l"
    shown=""
    emit_new "$ne" "$PE" "閉じたタスク: ${l}"
  done
fi

printf 'exemptions: %d\n' "$count"
printf '%s' "$out"
exit 0
