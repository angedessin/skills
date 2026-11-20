#!/usr/bin/env bash
# 新しく書いたテストを、変える前のコードで流す（frontend-code-review の Step 3）。
# 新しいテストは「変える前の版に同じファイル・同じ名前で通るテストが無いもの」。名前を変えずに本文だけ変えたテストは対象にならない。
#
# Usage: run-tests-on-base.sh [--base <ref> [--worktree]] [-- <path>...]
#   指定なし            未コミットの変更と未追跡のテストを、HEAD のコードで流す
#   --base <ref>        <ref> との merge-base から HEAD までにコミットしたテストを、merge-base のコードで流す
#   --worktree          --base と一緒に。未コミットの変更と未追跡のテストも足す
#   -- <path>...        パスで絞る
#   GIT=<path>          使う git（PATH の先頭の git が動かない環境で、動く git を渡す）
#   JQ=<path>           使う jq。無ければ PATH の jq を使い、それが起動できなければ /usr/bin/jq を試す
#   RUN_TESTS_ON_BASE_TIMEOUT=<秒>  vitest の打ち切り（既定 90。2 回の起動の合計）
#
# 出力: tests（対象のテストファイルの数）・passed-on-base（変える前でも通った新しいテスト。<ファイル> > <名前>）・
#       failed-on-base（変える前に落ちたテストの数）・broken-on-base（読み込めずにファイルごと落ちたテストファイル）
# 終了コード: 0 = 判定した / 2 = 判定できない（理由は stderr）
set -u
set -o pipefail

die() {
  printf 'run-tests-on-base: %s\n' "$1" >&2
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
# Bash ツールの既定の打ち切り（120 秒）より短く保ち、こちらの「打ち切った」で理由を返す
TIMEOUT="${RUN_TESTS_ON_BASE_TIMEOUT:-90}"
case "$TIMEOUT" in
  '' | *[!0-9]*) die "RUN_TESTS_ON_BASE_TIMEOUT は秒の整数で渡す: ${TIMEOUT}" ;;
esac

# command -v で先に確かめない: stat を拒み実行は許す sandbox では、動く git も「無い」と判定する
git=${GIT:-git}
"$git" rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "git が動かないか、git の作業ツリーの外にいる（動く git は GIT=<パス> で渡す）"
"$git" rev-parse --verify -q HEAD >/dev/null 2>&1 || die "HEAD が無い（コミットが 1 つも無い）"
root=$("$git" rev-parse --show-toplevel 2>/dev/null) || die "リポジトリの根が分からない"
cd "$root" || die "リポジトリの根に移れない: ${root}"

if [ -z "$base" ]; then
  old=$("$git" rev-parse HEAD)
  with_wt=1
else
  "$git" rev-parse --verify -q "${base}^{commit}" >/dev/null 2>&1 || die "ベースが見つからない: ${base}"
  old=$("$git" merge-base "$base" HEAD 2>/dev/null) || die "merge-base が見つからない: ${base}"
  with_wt=$worktree
fi

# テストファイルの定義は SKILL.md の Step 2 と同じ。E2E はブラウザで流すので除く
is_test() {
  case "$1" in
    e2e/* | */e2e/*) return 1 ;;
    *.d.ts | *.d.mts | *.d.cts) return 1 ;;
    *.ts | *.tsx | *.js | *.jsx | *.mts | *.cts | *.mjs | *.cjs | *.vue | *.svelte) ;;
    *) return 1 ;;
  esac
  case "$1" in
    *.test.* | *.spec.* | __tests__/* | */__tests__/* | tests/* | */tests/*) return 0 ;;
  esac
  return 1
}

now_paths=()
before_paths=()
add() { # $1 = 今のパス, $2 = ベースのパス（新しいファイルなら空）
  is_test "$1" || return 0
  now_paths+=("$1")
  before_paths+=("$2")
}

work=$(mktemp -d "${TMPDIR:-/tmp}/run-tests-on-base.XXXXXX") || die "一時ディレクトリを作れない"
trap 'rm -rf "$work"' EXIT

if [ "$with_wt" = 1 ]; then
  # 未追跡のファイルを一時的な索引に登録した形にして、ステージしない mv も改名として検出させる（本物の索引は変えない）
  index=$("$git" rev-parse --git-path index) || die "索引の場所が分からない"
  export GIT_INDEX_FILE="$work/index"
  if [ -f "$index" ]; then cp -- "$index" "$GIT_INDEX_FILE" || die "索引を写せない"; fi
  "$git" ls-files --others --exclude-standard -z -- "$@" >"$work/untracked" || die "git ls-files が失敗した"
  if [ -s "$work/untracked" ]; then
    "$git" add -N --pathspec-from-file="$work/untracked" --pathspec-file-nul || die "未追跡のファイルを一時的な索引に登録できない"
  fi
  diff_args=("$old")
else
  diff_args=("$old" HEAD)
fi
# プロセス置換は sandbox で /dev/fd が使えず落ちるので、ファイルに書いてから読む
"$git" diff --no-ext-diff --name-status -z -M --diff-filter=AMR "${diff_args[@]}" -- "$@" >"$work/changed" || die "git diff が失敗した"
unset GIT_INDEX_FILE
# -z の出力は「状態 NUL パス NUL」（改名は「状態 NUL 元 NUL 先 NUL」）
while IFS= read -r -d '' st; do
  case "$st" in
    R*)
      IFS= read -r -d '' from
      IFS= read -r -d '' to
      add "$to" "$from"
      ;;
    M*)
      IFS= read -r -d '' p
      add "$p" "$p"
      ;;
    *)
      IFS= read -r -d '' p
      add "$p" ""
      ;;
  esac
done <"$work/changed"

total=${#now_paths[@]}
if [ "$total" -eq 0 ]; then
  printf 'tests: 0\npassed-on-base: 0\nfailed-on-base: 0\nbroken-on-base: 0\n'
  exit 0
fi

VITEST="$root/node_modules/.bin/vitest"
[ -x "$VITEST" ] || die "vitest が無い: node_modules/.bin/vitest（依存を入れてから呼ぶ。vitest がサブパッケージにだけあるモノレポは対象外）"
# 起動の失敗（127 以外）は「動かない」と分ける: sandbox がライブラリの読み込みを拒むと jq は abort する（134）
jq_bin=${JQ:-jq}
jq_err=$("$jq_bin" --version 2>&1 >/dev/null)
jq_rc=$?
if [ "$jq_rc" -ne 0 ] && [ -z "${JQ:-}" ] && [ "$jq_rc" -ne 127 ] && /usr/bin/jq --version >/dev/null 2>&1; then
  jq_bin=/usr/bin/jq
  jq_rc=0
fi
if [ "$jq_rc" -eq 127 ]; then
  die "jq が無い"
elif [ "$jq_rc" -ne 0 ]; then
  first=""
  while IFS= read -r line; do
    [ -n "${line//[[:space:]]/}" ] && { first=$line; break; }
  done <<<"$jq_err"
  die "jq が動かない: ${jq_bin}（exit ${jq_rc}）: ${first}"
fi

copy="$work/base"
mkdir "$copy" || die "一時ディレクトリを作れない"
"$git" archive "$old" | tar -x -C "$copy" || die "変える前のコードを展開できない: ${old}"
# node_modules は中身ごとにリンクする: まるごとリンクすると vitest のキャッシュ（node_modules/.vite）が本物の側に書かれる
if [ ! -e "$copy/node_modules" ]; then
  mkdir "$copy/node_modules" || die "node_modules を借りられない"
  for e in "$root/node_modules"/* "$root/node_modules"/.[!.]*; do
    [ -e "$e" ] || continue
    [ "${e##*/}" = .vite ] && continue
    ln -s "$e" "$copy/node_modules/${e##*/}" || die "node_modules を借りられない"
  done
fi
copy_real=$(cd "$copy" && pwd -P) || die "一時ディレクトリに移れない"
json="$work/result.json"
log="$work/vitest.log"
marker="$work/timed-out"
start=$SECONDS

run_vitest() { # 引数 = 写しの中のテストのパス
  local remain=$((TIMEOUT - (SECONDS - start)))
  [ "$remain" -gt 0 ] || die "vitest を ${TIMEOUT} 秒で打ち切った（RUN_TESTS_ON_BASE_TIMEOUT で延ばせる）"
  : >"$json"
  rm -f "$marker"
  set -m
  # カバレッジを切る: 設定でしきい値を有効にしていると、一部のテストだけを流すと割って 0 以外で終わる
  # CI=true: CI でない vitest は無いスナップショットを書いて通すので、新しいスナップショットのテストが変える前でも通ってしまう
  (cd "$copy" && CI=true exec "$VITEST" run "$@" --coverage.enabled=false --reporter=json --outputFile="$json") </dev/null >"$log" 2>&1 &
  local pid=$!
  (
    sleep "$remain"
    : >"$marker"
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null
    sleep 2
    kill -KILL -- "-$pid" 2>/dev/null
  ) </dev/null >/dev/null 2>&1 &
  local watcher=$!
  set +m
  wait "$pid" 2>/dev/null
  local rc=$?
  kill -TERM -- "-$watcher" 2>/dev/null || kill -TERM "$watcher" 2>/dev/null
  wait "$watcher" 2>/dev/null
  [ -f "$marker" ] && die "vitest を ${TIMEOUT} 秒で打ち切った（RUN_TESTS_ON_BASE_TIMEOUT で延ばせる）"
  # 件数が無い = 道具の故障（node が無い・設定のエラー）。テストの失敗とは分ける
  [ -n "$("$jq_bin" -r '.numTotalTestSuites | numbers' "$json" 2>/dev/null)" ] ||
    die "vitest が結果を返さなかった（exit ${rc}）:"$'\n'"$(tail -5 "$log")"
}

# <写しの中のパス> NUL <状態> NUL <テストの名前> NUL を $work/results に書く。ファイルごと落ちたもの（import のエラーなど）は名前を空にする
results() {
  "$jq_bin" -j --arg a "$copy_real/" --arg b "$copy/" '.testResults[]? |
    (.name | ltrimstr($a) | ltrimstr($b)) as $f |
    if ((.assertionResults // []) | length) == 0 and .status == "failed" then "\($f)\u0000broken\u0000\u0000"
    else (.assertionResults[]? | "\($f)\u0000\(.status)\u0000\(.fullName)\u0000") end' "$json" >"$work/results" ||
    die "vitest の結果を読めない"
}

# 鍵は配列に持って比べる: bash 3.2 の %q は日本語をバイトごとに崩し、grep が読めない
SEP=$'\001'
pre=()
in_pre() {
  local k
  for k in ${pre[@]+"${pre[@]}"}; do [ "$k" = "$1" ] && return 0; done
  return 1
}

befores=()
for i in "${!now_paths[@]}"; do
  [ -n "${before_paths[$i]}" ] && befores+=("${before_paths[$i]}")
done
if [ "${#befores[@]}" -gt 0 ]; then
  # 変えたテストファイルのベースの版を先に流し、前から通っていたテストを控える（新しいテストだけを報告するため）
  run_vitest "${befores[@]}"
  results
  while IFS= read -r -d '' f && IFS= read -r -d '' st && IFS= read -r -d '' name; do
    [ "$st" = passed ] || continue
    for i in "${!now_paths[@]}"; do
      [ "${before_paths[$i]}" = "$f" ] && pre+=("${now_paths[$i]}$SEP$name")
    done
  done <"$work/results"
fi

put() { # $1 = パス。今の版を写しに置く
  mkdir -p "$copy/$(dirname "$1")" || die "テストを写しに置けない: ${1}"
  if [ "$with_wt" = 1 ]; then
    cp -- "$1" "$copy/$1" || die "テストを写しに置けない: ${1}"
  else
    "$git" show "HEAD:$1" >"$copy/$1" || die "テストを写しに置けない: ${1}"
  fi
}
for p in "${now_paths[@]}"; do put "$p"; done
run_vitest "${now_paths[@]}"

nl=$'\n'
show() { # 改行を含む名前は 1 行に収めないと一覧が崩れる
  if [[ $1 == *"$nl"* ]]; then printf '%q' "$1"; else printf '%s' "$1"; fi
}

passed_list=""
passed=0
failed=0
broken_list=""
broken=0
results
while IFS= read -r -d '' f && IFS= read -r -d '' st && IFS= read -r -d '' name; do
  # vitest run のフィルタは部分一致で、渡していない似た名前のテストも流れる
  hit=0
  for p in "${now_paths[@]}"; do [ "$p" = "$f" ] && hit=1; done
  [ "$hit" = 1 ] || continue
  case "$st" in
    passed)
      in_pre "$f$SEP$name" && continue
      passed=$((passed + 1))
      passed_list="$passed_list  $(show "$f") > $(show "$name")$nl"
      ;;
    failed) failed=$((failed + 1)) ;;
    broken)
      broken=$((broken + 1))
      broken_list="$broken_list  $(show "$f")$nl"
      ;;
  esac
done <"$work/results"

printf 'tests: %d\n' "$total"
printf 'passed-on-base: %d\n' "$passed"
[ -n "$passed_list" ] && printf '%s' "$passed_list" | sort
printf 'failed-on-base: %d\n' "$failed"
printf 'broken-on-base: %d\n' "$broken"
[ -n "$broken_list" ] && printf '%s' "$broken_list" | sort
exit 0
