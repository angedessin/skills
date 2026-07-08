# Tasklist: skill-template

Last updated: 20260708

## Implementation

- [x] `templates/SKILL.template.md` を作成（frontmatter 骨格・セクション骨格・ハードストップ雛形・境界相互明記プレースホルダ・skill-design-patterns.md へのポインタ）
- [x] `templates/README.md` を作成（コピー → 埋め → validate_skills.py 検証の手順）
- [x] CLAUDE.md「スキル管理ルール」に「新規スキルはテンプレから始める」を1行追記
- [x] `docs/knowledge/skill-design-patterns.md` の契約準拠節にテンプレへのポインタを1行追記（CLAUDE.md 追記と同一コミット）
- [x] compound 本文にテンプレ参照 + フォールバック文を1行追記（Open question 2 の推奨「入れる」に従った）

## Verification

- [x] プレースホルダを仮の値で埋めたインスタンスを scratchpad のスキルディレクトリに置き `validate_skills.py --skill` で PASS を確認
- [x] テンプレート・README にアストラル面文字がないことを確認（Python で U+10000 以上を走査 → none）
- [x] 追記した語（`templates/SKILL.template.md` 等）をリポジトリ全体で grep し、同じ情報を持つ箇所の直し漏れがないことを確認
- [x] 回帰: `validate_skills.py` 全体 20/20 PASS（compound 編集後）

## Deploy

- [ ] コミット（テンプレ + CLAUDE.md + skill-design-patterns.md + compound を同一コミットで）

## Knowledge

- [ ] knowledge-capture スキルの実行
- [ ] steering archive モードでアーカイブ
