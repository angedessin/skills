#!/bin/bash
# Stop hook: テストのゲート。変えた実装ファイルに関係するテストが無い・落ちる・テストを弱めたときに exit 2 で差し戻す。
# 対象・免除のファイルの書き方・差し戻す条件は README の「hook と設定」。
# stop_hook_active では緩めない（逃げ道は免除のファイル。連続の差し戻しは Claude Code の上限に任せる）。

command -v jq >/dev/null 2>&1 || exit 0
input=$(cat)

cwd=$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)
[ -n "$cwd" ] || cwd="${CLAUDE_PROJECT_DIR:-$PWD}"
ROOT=$(cd "$cwd" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null)
[ -n "$ROOT" ] || exit 0
VITEST="$ROOT/node_modules/.bin/vitest"
[ -x "$VITEST" ] || exit 0
cd "$ROOT" || exit 0

base=""
if git rev-parse --verify -q origin/HEAD >/dev/null 2>&1; then
  base=$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null)
else
  for b in "$(git config init.defaultBranch 2>/dev/null)" main master; do
    [ -n "$b" ] && git rev-parse --verify -q "refs/heads/$b" >/dev/null 2>&1 && base=$b && break
  done
fi
from=""
if git rev-parse --verify -q HEAD >/dev/null 2>&1; then
  from=HEAD
  current=$(git symbolic-ref --short -q HEAD 2>/dev/null)
  if [ -n "$base" ] && [ "$current" != "${base#origin/}" ]; then
    mb=$(git merge-base "$base" HEAD 2>/dev/null) && [ -n "$mb" ] && from=$mb
  fi
fi
changed=$(
  {
    [ -n "$from" ] && git -c core.quotepath=false diff --name-only --diff-filter=d "$from"
    git -c core.quotepath=false ls-files --others --exclude-standard
  } 2>/dev/null | sort -u
)

has_code_ext() {
  case "$1" in
    *.d.ts | *.d.mts | *.d.cts) return 1 ;;
    *.ts | *.tsx | *.js | *.jsx | *.mts | *.cts | *.mjs | *.cjs | *.vue | *.svelte) return 0 ;;
  esac
  return 1
}
is_impl() {
  has_code_ext "$1" || return 1
  case "${1##*/}" in .*) return 1 ;; esac # .eslintrc.cjs などの設定
  case "$1" in
    *.config.* | *.stories.*) return 1 ;;
    *.test.* | *.spec.*) return 1 ;;
    __tests__/* | */__tests__/* | tests/* | */tests/* | e2e/* | */e2e/*) return 1 ;;
  esac
  return 0
}
norm_path() { # 結果は NP に入れる（行ごとに $(...) のサブシェルを起こさないため）
  NP=$1
  NP=${NP#\`}
  NP=${NP%\`}
  NP=${NP#./}
}

ex_files=()
for d in .steering/*/; do
  [ -d "$d" ] || continue
  name=$(basename "$d")
  [ "$name" = "archived" ] && continue
  ex_files+=(".steering/$name/test-exemptions.md")
done
[ ${#ex_files[@]} -eq 0 ] && ex_files=(".steering/test-exemptions.md")

exempt_paths() { # $1 = 節の名前
  local f line on path reason
  for f in "${ex_files[@]}"; do
    [ -f "$f" ] || continue
    on=0
    while IFS= read -r line || [ -n "$line" ]; do
      case "$line" in
        "## "*)
          if [ "$line" = "## $1" ]; then on=1; else on=0; fi
          continue
          ;;
      esac
      [ "$on" = 1 ] || continue
      case "$line" in "- "*" — "*) ;; *) continue ;; esac
      line=${line#- }
      path=${line%% — *}
      reason=${line#* — }
      norm_path "$path"
      [ -n "${reason//[[:space:]]/}" ] && printf '%s\n' "$NP"
    done <"$f"
  done
}
exempt_none=$(exempt_paths "テスト不要")
exempt_fail=$(exempt_paths "失敗を残す")
listed() { printf '%s\n' "$2" | grep -qxF -- "$1"; }

is_test() {
  has_code_ext "$1" || return 1
  case "$1" in
    *.test.* | *.spec.* | __tests__/* | */__tests__/* | tests/* | */tests/* | e2e/* | */e2e/*) return 0 ;;
  esac
  return 1
}

targets=()
while IFS= read -r f; do
  [ -n "$f" ] && is_impl "$f" && targets+=("$f")
done <<<"$changed"
# 改名は古いパスの版と比べる（新しいパスはベースに無く、0 件と比べて弱めた判定をすり抜けるため）
tests_changed=()
renames=""
while IFS=$'\t' read -r st a b; do
  case "$st" in
    R*)
      if is_test "$b"; then
        tests_changed+=("$b")
        renames="$renames$b"$'\t'"$a"$'\n'
      elif is_test "$a"; then
        tests_changed+=("$a") # テストでない名前への改名は、テストを消したとみなす
      fi
      ;;
    ?*) is_test "$a" && tests_changed+=("$a") ;;
  esac
done < <([ -n "$from" ] && git -c core.quotepath=false diff --name-status -M "$from" 2>/dev/null)
while IFS= read -r f; do
  [ -n "$f" ] && is_test "$f" && tests_changed+=("$f")
done < <(git -c core.quotepath=false ls-files --others --exclude-standard 2>/dev/null)
renamed_from() { printf '%s' "$renames" | awk -F'\t' -v n="$1" '$1 == n { print $2; exit }'; }
[ ${#targets[@]} -eq 0 ] && [ ${#tests_changed[@]} -eq 0 ] && exit 0

# 同じ差分で通った後は流さない。免除のファイルもハッシュに入れる（.steering/ を gitignore していても判定し直すため）
session=$(printf '%s' "$input" | jq -r '.session_id // "nosession"' 2>/dev/null | tr -c 'A-Za-z0-9_-' '_')
STATE_DIR="${TMPDIR:-/tmp}/claude-stop-test-gate"
STATE="$STATE_DIR/${session:-nosession}"
hash=$(
  {
    printf '%s\n' "$ROOT"
    [ -n "$from" ] && git diff "$from"
    git ls-files --others --exclude-standard -z | while IFS= read -r -d '' u; do
      printf '%s\n' "$u"
      cat -- "$u"
    done
    for f in "${ex_files[@]}"; do [ -f "$f" ] && cat -- "$f"; done
  } 2>/dev/null | cksum
)
[ -f "$STATE" ] && [ "$(cat "$STATE")" = "$hash" ] && exit 0

EXPECT_RE='(^|[^A-Za-z0-9_$.])expect(\.(soft|poll))?[[:space:]]*\('
SKIP_RE='(^|[^A-Za-z0-9_$.])((it|test|describe|suite|bench)(\.[A-Za-z]+)*\.(skip|skipIf|only|todo)([^A-Za-z0-9_$]|$)|(xit|xtest|xdescribe|fit|fdescribe)[[:space:]]*\()'
count() { grep -oE -- "$1" | wc -l | tr -d ' '; }
exempt_weak=$(exempt_paths "テストを弱める")
weakened=""
for t in "${tests_changed[@]}"; do
  listed "$t" "$exempt_weak" && continue
  src=$(renamed_from "$t")
  shown=$t
  [ -n "$src" ] && shown="${src} → ${t}"
  [ -n "$src" ] || src=$t
  old=""
  [ -n "$from" ] && old=$(git show "$from:$src" 2>/dev/null)
  new=""
  [ -f "$t" ] && new=$(cat -- "$t")
  oe=$(printf '%s\n' "$old" | count "$EXPECT_RE")
  ne=$(printf '%s\n' "$new" | count "$EXPECT_RE")
  os=$(printf '%s\n' "$old" | count "$SKIP_RE")
  ns=$(printf '%s\n' "$new" | count "$SKIP_RE")
  why=""
  [ "$ne" -lt "$oe" ] && why="expect が ${oe} → ${ne}"
  [ "$ns" -gt "$os" ] && why="${why:+${why}、}skip・only・todo が ${os} → ${ns}"
  [ -n "$why" ] && [ ! -f "$t" ] && why="${why}。ファイルを消した"
  [ -n "$why" ] && weakened="$weakened  - ${shown}（${why}）"$'\n'
done

# タスクの外の免除は閉じても消えないので、載ったファイルが変わったら見直しを促す
GLOBAL_EX=".steering/test-exemptions.md"
stale=""
if [ "${ex_files[*]}" = "$GLOBAL_EX" ] && [ -f "$GLOBAL_EX" ]; then
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    while IFS= read -r line || [ -n "$line" ]; do
      case "$line" in "- "*" — "*) ;; *) continue ;; esac
      p=${line#- }
      norm_path "${p%% — *}"
      [ "$NP" = "$f" ] && stale="$stale  ${line}"$'\n'
    done <"$GLOBAL_EX"
  done <<<"$changed"
fi
if [ -n "$stale" ]; then
  {
    echo "test gate: 次のファイルは ${GLOBAL_EX} で免除したまま変わりました（差し戻しません）。免除がまだ要るか確かめ、要らなければ行を消してください:"
    printf '%s' "$stale"
  } >&2
fi

# hook の timeout（180）より 10 秒以上短く保つ（check_settings.py が検査する）。時間切れの hook は差し戻さずに終わるため
TIMEOUT="${STOP_TEST_GATE_TIMEOUT:-150}"
work=$(mktemp -d "${TMPDIR:-/tmp}/stop-test-gate.XXXXXX") || exit 0
trap 'rm -rf "$work"' EXIT
json="$work/result.json"
log="$work/vitest.log"
marker="$work/timed-out"
REAL_ROOT=$(pwd -P)

run_vitest() { # $1 = 残りの秒数, 残り = vitest の引数。rc と timed を決める
  local secs=$1
  shift
  : >"$json" # 道具の故障で json が書かれないとき、前のファイルの結果を読まないため
  rm -f "$marker"
  set -m
  # カバレッジを切る: 設定でしきい値を有効にしていると、一部のテストだけを流すと割って 0 以外で終わる
  "$VITEST" "$@" --coverage.enabled=false --reporter=json --outputFile="$json" </dev/null >"$log" 2>&1 &
  local pid=$!
  (
    sleep "$secs"
    : >"$marker"
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null
    sleep 2
    kill -KILL -- "-$pid" 2>/dev/null
  ) </dev/null >/dev/null 2>&1 &
  local watcher=$!
  set +m
  wait "$pid" 2>/dev/null
  rc=$?
  kill -TERM -- "-$watcher" 2>/dev/null || kill -TERM "$watcher" 2>/dev/null
  wait "$watcher" 2>/dev/null
  if [ -f "$marker" ]; then timed=1; else timed=0; fi
}

start=$SECONDS
missing=""
failures=""
broken=""
unjudged=""
ran=""

judge() { # $1 = 対象の表示, $2 = 落ちたテストに添える文, $3 = 差し戻しの対象にするテストの一覧（空なら全部）
  local n name rel failed_any=0
  n=$(jq -r '.numTotalTestSuites | numbers' "$json" 2>/dev/null)
  if [ -z "$n" ]; then # 件数が無い = 道具の故障（node が無い・設定のエラー）。テストの失敗と区別して差し戻さない
    broken="$broken  - ${1}（exit ${rc}）:"$'\n'"$(tail -5 "$log" | sed 's/^/      /')"$'\n'
    return 1
  fi
  ran="$ran$(jq -r --arg a "$REAL_ROOT/" --arg b "$ROOT/" '.testResults[]?.name | ltrimstr($a) | ltrimstr($b)' "$json" 2>/dev/null)"$'\n'
  [ "$n" -eq 0 ] && return 0
  while IFS= read -r name; do
    [ -n "$name" ] || continue
    failed_any=1
    rel=${name#"$REAL_ROOT"/}
    rel=${rel#"$ROOT"/}
    listed "$rel" "$exempt_fail" && continue
    # vitest run のフィルタは部分一致で、渡していない似た名前のテストも流れる
    [ -n "${3:-}" ] && ! listed "$rel" "$3" && continue
    failures="$failures  - ${rel}（${2}）"$'\n'"$(
      jq -r --arg n "$name" '.testResults[] | select(.name == $n) |
        ([.assertionResults[]? | select(.status == "failed") | "      \(.fullName): \((.failureMessages[0] // "") | split("\n")[0])"]
         + (if (.message // "") != "" then ["      \(.message | split("\n")[0])"] else [] end)) | .[]' "$json" 2>/dev/null | tail -20
    )"$'\n'
  done < <(jq -r '.testResults[]? | select(.status == "failed") | .name' "$json" 2>/dev/null)
  # 落ちたファイルが無いのに 0 以外（Unhandled Errors など）
  if [ "$rc" -ne 0 ] && [ "$failed_any" = 0 ]; then
    failures="$failures  - ${1}: vitest が失敗で終わりました（exit ${rc}。落ちたテストファイルは無い。Unhandled Errors など）:"$'\n'"$(tail -5 "$log" | sed 's/^/      /')"$'\n'
  fi
  return 0
}

# 実装ファイルごとに流し、件数で有無を見る（0 件でも終了コードは 0 で、まとめて渡すとどのファイルに無いかが分からない）
i=0
while [ $i -lt ${#targets[@]} ]; do
  f=${targets[$i]}
  i=$((i + 1))
  listed "$f" "$exempt_fail" && continue
  remain=$((TIMEOUT - (SECONDS - start)))
  timed=1
  [ "$remain" -gt 0 ] && run_vitest "$remain" related "$f" --run
  if [ "$timed" = 1 ]; then
    unjudged="$unjudged  - $f"$'\n'
    while [ $i -lt ${#targets[@]} ]; do
      listed "${targets[$i]}" "$exempt_fail" || unjudged="$unjudged  - ${targets[$i]}"$'\n'
      i=$((i + 1))
    done
    break
  fi
  judge "$f" "${f} に関係するテスト" || continue
  n=$(jq -r '.numTotalTestSuites | numbers' "$json" 2>/dev/null)
  [ "$n" -eq 0 ] && ! listed "$f" "$exempt_none" && missing="$missing  - $f"$'\n'
done

# 変えたテストのうち、上で流れなかったものをまとめて流す（e2e/ は Playwright の領分なので除く）
run_tests=()
for t in "${tests_changed[@]}"; do
  [ -f "$t" ] || continue
  case "$t" in e2e/* | */e2e/*) continue ;; esac
  listed "$t" "$exempt_fail" && continue
  listed "$t" "$ran" && continue
  run_tests+=("$t")
done
if [ ${#run_tests[@]} -gt 0 ]; then
  remain=$((TIMEOUT - (SECONDS - start)))
  timed=1
  [ -z "$unjudged" ] && [ "$remain" -gt 0 ] && run_vitest "$remain" run "${run_tests[@]}"
  if [ "$timed" = 1 ]; then
    for t in "${run_tests[@]}"; do unjudged="$unjudged  - $t"$'\n'; done
  else
    judge "変えたテストファイル（${run_tests[*]}）" "変えたテストファイル" "$(printf '%s\n' "${run_tests[@]}")"
  fi
fi

if [ -n "$broken" ]; then
  {
    echo "test gate: vitest がテストの結果を返さなかったので、次のファイルは判定していません（道具の故障として差し戻しません）:"
    printf '%s' "$broken"
  } >&2
fi

if [ -n "$missing$failures$unjudged$weakened" ]; then
  {
    if [ -n "$weakened" ]; then
      echo "test gate: 次のテストファイルでテストを弱めています（expect が減った・skip・only・todo が増えた・消した）。弱めずに直してから終えてください:"
      printf '%s' "$weakened"
    fi
    if [ -n "$missing" ]; then
      echo "test gate: 次の実装ファイルに関係するテストがありません（vitest related で 0 件）。変えた振る舞いを確かめるテストを書いてから終えてください:"
      printf '%s' "$missing"
    fi
    if [ -n "$failures" ]; then
      echo "test gate: 関係するテストが落ちています。直してから終えてください:"
      printf '%s' "$failures"
    fi
    if [ -n "$unjudged" ]; then
      echo "test gate: ${TIMEOUT} 秒で打ち切り、テストを流しきれなかったので、次のファイルを判定できていません:"
      printf '%s' "$unjudged"
    fi
    echo "テストが本当に要らないファイルは「## テスト不要」、落ちる・流しきれないのを残すテスト（または実装ファイル）は「## 失敗を残す」、正当な理由で弱めるテストは「## テストを弱める」の節に、理由を添えて書いてください:"
    for f in "${ex_files[@]}"; do echo "  $f"; done
    echo "  書き方: - <パス> — <理由>（YYYYMMDD）"
  } >&2
  exit 2
fi

# 道具の故障があった差分は残さない（直ったら流し直すため）
[ -z "$broken" ] && mkdir -p "$STATE_DIR" && printf '%s' "$hash" >"$STATE"
exit 0
