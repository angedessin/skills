# templates — 新規スキルの雛形（マスター専用）

`SKILL.template.md` は新規スキルを契約準拠で書き始めるための骨格。構造とプレースホルダのみを持ち、
ルールの「なぜ」は複製せず `docs/knowledge/skill-design-patterns.md` へのポインタで済ませている。
このディレクトリは配布しない（`scripts/validate_skills.py` と同じマスター専用ツール）。

## 使い方

```bash
# 1. コピー（ディレクトリ名 = スキル名にする）
cp templates/SKILL.template.md .claude/skills/[new-skill]/SKILL.md

# 2. プレースホルダを埋める
#    - name: をディレクトリ名と一致させる
#    - <!-- --> の案内コメントは、該当しないブロック（前提チェック/停止/境界相互明記）ごと削除する
#    - ルールの詳細は docs/knowledge/skill-design-patterns.md を参照して書く

# 3. 検証（このスキルディレクトリ単体）
python3 scripts/validate_skills.py --skill .claude/skills/[new-skill]
#    → PASS で機械契約（name一致・description引用符・500行以内・アストラル面文字なし・version）は充足
```

テンプレ自身は `name:` がディレクトリ名と一致しないため validator を直接は通せない。
検証は必ずコピー先（実スキルのディレクトリ）で行う。

## 契約が変わったら

`validate_skills.py` か `skill-design-patterns.md` を更新したら、相互ポインタをたどって
`SKILL.template.md` も**同一コミットで**更新する（skill-design-patterns.md「片側修正の禁止」）。
