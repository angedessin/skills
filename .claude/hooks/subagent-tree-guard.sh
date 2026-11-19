#!/bin/bash
# 検証役（review-verify）の作業ツリーの見張り。開始時に控え、終了時に比べ、違えば 1 回だけ差し戻す。
# 事故を防ぐのではなく、起きた後に気づくための仕組み（検証役の Bash は残すため）。
#
# Usage: subagent-tree-guard.sh start|stop|report [--mirror-gitdir]   （入力は hook の JSON を stdin で）
#   start  SubagentStart: リポジトリの根と中身を控える。控えがあれば上書きしない（途中の再開で汚れた状態を控え直さない）。
#          ただし前の実行が same・returned で終わっていれば、控え直して新しい実行として扱う（その間の親やユーザーの書き込みを数えない）
#   stop   SubagentStop:  控えた根を今と比べ、結果を記録する。違えば 1 回目だけ exit 2 で差し戻す。
#          一度終わった検証役が止まり直したとき（背景の作業の終わりなど）は差し戻さず、late-diff として記録だけする
#   report PostToolUse(Agent)・親の Stop: その session の記録を、結果が変わるたびに 1 回ずつ親に知らせる。
#          確かめていないものは session ごとに 1 回。PostToolUse は additionalContext で、Stop は exit 2 で知らせる
#          （背景で起動した agent は PostToolUse が起動の直後に来るので、親の Stop でも拾う）
#   --mirror-gitdir: stop の結果を、見張ったリポジトリの .git/tree-guard.log にも 1 行ずつ足す。
#          評価（claude plugin eval）の grader は TMPDIR を読めず、ワークスペースのファイルしか見られないため。普段は付けない
# 記録: ${TMPDIR}/claude-tree-guard/<session_id>/<agent_id>/ の root・state・result・diff・rejected・reported
#   result: same（同じ）・differs（違い、差し戻した）・returned（差し戻しの後に戻った）・not-returned（差し戻しの後も違う）・
#           late-diff（終わった後に止まり直したときの違い）・unreadable（終了時に状態を読めない）・unchecked（控えが無い）
# git・jq が無い・リポジトリの外では素通しする（ほかの hook と同じ）。

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

# パスの中身を表す値。ふつうのファイルは呼び出し側でまとめてハッシュにする（1 ファイルごとに git を起こさない）
# 入れ子のリポジトリ・サブモジュール（ディレクトリ）と、指す先の無いリンクは hash-object が失敗し、まとめた残りまで落とすので別に扱う
kind_of() { # $1 = 根, $2 = パス。標準出力に値を出し、ふつうのファイルなら何も出さずに 1 を返す
  local f="$1/${2%/}"
  if [ -L "$f" ]; then
    printf 'link:%s' "$(readlink "$f")"
  elif [ -d "$f" ]; then
    printf 'dir:%s:%s' "$(git -C "$f" rev-parse -q --verify HEAD 2>/dev/null || echo none)" \
      "$(git -C "$f" --no-optional-locks status --porcelain 2>/dev/null | git hash-object --stdin)"
  elif [ -f "$f" ]; then
    return 1
  elif [ -e "$f" ]; then
    printf 'other'
  else
    printf 'deleted'
  fi
}

# 1 行 1 項目: 種類 TAB 鍵 TAB 値。H=HEAD・R=ref・W=HEAD と違う追跡ファイルの中身・I=索引・U=未追跡のファイルの中身
# git status は使わない: 既に変更のあるファイルをさらに書き換えても行が変わらない
state() {
  local r=$1 head tree p v i n
  local g=(git -C "$r" --no-optional-locks -c core.quotepath=false)
  head=$("${g[@]}" rev-parse -q --verify HEAD 2>/dev/null) || head=none
  printf 'H\tHEAD\t%s\n' "$head"
  # リモートの ref は見ない（IDE の自動 fetch で変わる）
  "${g[@]}" for-each-ref --format='R%09%(refname)%09%(objectname)' refs/heads refs/tags refs/stash || return 1
  tree=$head
  [ "$head" = none ] && { tree=$("${g[@]}" hash-object -t tree /dev/null) || return 1; }
  "${g[@]}" diff --no-ext-diff --no-renames --cached --raw --no-abbrev "$tree" 2>/dev/null |
    awk -F'\t' '{ print "I\t" $2 "\t" $1 }'

  local kinds=() paths=() files=()
  # 未追跡はディレクトリに畳まず 1 ファイルずつ（畳むと、下に足しても行が変わらない）
  while IFS= read -r -d '' p; do kinds+=(W) && paths+=("$p"); done < <("${g[@]}" diff --no-ext-diff --no-renames --name-only -z "$tree" 2>/dev/null)
  while IFS= read -r -d '' p; do kinds+=(U) && paths+=("$p"); done < <("${g[@]}" ls-files --others --exclude-standard -z 2>/dev/null)
  n=${#paths[@]}
  local hashes=()
  for ((i = 0; i < n; i++)); do
    p=${paths[$i]}
    case "$p" in *$'\n'*) continue ;; esac # 改行を含む名前は --stdin-paths に渡せない
    kind_of "$r" "$p" >/dev/null || files+=("$p")
  done
  if [ ${#files[@]} -gt 0 ]; then
    while IFS= read -r v; do hashes+=("$v"); done < <(printf '%s\n' "${files[@]}" | "${g[@]}" hash-object --no-filters --stdin-paths 2>/dev/null)
    [ ${#hashes[@]} = ${#files[@]} ] || return 1
  fi
  local j=0
  for ((i = 0; i < n; i++)); do
    p=${paths[$i]}
    case "$p" in *$'\n'*) continue ;; esac
    if v=$(kind_of "$r" "$p"); then :; else
      v=${hashes[$j]}
      j=$((j + 1))
    fi
    printf '%s\t%s\t%s\n' "${kinds[$i]}" "${p%/}" "$v"
  done
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
    unchecked | unreadable) echo "TREE-GUARD-UNCHECKED $1" ;;
    same | returned | not-returned | differs) echo "TREE-GUARD-CHECKED $1" ;;
    late-diff) echo "TREE-GUARD-LATE $1" ;;
  esac >>"$gd/tree-guard.log"
  case "$1" in
    differs | not-returned | returned) echo "TREE-GUARD-DIFF $1" >>"$gd/tree-guard.log" ;;
  esac
}

snapshot() { # 控えを取る（失敗したら控えを残さない）
  local tmp="$dir/state.tmp"
  if state "$root" >"$tmp" 2>/dev/null; then
    printf '%s\n' "$root" >"$dir/root"
    mv "$tmp" "$dir/state"
  else
    rm -f "$tmp" "$dir/state"
  fi
}

case "$mode" in
  start)
    [ -n "$aid" ] && [ -n "$cwd" ] || exit 0
    if [ -f "$dir/state" ]; then
      # 前の実行がきれいに終わっていれば、新しい実行として控え直す。それ以外（途中・違いが残った）は控えを保つ
      case "$(cat "$dir/result" 2>/dev/null)" in
        same | returned) ;;
        *) exit 0 ;;
      esac
      root=$(cat "$dir/root")
      rm -f "$dir/result" "$dir/rejected" "$dir/reported" "$dir/diff"
      snapshot
      exit 0
    fi
    root=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null) || exit 0
    [ -n "$root" ] || exit 0
    # 古い session の記録を消す（1 日より前）
    [ -d "$base" ] && find "$base" -mindepth 1 -maxdepth 1 -type d -mmin +1440 -exec rm -rf {} + 2>/dev/null
    mkdir -p "$dir" || exit 0
    snapshot
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
    prev=$(cat "$dir/result" 2>/dev/null)
    now="$dir/state.now"
    if ! state "$root" >"$now" 2>/dev/null; then
      rm -f "$now"
      record unreadable
      echo "subagent-tree-guard: ${root} の今の状態を読めないので、比べていない" >&2
      exit 0
    fi
    diff_text=$(describe "$root" "$dir/state" "$now")
    rm -f "$now"
    case "$prev" in
      same | returned | not-returned | late-diff)
        # 一度終わった後に止まり直した。間に親やユーザーが書いた分も入るので、差し戻さずに知らせるだけにする
        [ -n "$diff_text" ] || exit 0
        [ "$diff_text" = "$(cat "$dir/diff" 2>/dev/null)" ] && exit 0
        printf '%s\n' "$diff_text" >"$dir/diff"
        record late-diff
        exit 0
        ;;
    esac
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
      echo "戻してよいのは、一覧の「未追跡のファイルが増えた」のうち自分が作ったものを消すことだけ。"
      echo "追跡ファイルの書き換え・ステージ・コミット・ref は戻さないこと（git restore・git checkout・git reset は、開始前からあったユーザーの変更まで消す）。覚えのない違いにも触らないこと。"
      echo "消したものと、戻さずに残したものを、返す結果の先頭に書くこと。"
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
      [ -f "$d/result" ] || continue
      r=$(cat "$d/result")
      # 同じ結果は 2 回知らせない。結果が変われば（差し戻し → 戻らなかった など）もう一度知らせる
      [ "$(cat "$d/reported" 2>/dev/null)" = "$r" ] && continue
      id=${d##*/}
      root_of=$(cat "$d/root" 2>/dev/null)
      list="$(sed 's/^/  /' "$d/diff" 2>/dev/null | head -30)"
      case "$r" in
        not-returned) msg+="- 検証役（${id}）の間に ${root_of} の作業ツリーが変わり、差し戻した後も違いが残っている:"$'\n'"${list}"$'\n' ;;
        returned) msg+="- 検証役（${id}）の間に ${root_of} の作業ツリーが変わったが、差し戻した後に元に戻った。戻る前の違い:"$'\n'"${list}"$'\n' ;;
        differs) msg+="- 検証役（${id}）の間に ${root_of} の作業ツリーが変わり差し戻したが、検証役がまだ止まり直していない（中断などで結果が出ないこともある）。差し戻した時点の違い:"$'\n'"${list}"$'\n' ;;
        late-diff) msg+="- 検証役（${id}）が一度終わった後に止まり直したとき、${root_of} の作業ツリーが開始時と違った。親やユーザーの書き込みの可能性が高いので差し戻していない。違い:"$'\n'"${list}"$'\n' ;;
        unreadable)
          msg+="- 検証役（${id}）の終了時に ${root_of} の作業ツリーの状態を読めず、比べられなかった。レビューの報告の「レビューできなかったもの」に書くこと"$'\n'
          [ -n "$list" ] && msg+="  差し戻した時点の違い:"$'\n'"${list}"$'\n'
          ;;
        unchecked) unchecked=1 ;;
        *) continue ;; # same は知らせない
      esac
      printf '%s' "$r" >"$d/reported"
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
