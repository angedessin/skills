#!/bin/bash
# 評価用 plugin の中身を、グループごとに条件 B か C に入れ替える。evals/ は両条件で共通（1 か所だけに置く）。
#   ./prepare.sh b design|impl|review   タグ pre-renewal-20261006 の版（現行）
#   ./prepare.sh c design|impl|review   書き直し版（採用済みのグループはマスター、評価中のグループは conditions/c/<group>/）
# 条件 A は plugin なしの baseline arm（plugin eval が自動で回す）なので、ここでは作らない。
# plugin にはそのグループのスキルだけを入れる。実行は `--tag <group>` でそのグループのケースだけに絞る。
set -euo pipefail
cd "$(dirname "$0")"
cond="${1:-}"
group="${2:-}"
TAG=pre-renewal-20261006

case "${group}" in
  design)
    SKILLS=(design-doc steering design-premortem)
    AGENTS=(premortem-attacker)
    # 判定済み（20261027）: design-doc・steering は C に置き換えてマスターが正本。
    # design-premortem は手動専用（disable-model-invocation）で残したので、プロンプトでは発動しない。評価の C には入れない
    C_FROM_MASTER=(design-doc steering)
    ;;
  impl)
    SKILLS=(impl-from-design tdd e2e)
    AGENTS=(codebase-explorer)
    # 判定済み（20261028）: e2e は C に置き換えてマスターが正本。impl-from-design・tdd は削除
    C_FROM_MASTER=(e2e)
    ;;
  review)
    SKILLS=(frontend-code-review review-a11y review-correctness review-performance review-security review-ui impl-review test-review)
    AGENTS=(review-a11y review-correctness review-impl review-performance review-security review-test review-ui)
    # 判定済み（20261031）: frontend-code-review は C に置き換えてマスターが正本。agent も C の 5 本をマスターから取る
    C_FROM_MASTER=(frontend-code-review)
    C_AGENTS_FROM_MASTER=(review-bug review-rules review-ui-a11y review-test review-verify)
    ;;
  *) echo "usage: $0 b|c design|impl|review" >&2; exit 2 ;;
esac
case "${cond}" in
  b|c) ;;
  *) echo "usage: $0 b|c design|impl|review" >&2; exit 2 ;;
esac

rm -rf skills agents hooks/skill-claude-md.md .claude-plugin
mkdir -p skills agents .claude-plugin

if [ "${cond}" = b ]; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  paths=()
  for s in "${SKILLS[@]}"; do paths+=(".claude/skills/$s"); done
  for a in "${AGENTS[@]}"; do paths+=(".claude/agents/$a.md"); done
  git -C "$(git rev-parse --show-toplevel)" archive "$TAG" "${paths[@]}" | tar -x -C "$tmp"
  cp -R "$tmp/.claude/skills/." skills/
  cp -R "$tmp/.claude/agents/." agents/
else
  # 採用が決まったグループの C はマスターの .claude/skills/ が正本（評価した版は git の履歴にある）
  for s in ${C_FROM_MASTER[@]+"${C_FROM_MASTER[@]}"}; do cp -R "../.claude/skills/$s" skills/; done
  for a in ${C_AGENTS_FROM_MASTER[@]+"${C_AGENTS_FROM_MASTER[@]}"}; do cp "../.claude/agents/$a.md" agents/; done
  [ -d "conditions/c/${group}/skills" ] && cp -R "conditions/c/${group}/skills/." skills/
  [ -d "conditions/c/${group}/agents" ] && cp -R "conditions/c/${group}/agents/." agents/
  [ -n "$(ls skills)" ] || { echo "条件 c の ${group} のスキルがまだ無い（conditions/c/${group}/skills/）" >&2; exit 1; }
fi
f="conditions/${cond}/${group}-skill-claude-md.md"
if [ -f "$f" ]; then cp "$f" hooks/skill-claude-md.md; fi

cat > .claude-plugin/plugin.json <<JSON
{
  "name": "eval-${cond}",
  "version": "0.0.0",
  "description": "skillset-renewal の評価用（条件 ${cond}）。配布には使わない"
}
JSON

# 全ケースの append_system_prompt が common-claude-md.md と一致するか（条件間で CLAUDE.md がずれないように）
python3 -I - "$PWD" <<'PY'
import pathlib, sys, textwrap
root = pathlib.Path(sys.argv[1])
want = (root / "common-claude-md.md").read_text(encoding="utf-8")
bad = []
cases = sorted(root.glob("evals/**/case.yaml"))
for p in cases:
    lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    try:
        i = next(n for n, l in enumerate(lines) if l.strip() == "append_system_prompt: |")
    except StopIteration:
        bad.append(f"{p}: append_system_prompt が無い"); continue
    block = []
    for l in lines[i + 1:]:
        if l.strip() and not l.startswith("    "):
            break
        block.append(l)
    if textwrap.dedent("".join(block)).rstrip("\n") != want.rstrip("\n"):
        bad.append(f"{p}: common-claude-md.md と一致しない")
if not cases:
    bad.append("case.yaml が 1 件も無い")
for b in bad:
    print("NG", b, file=sys.stderr)
sys.exit(1 if bad else 0)
PY

echo "条件 ${cond} を用意した: skills=$(ls skills | tr '\n' ' ')agents=$(ls agents | tr '\n' ' ')"
