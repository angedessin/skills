# Tasklist: rule-audit

Last updated: 20260703

## Implementation

- [x] `rule-audit/SKILL.md` 新設（監査基準 5 項目・手順 7 ステップ・compound 棲み分け表・フォールバック）
- [x] `compound/SKILL.md` の Related skills に rule-audit を追記
- [x] README 更新: スキル一覧（ナレッジ管理・自己改善 節）+ 自己改善ループ節に剪定の一文

## Verification

- [x] 構造検証: name 一致 / description ≤1024 / 本文 <500 行 / アストラル面絵文字なし（全 17 スキル走査で兼用）
- [x] 受け入れ試行: 本リポジトリの CLAUDE.md に実行。所見 6 件（参照切れ @testing-patterns / find の archived 未除外 / glossary 空 / config 導線なし / empirical 引用符 / 保持 16 件）→ 5 件をユーザー承認のうえ適用

## Deploy

- [x] コミット（main 直コミット運用）

## Compound

- [x] compound スキルの実行（昇格 1 件: @参照の毎セッション展開 → claude-code-config.md。効果検証: 20260702 昇格の初適用が正常動作。compound 自体の分担矛盾を skill-issues.md に記録）

## Knowledge

- [x] knowledge-capture スキルの実行（新規保存なし — 唯一の候補は compound で保存済み、設計判断は design.md / new-skills.md が保持）
- [x] steering archive モードでアーカイブ

---

Archived: 20260703
