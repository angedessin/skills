# Tasklist: e2e-skill

Last updated: 20260703

## Implementation

- [x] `e2e/SKILL.md` 新設（判断軸 4 つ・作成/レビュー両モード・references 縮退動作。99 行）
- [x] `e2e/references/patterns.md` 新設（§scope / §run / §locators / §waiting / §auth / §fixtures・example 明記）
- [x] `test-review/SKILL.md` に境界の相互明記（When NOT to use + Related skills）
- [x] `tdd/SKILL.md` に境界の相互明記（When NOT to use + Related skills）
- [x] README 更新: 実装カテゴリに e2e 行を追加

## Verification

- [x] 構造検証: 99 行 / desc 216 字 / name 一致 / アストラル面絵文字なし
- [x] エンジン純度: 本文のツール固有 API 出現 **0 件**（tdd 改修前 34 → 新規契約準拠で 0）
- [ ] 受け入れ試行: Playwright プロジェクトが必要なため配置先での初回利用に繰り越し

## Deploy

- [x] コミット（main 直コミット運用）

## Compound

- [x] compound スキルの実行（昇格 1 件: エンジン純度の実測パターン → skill-design-patterns.md。効果検証: 境界相互明記 2 度目の適用も機能）

## Knowledge

- [x] knowledge-capture スキルの実行（新規保存なし — 昇格分は compound で保存済み、設計判断は design.md が保持）
- [x] steering archive モードでアーカイブ

---

Archived: 20260703
繰り越し（配置時作業）: Playwright プロジェクトでの受け入れ試行。E2E 実需が出たら frontend-code-review への e2e-agent 統合を判断
