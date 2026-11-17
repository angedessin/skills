#!/usr/bin/env bash
# 再現に使う作業ツリーの写しか、空のディレクトリを $TMPDIR の下に作る（frontend-code-review の Step 3・review-verify）。
# 作る・移るの失敗を、出力の無い 0 以外の終了で知らせる。呼ぶ側は出たパスへ `cd <パス> && ...` で移る。
#
# Usage: make-copy.sh [--empty]
#   指定なし    リポジトリの根の写しを作り、写しの絶対パスを 1 行目に出す
#   --empty     空のディレクトリを作り、絶対パスを 1 行目に出す（一時リポジトリ用）
#   GIT=<path>                 使う git（PATH の先頭の git が動かない環境で、動く git を渡す）
#   MAKE_COPY_TIMEOUT=<秒>     複製の打ち切り（既定 60）
#
# 写しに入れないもの: .git（worktree では本物の gitdir を指すファイルで、写しの中の git が本物の索引に書く）と、
# sandbox が読ませない型（.env*・*.env・*.pem・*.key）。後者を除いたときは 2 行目に `excluded: <件数>` を出す。
# 終了コード: 0 = 作った / 2 = 作れない（理由は stderr。作りかけは消してある）
set -u
set -o pipefail

die() {
  printf 'make-copy: %s\n' "$1" >&2
  exit 2
}

empty=0
case "${1:-}" in
  '') ;;
  --empty) empty=1 ;;
  *) die "知らない引数: $1" ;;
esac
[ $# -le 1 ] || die "引数が多い"
TIMEOUT="${MAKE_COPY_TIMEOUT:-60}"
case "$TIMEOUT" in
  '' | *[!0-9]*) die "MAKE_COPY_TIMEOUT は秒の整数で渡す: ${TIMEOUT}" ;;
esac

# sandbox の中では $TMPDIR だけが書ける。/tmp に落とすと sandbox に拒まれ、cd の失敗の元になる
[ -n "${TMPDIR:-}" ] || die "TMPDIR が無い"
[ -d "$TMPDIR" ] && [ -w "$TMPDIR" ] || die "TMPDIR に書けない: ${TMPDIR}"
tmp_real=$(cd "$TMPDIR" && pwd -P) || die "TMPDIR に移れない: ${TMPDIR}"

# 古さは写しの外の印で測る: rsync -a は写し元の更新時刻を写しに引き継ぐ
for old in "$tmp_real"/review-copy.*; do
  [ -d "$old" ] || continue
  if [ -f "$old/made" ]; then
    [ -n "$(find "$old/made" -mmin +1440 2>/dev/null)" ] || continue
  else
    [ -n "$(find "$old" -maxdepth 0 -mmin +1440 2>/dev/null)" ] || continue
  fi
  rm -rf -- "$old"
done

root=""
if [ "$empty" = 0 ]; then
  # command -v で先に確かめない: stat を拒み実行は許す sandbox では、動く git も「無い」と判定する
  git=${GIT:-git}
  root=$("$git" rev-parse --show-toplevel 2>/dev/null) || die "git が動かないか、git の作業ツリーの外にいる（動く git は GIT=<パス> で渡す）"
  root=$(cd "$root" && pwd -P) || die "リポジトリの根に移れない: ${root}"
  case "$tmp_real/" in
    "$root"/*) die "TMPDIR がリポジトリの中を指している: ${TMPDIR}" ;;
  esac
fi

box=$(mktemp -d "$tmp_real/review-copy.XXXXXX") || die "一時ディレクトリを作れない: ${TMPDIR}"
ok=0
trap '[ "$ok" = 1 ] || rm -rf -- "$box"' EXIT
: >"$box/made" || die "印を書けない: ${box}"
dest="$box/tree"

if [ "$empty" = 1 ]; then
  mkdir "$dest" || die "ディレクトリを作れない: ${dest}"
  ok=1
  printf '%s\n' "$dest"
  exit 0
fi

# cp は型で除けず、sandbox の中では読めないファイルで必ず失敗する。rsync は除いた型を開かない
marker="$box/timed-out"
rsync -a --exclude=.git --exclude='.env*' --exclude='*.env' --exclude='*.pem' --exclude='*.key' \
  "$root/" "$dest/" </dev/null >"$box/log" 2>&1 &
pid=$!
(
  sleep "$TIMEOUT"
  : >"$marker"
  kill -TERM "$pid" 2>/dev/null
  sleep 2
  kill -KILL "$pid" 2>/dev/null
) </dev/null >/dev/null 2>&1 &
watcher=$!
wait "$pid" 2>/dev/null
rc=$?
kill -TERM "$watcher" 2>/dev/null
wait "$watcher" 2>/dev/null
[ -f "$marker" ] && die "複製を ${TIMEOUT} 秒で打ち切った（MAKE_COPY_TIMEOUT で延ばせる）"
[ "$rc" = 127 ] && die "rsync が無い"
[ "$rc" = 0 ] || die "複製に失敗した（rsync exit ${rc}）:"$'\n'"$(tail -5 "$box/log")"
[ -d "$dest" ] || die "写しができていない: ${dest}"
# 件数は rsync の出力でなく find で数える（openrsync と GNU rsync で出力の形が違う）
excluded=$(cd "$root" && find . -name .git -prune -o \( -name '.env*' -o -name '*.env' -o -name '*.pem' -o -name '*.key' \) ! -type d -print | wc -l | tr -d ' ')
rm -f -- "$box/log"
ok=1
printf '%s\n' "$dest"
[ "$excluded" = 0 ] || printf 'excluded: %s\n' "$excluded"
exit 0
