# タスクリスト: rm-mv-policy

Last updated: 20260806
Archived: 20260806

## 実装前

- [x] 変更対象語（`guard-gated` / `削除は非対象` / `expected_hooks` / `HOOK_REGISTRATIONS`）で全文検索し、主要コンポーネント表を確定する

## 実装

- [x] `guard-gated-delete.sh` を新設 — command 構造抽出・失敗は沈黙・守る形のみ deny
- [x] `.claude/settings.json` に PreToolUse 登録のみ（permissions 不変）
- [x] `deploy_skills.py` の `expected_hooks` + `HOOK_REGISTRATIONS` を対で更新
- [x] `tests/hooks/run_fixtures.py` + `pnpm run test:hooks` — 25/25
- [x] README / starter-kit / `claude-code-config.md` を守る形／守らない形に更新
- [x] `pnpm run` で consistency / validate
- [x] BACKLOG 節 1 削除 + export ドリフト既知一文
- [x] セッション再起動後の人間 deny 確認 1 ケース

## レビュー

- [x] frontend-code-review の実行（review-result.md）
- [x] レビュー指摘の修正（H1/H2 + M1–M5）
- [x] 修正後の差分再レビュー（25/25・High 穴塞ぎ確認）

## 知見保存（この PR / ブランチに載せる分）

- [x] knowledge-capture — 追加ファイル無し（claude-code-config / fixtures / decisions に反映済み）
- [x] docs/ 追記は本ブランチに含む

## デプロイ

- [x] PR 作成 — https://github.com/angedessin/skills/pull/15
- [x] CI 確認（チェック無し）
- [x] マージ（人間明示後）

## 福利化

- [x] compound — 今回は不要（行動ルール新設なし。必要なら別途）
