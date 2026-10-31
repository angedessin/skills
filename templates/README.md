# templates — 新規スキルの雛形（マスター専用）

`SKILL.template.md` は新しいスキルを書き始めるための骨格。このディレクトリは配布しない（`scripts/validate_skills.py` と同じマスター専用ツール）。

## 使い方

```bash
# 1. コピー（ディレクトリ名 = スキル名にする）
mkdir -p .claude/skills/[new-skill]
cp templates/SKILL.template.md .claude/skills/[new-skill]/SKILL.md

# 2. プレースホルダ（[...]）を埋め、案内コメントと該当しないブロックを消す

# 3. 検証（このスキルディレクトリ単体）
mise exec -- python3 scripts/validate_skills.py --skill .claude/skills/[new-skill]
```

テンプレ自身は `name:` がディレクトリ名と一致しないため、validator はテンプレ用のモード（`--template`）で検査する。

## スキルを残すかを確かめる

書いたスキルは、スキルなしより良い結果になることを `eval/` で確かめてから残す（課題と採点基準を先に固定する。手順は `eval/README.md`）。残したら、回帰テストのケースを `eval/README.md` の「回帰テスト」の表に足す。
