# タスクリスト: spike-lane

Last updated: 20260801

## 実装前（主要コンポーネントの確定）

- [x] `Status` / `DRAFT` / `APPROVED` / `SPIKE` / `impl-from-design` / `pr-create` / `feature-pipeline` を全文検索し、変更対象の挙げ漏れがないか確認して主要コンポーネント表を確定する

## 実装

- [x] design-doc テンプレ + SKILL: Status 3 値・正規表記・SPIKE 入口/出口・Phase 4 直昇格停止・decisions 必須・ツリーゲート
- [x] steering SKILL + references/spec.md: SPIKE 表示 + 実装可否正本（旧二値文を残さない）
- [x] impl-from-design: SPIKE 続行 / DRAFT・未知停止 / 外向き禁止の注意
- [x] pr-create: SPIKE 拒否 + 複数タスク/差分混入の fail-closed
- [x] feature-pipeline: 判定表 DRAFT 直後に SPIKE 即停止 + 未知 fail-closed（README と同一コミット）
- [x] README ワークフロー図を feature-pipeline と同一コミットで改訂
- [x] user-guide / starter-kit の Status・依存表を契約に揃える
- [x] passthrough: DRAFT 停止維持 + SPIKE 続行 + pr-create SPIKE 拒否（必須）
- [x] impl-tournament に SPIKE 不可を一文
- [x] BACKLOG 節 4 から SPIKE 行を削除
- [x] `pnpm run validate` PASS（`mise exec --`）

## レビュー

- [x] frontend-code-review の実行（スキル/文書変更のため軽量モード）
- [x] レビュー指摘の修正（review-result.md を参照）
- [x] 修正後の差分再レビュー（RESOLVED）

## 知見保存（この PR / ブランチに載せる分）

- [ ] knowledge-capture スキルの実行（PR 差分に属する知見）
- [ ] 必要なら docs/ への追記をこのブランチでコミット

## デプロイ

- [x] PR 作成（base = `integration/20260730-reports`）— https://github.com/angedessin/skills/pull/7
- [ ] CI グリーン確認
- [ ] マージ（**人間の明示指示があるまでしない**）

## 福利化

- [ ] compound スキルの実行（パターンをルール・知識に昇格）

## クローズ

- [ ] knowledge-capture（会話由来・横断の残りがあれば）
- [ ] steering archive モードでアーカイブ
