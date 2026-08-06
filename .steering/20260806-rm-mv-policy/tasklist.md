# タスクリスト: rm-mv-policy

Last updated: 20260806

## 実装前

- [x] 変更対象語（`guard-gated` / `削除は非対象` / `expected_hooks` / `HOOK_REGISTRATIONS`）で全文検索し、主要コンポーネント表を確定する

## 実装

- [x] `guard-gated-delete.sh` を新設 — command 構造抽出・失敗は沈黙・守る形のみ deny
- [x] `.claude/settings.json` に PreToolUse 登録のみ（permissions 不変）
- [x] `deploy_skills.py` の `expected_hooks` + `HOOK_REGISTRATIONS` を対で更新
- [x] `tests/hooks/guard-gated-delete/` 相当 + `pnpm run test:hooks`（発火／沈黙／抽出失敗／write 回帰）— `tests/hooks/run_fixtures.py` 20/20
- [x] README / starter-kit / `claude-code-config.md` を守る形／守らない形に更新
- [x] `pnpm run` で consistency（(e)(f) 含む）/ 関連 validate — 8/8・33/33
- [x] BACKLOG 節 1 削除 + export ドリフト既知一文（追従タスクなし）
- [x] セッション再起動後の人間 deny 確認 1 ケース（20260806: `rm -f docs/knowledge/x.md` → guard-gated-delete がブロック）

## レビュー

- [x] frontend-code-review の実行（review-result.md）
- [x] レビュー指摘の修正（H1/H2 + M1–M5）
- [ ] 修正後の差分再レビュー

## 知見保存（この PR / ブランチに載せる分）

- [ ] knowledge-capture（PR 差分に属する知見）
- [ ] 必要なら docs/ 追記をこのブランチでコミット

## デプロイ

- [x] PR 作成（base: `integration/20260730-reports`）— https://github.com/angedessin/skills/pull/15
- [ ] CI 確認（あれば）
- [ ] マージ（人間の明示後のみ）

## 福利化

- [ ] 必要なら compound
