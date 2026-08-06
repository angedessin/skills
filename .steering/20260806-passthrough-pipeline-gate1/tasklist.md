# タスクリスト: passthrough-pipeline-gate1

Last updated: 20260806

## 実装前（変更対象の確定）

- [x] `feature-pipeline` / `passthrough` / `Gate 1` / `judge_glob` / `feature-pipeline-gate1` でリポジトリを全文検索し、シナリオ以外に片側修正が要る参照が無いか確認（主に BACKLOG・skill-test 案内・knowledge）
- [x] 既存 `tests/passthrough/impl-from-design/scenario.md` を型として読み、sandbox 差分（スキルパス・request・pressure・judge_glob に design.md）を決める

## 実装

- [x] `tests/passthrough/feature-pipeline-gate1/scenario.md` を作成（Gate 1 / DRAFT 停止 + Status 改変検出）
- [x] `python3 scripts/passthrough_check.py tests/passthrough/feature-pipeline-gate1/scenario.md --dry-run` で構造確認し、スナップショット N≥1 を目視
- [x] `.steering/BACKLOG.md` 節 4 を「Gate 1 骨格・未実走」文言で更新

## レビュー

- [x] frontend-code-review の実行（シナリオ Markdown 中心なら軽量で可）
- [x] レビュー指摘の修正（review-result.md を参照）— 重要指摘 0。Info 1 は任意。指摘なし扱いで RESOLVED
- [x] 修正後の差分再レビュー — 指摘なしのため再レビュー省略

## 知見保存（この PR / ブランチに載せる分）
<!-- この変更の説明・落とし穴として残す knowledge は、マージ前に同じブランチへ含める。 -->

- [ ] knowledge-capture スキルの実行（PR 差分に属する知見）
- [ ] 必要なら docs/ への追記をこのブランチでコミット

## デプロイ

- [ ] PR 作成（base = `integration/20260730-reports`。`pr-create` または `gh pr create`）
- [ ] CI グリーン確認（あれば）
- [ ] マージは人間の明示指示後のみ

## 福利化

- [ ] compound スキルの実行（パターンをルール・知識に昇格）

## クローズ

- [ ] knowledge-capture（会話由来・横断の残りがあれば）
- [ ] steering archive モードでアーカイブ
- [ ] （任意）課金実走は skill-test のコスト承認後
