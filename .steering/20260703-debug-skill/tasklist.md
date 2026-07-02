# Tasklist: debug-skill

Last updated: 20260703

## Implementation

- [x] `debug/SKILL.md` 新設（5 ステップフロー・出口分岐・再現不能時の縮退・investigation.md フォールバック）
- [x] `design-doc/SKILL.md` 改訂: description から「障害調査」除去 + リダイレクト追記（description 末尾 + When NOT to use）
- [x] README 更新: スキル一覧（設計・コンテキスト管理）に debug 追加 + 入口分岐の一文

## Verification

- [x] 構造検証: debug（73 行・desc 200 字）/ design-doc（137 行・desc 383 字）— name 一致・絵文字なし・引用符付き
- [ ] 受け入れ試行: 実バグが必要なため配置先での初回利用に繰り越し（design.md Test strategy 参照）

## Deploy

- [x] コミット（main 直コミット運用）

## Compound

- [x] compound スキルの実行（昇格候補ゼロ。効果検証: impl-from-design モード分岐が 2 回目の適用でも正常動作）

## Knowledge

- [x] knowledge-capture スキルの実行（新規保存なし — 設計判断は design.md / new-skills.md が保持）
- [x] steering archive モードでアーカイブ

---

Archived: 20260703
繰り越し（配置時作業）: 実バグでの受け入れ試行は配置先プロジェクトでの初回利用時に行う
