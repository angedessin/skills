#!/bin/bash
# 検証役（review-verify）の作業ツリーの見張り。開始時に控え、終了時に比べ、違えば 1 回だけ差し戻す。
# 事故を防ぐのではなく、起きた後に気づくための仕組み（検証役の Bash は残すため）。
#
# Usage: subagent-tree-guard.sh start|stop|report   （入力は hook の JSON を stdin で）
#   start  SubagentStart: リポジトリの根と中身を控える。控えが既にあれば上書きしない（再開で汚れた状態を控え直さない）
#   stop   SubagentStop:  控えた根を今と比べ、結果を記録する。違えば 1 回目だけ exit 2 で差し戻す
#   report PostToolUse(Agent)・親の Stop: その session の未報告の記録を親に知らせる。違いの残ったもの・戻ったものは 1 回ずつ、
#          確かめていないものは session ごとに 1 回。PostToolUse は additionalContext で、Stop は exit 2 で知らせる
#          （背景で起動した agent は PostToolUse が起動の直後に来るので、親の Stop でも拾う）
# 記録: ${TMPDIR}/claude-tree-guard/<session_id>/<agent_id>/ の root・state・result・diff・rejected・reported
#   result は same（同じ）・differs（違い、差し戻した）・returned（差し戻しの後に戻った）・
#   not-returned（差し戻しの後も違う）・unchecked（控えが無く確かめていない）
# git・jq が無い・リポジトリの外では素通しする（ほかの hook と同じ）。
#   --mirror-gitdir（2 つ目の引数）: stop の結果を、見張ったリポジトリの .git/tree-guard.log にも 1 行ずつ足す。
#   評価（claude plugin eval）の grader は TMPDIR を読めず、ワークスペースのファイルしか見られないため。普段は付けない

mode=${1:-}
mirror=0
[ "${2:-}" = --mirror-gitdir ] && mirror=1
command -v jq >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0
input=$(cat)

# 欄ごとに読む: タブ区切りで 1 回に読むと、空の欄が詰まって後ろの欄がずれる
field() { printf '%s' "$input" | jq -r --arg k "$1" '.[$k] // "" | tostring' 2>/dev/null; }
sid=$(field session_id)
aid=$(field agent_id)
cwd=$(field cwd)
safe() { printf '%s' "$1" | tr -c 'A-Za-z0-9_.-' '_'; }
base="${TMPDIR:-/tmp}/claude-tree-guard"
sdir="$base/$(safe "${sid:-nosession}")"
if [ -n "$aid" ]; then
  dir="$sdir/$(safe "$aid")"
else
  dir="$sdir/noid-$$"
fi

# 1 行 1 項目: 種類 TAB 鍵 TAB 値。H=HEAD・R=ref・W=HEAD と違う追跡ファイルの中身・I=索引・U=未追跡のファイルの中身
# git status は使わない: 既に変更のあるファイルをさらに書き換えても行が変わらない
state() {
  local r=$1 head tree p h
  local g=(git -C "$r" --no-optional-locks -c core.quotepath=false)
  head=$("${g[@]}" rev-parse -q --verify HEAD 2>/dev/null) || head=none
  printf 'H\tHEAD\t%s\n' "$head"
  # リモートの ref は見ない（IDE の自動 fetch で変わる）
  "${g[@]}" for-each-ref --format='R%09%(refname)%09%(objectname)' refs/heads refs/tags refs/stash || return 1
  tree=$head
  [ "$head" = none ] && { tree=$("${g[@]}" hash-object -t tree /dev/null) || return 1; }
  while IFS= read -r -d '' p; do
    if [ -e "$r/$p" ] || [ -L "$r/$p" ]; then
      h=$("${g[@]}" hash-object --no-filters -- "$p") || return 1
    else
      h=deleted
    fi
    printf 'W\t%s\t%s\n' "$p" "$h"
  done < <("${g[@]}" diff --no-ext-diff --no-renames --name-only -z "$tree" 2>/dev/null)
  "${g[@]}" diff --no-ext-diff --no-renames --cached --raw --no-abbrev "$tree" 2>/dev/null |
    awk -F'\t' '{ print "I\t" $2 "\t" $1 }'
  # 未追跡はディレクトリに畳まず 1 ファイルずつ（畳むと、下に足しても行が変わらない）
  local list
  list=$("${g[@]}" ls-files --others --exclude-standard) || return 1
  if [ -n "$list" ]; then
    paste <(printf '%s\n' "$list") <(printf '%s\n' "$list" | "${g[@]}" hash-object --no-filters --stdin-paths) |
      awk -F'\t' '{ print "U\t" $1 "\t" $2 }'
  fi
}

# 控え（$1）と今（$2）の違いを、人が読む行にする
describe() {
  local root=$1 old=$2 new=$3 kind key a b
  awk -F'\t' 'NR == FNR { o[$1 FS $2] = $3; next } { n[$1 FS $2] = $3 }
    END {
      for (k in o) if (!(k in n)) print "-" FS k FS o[k] FS ""; else if (o[k] != n[k]) print "~" FS k FS o[k] FS n[k]
      for (k in n) if (!(k in o)) print "+" FS k FS "" FS n[k]
    }' "$old" "$new" | sort -t$'\t' -k2,2 -k3,3 |
    while IFS=$'\t' read -r op kind key a b; do
      case "$kind" in
        H)
          printf -- '- HEAD が変わった: %s → %s\n' "${a:0:12}" "${b:0:12}"
          if [ "$a" != none ] && [ "$b" != none ]; then
            git -C "$root" --no-optional-locks log --oneline -10 "$a..$b" 2>/dev/null | sed 's/^/    増えたコミット: /'
          fi
          ;;
        R)
          case "$op" in
            +) printf -- '- ref が増えた: %s\n' "$key" ;;
            -) printf -- '- ref が消えた: %s\n' "$key" ;;
            *) printf -- '- ref が動いた: %s\n' "$key" ;;
          esac
          ;;
        W) printf -- '- 追跡ファイルの中身が変わった: %s\n' "$key" ;;
        I) printf -- '- ステージが変わった: %s\n' "$key" ;;
        U)
          case "$op" in
            +) printf -- '- 未追跡のファイルが増えた: %s\n' "$key" ;;
            -) printf -- '- 未追跡のファイルが消えた: %s\n' "$key" ;;
            *) printf -- '- 未追跡のファイルの中身が変わった: %s\n' "$key" ;;
          esac
          ;;
      esac
    done
}

record() { # $1 = 結果
  mkdir -p "$dir" 2>/dev/null && printf '%s\n' "$1" >"$dir/result"
  [ "$mirror" = 1 ] || return 0
  local r=${root:-$cwd} gd
  gd=$(git -C "$r" rev-parse --absolute-git-dir 2>/dev/null) || return 0
  case "$1" in
    unchecked) echo "TREE-GUARD-UNCHECKED" ;;
    same | returned | not-returned | differs) echo "TREE-GUARD-CHECKED $1" ;;
  esac >>"$gd/tree-guard.log"
  case "$1" in
    differs | not-returned | returned) echo "TREE-GUARD-DIFF $1" >>"$gd/tree-guard.log" ;;
  esac
}

case "$mode" in
  start)
    [ -n "$aid" ] && [ -n "$cwd" ] || exit 0
    [ -f "$dir/state" ] && exit 0
    root=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null) || exit 0
    [ -n "$root" ] || exit 0
    # 古い session の記録を消す（1 日より前）
    [ -d "$base" ] && find "$base" -mindepth 1 -maxdepth 1 -type d -mmin +1440 -exec rm -rf {} + 2>/dev/null
    mkdir -p "$dir" || exit 0
    tmp="$dir/state.tmp"
    if state "$root" >"$tmp" 2>/dev/null; then
      printf '%s\n' "$root" >"$dir/root"
      mv "$tmp" "$dir/state"
    else
      rm -f "$tmp"
    fi
    exit 0
    ;;
  stop)
    if [ ! -f "$dir/state" ] || [ ! -f "$dir/root" ]; then
      record unchecked
      echo "subagent-tree-guard: 開始時の控えが無いので、作業ツリーを比べていない" >&2
      exit 0
    fi
    # 根は控えたものだけを使う（写しや一時リポジトリに移った後の cwd から決め直さない）
    root=$(cat "$dir/root")
    now="$dir/state.now"
    if ! state "$root" >"$now" 2>/dev/null; then
      record unchecked
      echo "subagent-tree-guard: ${root} の今の状態を読めないので、比べていない" >&2
      exit 0
    fi
    diff_text=$(describe "$root" "$dir/state" "$now")
    rm -f "$now"
    if [ -z "$diff_text" ]; then
      if [ -f "$dir/rejected" ]; then record returned; else record same; fi
      exit 0
    fi
    printf '%s\n' "$diff_text" >"$dir/diff"
    # 差し戻しは agent ごとに 1 回だけ。2 回目からは、覚えのない違いに手を出す危険の方が大きい
    if [ -f "$dir/rejected" ]; then
      record not-returned
      exit 0
    fi
    : >"$dir/rejected"
    record differs
    {
      echo "作業ツリーの見張り（subagent-tree-guard）: 検証役の間に、リポジトリ ${root} の作業ツリーが変わった。"
      printf '%s\n' "$diff_text" | head -30
      echo "自分が作った・変えたものだけを戻すこと。覚えのない違いには触らないこと（ユーザーが同時に編集していることがある）。"
      echo "戻したものと戻せなかったものを、返す結果の先頭に書くこと。"
    } >&2
    exit 2
    ;;
  report)
    # 背景の agent の起動直後（まだ終わっていない）は読まない
    status=$(printf '%s' "$input" | jq -r '.tool_response.status // ""' 2>/dev/null)
    [ "$status" = async_launched ] && exit 0
    [ -d "$sdir" ] || exit 0
    msg=""
    unchecked=0
    for d in "$sdir"/*/; do
      d=${d%/}
      [ -f "$d/result" ] && [ ! -f "$d/reported" ] || continue
      r=$(cat "$d/result")
      id=${d##*/}
      root_of=$(cat "$d/root" 2>/dev/null)
      case "$r" in
        not-returned)
          msg+="- 検証役（${id}）の間に ${root_of} の作業ツリーが変わり、差し戻した後も違いが残っている:"$'\n'
          msg+="$(sed 's/^/  /' "$d/diff" 2>/dev/null | head -30)"$'\n'
          ;;
        returned)
          msg+="- 検証役（${id}）の間に ${root_of} の作業ツリーが変わったが、差し戻した後に元に戻った。戻る前の違い:"$'\n'
          msg+="$(sed 's/^/  /' "$d/diff" 2>/dev/null | head -30)"$'\n'
          ;;
        unchecked) unchecked=1 ;;
        *) continue ;; # same は知らせない。differs は検証役の次の終了で決まる
      esac
      : >"$d/reported"
    done
    if [ "$unchecked" = 1 ] && [ ! -f "$sdir/unchecked-reported" ]; then
      : >"$sdir/unchecked-reported"
      msg+="- 検証役の作業ツリーを確かめていないものがある（開始時の控えが無く、見張りが動いていない）。レビューの報告の「レビューできなかったもの」に書くこと"$'\n'
    fi
    [ -n "$msg" ] || exit 0
    text="作業ツリーの見張り（subagent-tree-guard）からの知らせ:"$'\n'"${msg}"
    text+="これは検証役の間に変わったことを示すだけで、検証役のせいとは限らない（ユーザーが同時に編集した場合もある）。"
    text+="自分では戻さず（git restore・git checkout・git reset を打たない）、違いの一覧をユーザーに示すこと。"
    if [ "$(printf '%s' "$input" | jq -r '.hook_event_name // ""' 2>/dev/null)" = Stop ]; then
      printf '%s\n' "$text" >&2
      exit 2
    fi
    jq -n --arg t "$text" '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $t}}'
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
