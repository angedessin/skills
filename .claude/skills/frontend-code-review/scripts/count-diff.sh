#!/usr/bin/env bash
# レビューの対象の差分の大きさを数える（frontend-code-review の Step 1）。
#
# Usage: count-diff.sh [--base <ref> [--worktree]] [-- <path>...]
#   指定なし            未コミットの変更（HEAD との差分）と未追跡のファイル
#   --base <ref>        <ref>...HEAD（merge-base からのコミット済みだけ）
#   --worktree          --base と一緒に。merge-base から作業ツリーまでと未追跡のファイル
#   -- <path>...        パスで絞る（未追跡のファイルも絞る）
#   GIT=<path>          使う git（PATH の先頭の git が動かない環境で、動く git を渡す）
#
# 出力: files・lines（追加・削除）・untracked（対象に入る未追跡のファイル）・dirstat（行数の割合）
# 終了コード: 0 = 数えた / 2 = 数えられない（理由は stderr）
set -u
set -o pipefail

die() {
  printf 'count-diff: %s\n' "$1" >&2
  exit 2
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
    --)
      shift
      break
      ;;
    *) die "知らない引数: $1" ;;
  esac
done
if [ "$worktree" = 1 ] && [ -z "$base" ]; then
  die "--worktree は --base と一緒に使う"
fi

# macOS の /usr/bin/git は sandbox の中でキャッシュの警告を stderr に出すので、成否は終了コードで見る
# command -v で先に確かめない: stat を拒み実行は許す sandbox では、動く git も「無い」と判定する
git=${GIT:-git}
"$git" rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "git が動かないか、git の作業ツリーの外にいる（動く git は GIT=<パス> で渡す）"
"$git" rev-parse --verify -q HEAD >/dev/null 2>&1 || die "HEAD が無い（コミットが 1 つも無い）"

with_untracked=1
if [ -z "$base" ]; then
  range=HEAD
else
  "$git" rev-parse --verify -q "${base}^{commit}" >/dev/null 2>&1 || die "ベースが見つからない: ${base}"
  if [ "$worktree" = 1 ]; then
    range=$("$git" merge-base "$base" HEAD 2>/dev/null) || die "merge-base が見つからない: ${base}"
  else
    range="${base}...HEAD"
    with_untracked=0
  fi
fi

stat=$("$git" diff --no-ext-diff --no-color --numstat "$range" -- "$@") || die "git diff が失敗した"
# バイナリは追加・削除が「-」になるので、ファイル数にだけ数える
totals=$(printf '%s\n' "$stat" | awk -F'\t' 'NF >= 3 { f++; if ($1 != "-") { a += $1; d += $2 } } END { printf "%d %d %d", f, a, d }')
files=${totals%% *}
rest=${totals#* }
added=${rest%% *}
deleted=${rest#* }

untracked_list=""
# bash 3.2 はコマンド置換の中の case の「)」を読み違えるので、型は [[ ]] で見る
nl=$'\n'
if [ "$with_untracked" = 1 ]; then
  # 名前に空白や改行があっても崩れないよう -z で読む。プロセス置換は sandbox で /dev/fd が使えず落ちるのでパイプにする
  ut=$("$git" ls-files --others --exclude-standard -z -- "$@" | {
    c=0
    a=0
    while IFS= read -r -d '' f; do
      c=$((c + 1))
      # 名前が「-」だと git が stdin（このループの入力）を読むので、./ を付けて stdin も塞ぐ
      n=$("$git" diff --no-index --no-ext-diff --numstat -- /dev/null "./$f" </dev/null 2>/dev/null | awk -F'\t' '$1 != "-" { s += $1 } END { print s + 0 }')
      a=$((a + n))
      # 改行を含む名前は 1 行に収めないと一覧と合計の行が崩れる
      if [[ $f == *"$nl"* ]]; then
        printf 'F %q\n' "$f"
      else
        printf 'F %s\n' "$f"
      fi
    done
    printf 'T %d %d\n' "$c" "$a"
  }) || die "git ls-files が失敗した"
  t=$(printf '%s\n' "$ut" | tail -n 1)
  case $t in
    "T "[0-9]*" "[0-9]*) t=${t#T } ;;
    *) die "未追跡のファイルを数えられない" ;;
  esac
  files=$((files + ${t%% *}))
  added=$((added + ${t#* }))
  untracked_list=$(printf '%s\n' "$ut" | sed -n 's/^F /  /p')
fi

printf 'files: %d\n' "$files"
printf 'lines: %d (+%d -%d)\n' "$((added + deleted))" "$added" "$deleted"
printf 'untracked:\n'
[ -n "$untracked_list" ] && printf '%s\n' "$untracked_list"
printf 'dirstat:\n'
"$git" diff --no-ext-diff --no-color --dirstat=lines,0 "$range" -- "$@" | sed 's/^ */  /' || die "git diff --dirstat が失敗した"
exit 0
