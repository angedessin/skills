# タスクリスト: design-impl-sync

Last updated: 20260803

## 実装前 — 変更対象の確定

- [x] 「方針転換」「乖離が生じた」「設計整合」「Axis 1」で全文検索し、主要コンポーネント表の挙げ漏れを潰す（片側修正防止）

## 実装

- [x] `design-doc/SKILL.md`: 方針転換＝分類表＋DRAFT 戻し／APPROVED 追認＋単一ライター＋SPIKE 委譲
- [x] `impl-from-design/SKILL.md`: 乖離＝停止＋短い分類テンプレ（Status/コアは書かない）
- [x] `impl-review/SKILL.md`: Axis 1＝契約コア全見出し突合＋APPROVED のみ High＋単独時次ステップ
- [x] `frontend-code-review/SKILL.md`: High に設計例外／軽量でも Axis 1（条件付き）／DEFERRED 警告
- [x] `feature-pipeline/SKILL.md`: 乖離待機の両分岐＋review-result 破棄整合
- [x] 機械検査: `validate_skills.py` にキー共存検査（限界コメント付き）
- [x] `pnpm run validate` グリーン
- [x] BACKLOG 節 4 の同期パス行を完了表記（マージ直前で可）

## レビュー

- [x] frontend-code-review の実行（スキル Markdown 成果物向け）
- [x] レビュー指摘の修正（review-result.md を参照）
- [x] 修正後の差分再レビュー

## 知見保存（この PR / ブランチに載せる分）

- [x] knowledge-capture スキルの実行（追加 docs なし。decisions / SKILL / validate で足りる）
- [x] 必要なら docs/ への追記をこのブランチでコミット（compound 経由で skill-design-patterns）

## デプロイ

- [x] PR 作成（base = `integration/20260730-reports`。`pr-create`）— https://github.com/angedessin/skills/pull/8
- [x] CI グリーン確認（CI 未設定のため N/A）
- [ ] マージ（**人間の明示「マージして」まで禁止**）— アーカイブ後に実施

## 福利化

- [x] compound の実行（片側修正節へ空スコープ早期終了の短文）

## クローズ

- [x] steering archive モードでアーカイブ（マージ前）

Archived: 20260803
