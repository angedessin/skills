#!/usr/bin/env python3
"""スキル frontmatter・構造の機械検証（マスター専用ツール・依存ゼロ）。

検証項目:
  1. name がディレクトリ名と一致する
  2. description が引用符付き 1 行で 1024 文字以内
  3. ファイル全体が 500 行以内
  4. アストラル面文字（U+10000 以上）を含まない
  5. metadata.version がある

使い方:
  python3 scripts/validate_skills.py            # .claude/skills/ 全体
  python3 scripts/validate_skills.py <dir>      # 指定ディレクトリ配下の各スキル
終了コード: 0 = 全 PASS / 1 = FAIL あり
"""
import re
import sys
from pathlib import Path


def validate(skill_dir: Path) -> list[str]:
    errors = []
    p = skill_dir / "SKILL.md"
    if not p.exists():
        return ["SKILL.md が存在しない"]
    t = p.read_text(encoding="utf-8")

    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not m:
        return ["frontmatter が無い"]
    fm = m.group(1)

    nm = re.search(r"^name: (\S+)$", fm, re.M)
    if not nm:
        errors.append("name が無い")
    elif nm.group(1) != skill_dir.name:
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

    return errors


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else (
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
