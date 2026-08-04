# タスクリスト: knowledge-freshness-nudge

Last updated: 20260804

## 実装前（主要コンポーネント確定）

- [x] 変更対象語で全文検索し、表の漏れを潰す: `rule-audit` / `SessionStart` / `session-start-check` / `月 1` / `鮮度` / `.last-rule-audit` / `docs-lifecycle-tiers` / `ナレッジ鮮度` / `GITIGNORE_LINES` / `ランタイムフラグ` / `3 行`
- [x] 配布分類確認: `session-start-check.sh`・`rule-audit` = 配布可。ADR・BACKLOG・validate・deploy_skills = master 側ツール。表に master-only スキル名を配布可本文へ書かない

## 実装

- [x] `.gitignore` と `deploy_skills.py` `GITIGNORE_LINES` に `.steering/.last-rule-audit` を追加（user-guide 行数も 4 に）
- [x] `session-start-check.sh`: スキル存在ゲート・`date +%s`・異常系・【rule-audit 月次】三択（capture/codify の後）・失敗時フェイルオープン
- [x] `rule-audit/SKILL.md` Step 5: マーカー更新 + 「当該ファイルのみ承認不要例外」明示
- [x] `CLAUDE.md` に任意再掲（順序・別契約のスキップ寿命）
- [x] `docs/starter-kit.md` / `docs/user-guide.md` / `README.md` を同一契約に同期
- [x] ADR 20260715 に Amendment（Consequences Bad 一文含む。Decision 核は不変）
- [x] `.steering/BACKLOG.md` 節 4 の「ナレッジ鮮度の機械化」行を削除
- [x] `scripts/validate_skills.py` にキー共存検査（capture「次の Stop」と分離）
- [x] hook フィクスチャ 9 ケースを実行して記録（`verification.md`）

## レビュー

- [x] frontend-code-review の実行（モードは diff トリアージに従う）
- [x] レビュー指摘の修正（review-result.md を参照）— Medium 1 件（八進マーカー）解消
- [x] 修正後の差分再レビュー（correctness）

## 知見保存（この PR / ブランチに載せる分）

- [ ] knowledge-capture スキルの実行（PR 差分に属する知見）
- [ ] 必要なら docs/ への追記をこのブランチでコミット

## デプロイ

- [ ] PR 作成（base = `integration/20260730-reports`。`pr-create`）
- [ ] CI グリーン確認
- [ ] マージ（**人間の明示「マージして」があるまでしない**）

## 福利化

- [ ] compound スキルの実行（パターンをルール・知識に昇格）

## クローズ

- [ ] knowledge-capture（会話由来・横断の残りがあれば）
- [ ] steering archive モードでアーカイブ（親マージ前）
