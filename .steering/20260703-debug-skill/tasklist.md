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

- [ ] compound スキルの実行（実装中の学びの昇格判断）

## Knowledge

- [ ] knowledge-capture スキルの実行
- [ ] steering archive モードでアーカイブ
