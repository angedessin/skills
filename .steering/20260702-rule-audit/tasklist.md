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

- [ ] compound スキルの実行（実装中の学びの昇格判断）

## Knowledge

- [ ] knowledge-capture スキルの実行
- [ ] steering archive モードでアーカイブ
