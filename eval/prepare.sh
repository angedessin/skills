#!/bin/bash
# 評価用 plugin の中身を条件 B か C に入れ替える。evals/ は両条件で共通（1 か所だけに置く）。
#   ./prepare.sh b   タグ pre-renewal-20261006 の版（現行）
#   ./prepare.sh c   conditions/c/ の書き直し版
# 条件 A は plugin なしの baseline arm（plugin eval が自動で回す）なので、ここでは作らない。
set -euo pipefail
cd "$(dirname "$0")"
cond="${1:-}"
TAG=pre-renewal-20261006
SKILLS=(design-doc steering design-premortem)
AGENTS=(premortem-attacker)
# 設計グループの判定（20261027）: design-doc・steering は C に置き換え、design-premortem は削除
C_FROM_MASTER=(design-doc steering)

case "${cond}" in
  b|c) ;;
  *) echo "usage: $0 b|c" >&2; exit 2 ;;
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
  for s in "${C_FROM_MASTER[@]}"; do cp -R "../.claude/skills/$s" skills/; done
  [ -d conditions/c/skills ] && cp -R conditions/c/skills/. skills/
  [ -d conditions/c/agents ] && cp -R conditions/c/agents/. agents/
fi
[ -f "conditions/${cond}/skill-claude-md.md" ] && cp "conditions/${cond}/skill-claude-md.md" hooks/

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
