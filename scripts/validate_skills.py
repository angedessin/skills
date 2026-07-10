#!/usr/bin/env python3
"""スキル frontmatter・構造の機械検証（マスター専用ツール・依存ゼロ）。

検証項目:
  1. name がディレクトリ名と一致する
  2. description が引用符付き 1 行で 1024 文字以内
  3. ファイル全体が 500 行以内
  4. アストラル面文字（U+10000 以上）を含まない
  5. metadata.version がある
  6. 本文に「When NOT to use」を含む見出しがある（発動境界の明示）
  7. 承認語彙（承認 / APPROVED）が出現するスキルは、本文にハードストップ表現
     （「ここで止ま」または見出しの STOP）を 1 つ以上持つ。否定形（承認不要 等）は
     トリガーから除外。逃し弁として本文に <!-- validator: no-stop-needed --> があればスキップ。

純度計測（レポートのみ・FAIL にしない）:
  python3 scripts/validate_skills.py --purity        # 各スキル本文のツール固有 API 出現数

使い方:
  python3 scripts/validate_skills.py                 # .claude/skills/ 全体
  python3 scripts/validate_skills.py <dir>           # 指定ディレクトリ配下の各スキル
  python3 scripts/validate_skills.py --skill <dir>   # 単一スキル（そのディレクトリ自体）のみ
  python3 scripts/validate_skills.py --template      # templates/SKILL.template.md（プレースホルダ許容）
  python3 scripts/validate_skills.py --purity        # ツール純度レポート（FAIL にしない）
終了コード: 0 = 全 PASS / 1 = FAIL あり
"""
import re
import sys
from pathlib import Path

# 項目8（純度計測）で数えるツール固有語彙。本文（frontmatter・references/ を除く）に
# これらが出るほどエンジン純度が下がる。skill-design-patterns.md「エンジン純度を実測する」を機械化。
TOOL_VOCAB = [
    "gh", "git", "npx", "pnpm", "npm", "yarn", "node", "python3",
    "playwright", "vitest", "jest", "eslint", "biome", "tsc", "curl", "jq",
]

# 項目7で承認語彙のトリガーから除外する否定形（自律実行境界の引用による誤 FAIL を防ぐ）。
_APPROVAL_NEGATIONS = ["承認不要", "承認なし", "承認は不要", "承認を要さない"]


def validate(skill_dir: Path, template_mode: bool = False) -> list[str]:
    """スキルの frontmatter・構造を検証する。

    template_mode=True は templates/SKILL.template.md 用。値はプレースホルダ（[...] 形式）でも
    許容し、構造（frontmatter の存在・キー・行数・文字種）だけを検査する。
    name がディレクトリ名と一致する検査だけはテンプレでは意味を持たないためスキップする。
    """
    errors = []
    p = skill_dir if template_mode else skill_dir / "SKILL.md"
    if not p.exists():
        return [f"{p.name} が存在しない"]
    t = p.read_text(encoding="utf-8")

    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not m:
        return ["frontmatter が無い"]
    fm = m.group(1)

    nm = re.search(r"^name: (\S+)$", fm, re.M)
    if not nm:
        errors.append("name が無い")
    elif not template_mode and nm.group(1) != skill_dir.name:
        errors.append(f'name "{nm.group(1)}" がディレクトリ名 "{skill_dir.name}" と不一致')

    dm = re.search(r'^description: "(.+)"$', fm, re.M)
    if not dm:
        errors.append("description が引用符付き 1 行で書かれていない")
    elif len(dm.group(1)) > 1024:
        errors.append(f"description が {len(dm.group(1))} 文字（上限 1024）")

    if not re.search(r'^metadata:\n  version: "[^"]+"$', fm, re.M):
        errors.append("metadata.version が無い")

    lines = t.count("\n") + 1
    if lines > 500:
        errors.append(f"{lines} 行（上限 500）")

    for i, line in enumerate(t.splitlines(), 1):
        astral = [c for c in line if ord(c) >= 0x10000]
        if astral:
            errors.append(f"アストラル面文字 {astral!r}（L{i}）— 400 エラーの原因")
            break

    body = t[m.end():]  # frontmatter を除いた本文

    # 項目6 — 「When NOT to use」を含む見出しの存在（発動境界の明示）
    if not re.search(r"^#+ .*When NOT to use", body, re.M):
        errors.append("本文に「When NOT to use」を含む見出しが無い（発動境界を明示する）")

    # 項目7 — 停止契約の構造検査
    scan = t
    for neg in _APPROVAL_NEGATIONS:
        scan = scan.replace(neg, "")
    has_approval = re.search(r"承認|APPROVED|approved", scan) is not None
    # 逃し弁マーカー。理由をコメント内に書く運用のため、末尾テキストの有無に依らず接頭辞で判定する。
    has_escape = "<!-- validator: no-stop-needed" in body
    has_hardstop = ("ここで止ま" in body) or (re.search(r"^#+ .*STOP", body, re.M) is not None)
    if has_approval and not has_hardstop and not has_escape:
        errors.append(
            "承認語彙があるのにハードストップ表現（「ここで止まる」/ 見出しの STOP）が無い"
            "（停止を説明文でなく手順の Step にする。停止点を持たないスキルは "
            "<!-- validator: no-stop-needed --> を理由つきで置く）"
        )

    return errors


def purity_counts(skill_md: Path) -> dict[str, int]:
    """SKILL.md 本文（frontmatter 除く）のツール固有語彙の出現数を返す。

    references/ は別ファイルのため自然に除外される（この関数は SKILL.md しか読まない）。
    語境界つきで数える（gh が「英語」の一部に一致しない等）。
    """
    t = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n.*?\n---\n", t, re.S)
    body = t[m.end():] if m else t
    counts: dict[str, int] = {}
    for tok in TOOL_VOCAB:
        hits = re.findall(r"(?<![\w-])" + re.escape(tok) + r"(?![\w-])", body)
        if hits:
            counts[tok] = len(hits)
    return counts


def main() -> None:
    args = sys.argv[1:]
    # 純度レポートモード（項目8・FAIL にしない・レポートのみ）
    if args and args[0] == "--purity":
        root = Path(args[1]) if len(args) > 1 else (
            Path(__file__).resolve().parent.parent / ".claude" / "skills"
        )
        dirs = sorted(d for d in root.iterdir() if d.is_dir())
        print("ツール純度レポート（本文のツール固有語彙の出現数・少ないほど良い）\n")
        for d in dirs:
            skill_md = d / "SKILL.md"
            if not skill_md.exists():
                continue
            counts = purity_counts(skill_md)
            total = sum(counts.values())
            detail = "  ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
            print(f"{total:>4}  {d.name}" + (f"    ({detail})" if detail else ""))
        sys.exit(0)

    # テンプレートモード（templates/SKILL.template.md をプレースホルダ許容で検証）
    if args and args[0] == "--template":
        tpl = (
            Path(args[1]) if len(args) > 1
            else Path(__file__).resolve().parent.parent / "templates" / "SKILL.template.md"
        )
        errs = validate(tpl, template_mode=True)
        if errs:
            print(f"FAIL  {tpl.name} (template)")
            for e in errs:
                print(f"      - {e}")
            sys.exit(1)
        print(f"PASS  {tpl.name} (template)")
        sys.exit(0)

    # 単一スキルモード（PostToolUse hook が編集された 1 スキルだけを検証する用途）
    if args and args[0] == "--skill":
        if len(args) < 2:
            print("--skill にはスキルディレクトリのパスが必要です")
            sys.exit(1)
        d = Path(args[1])
        errs = validate(d)
        if errs:
            print(f"FAIL  {d.name}")
            for e in errs:
                print(f"      - {e}")
            sys.exit(1)
        print(f"PASS  {d.name}")
        sys.exit(0)

    root = Path(args[0]) if args else (
        Path(__file__).resolve().parent.parent / ".claude" / "skills"
    )
    dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if not dirs:
        print(f"スキルディレクトリが見つかりません: {root}")
        sys.exit(1)

    failed = 0
    for d in dirs:
        errs = validate(d)
        if errs:
            failed += 1
            print(f"FAIL  {d.name}")
            for e in errs:
                print(f"      - {e}")
        else:
            print(f"PASS  {d.name}")

    print(f"\n{len(dirs) - failed}/{len(dirs)} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
