# タスクリスト: pr13-mustfix

Last updated: 20260807

## 実装

- [x] `feature/20260807-pr13-mustfix` を親 `integration/20260730-reports` から作成
- [x] M1: `guard-gated-delete.sh` 行継続畳み込み + 改行ループ判定 + ヘッダ宣言更新
- [x] M2: グロブ境界クラス拡張（B20・無関係パスを壊さない）
- [x] M1/M2 フィクスチャ最低 5 件追加（B11/B19/B20 回帰確認）
- [x] M3: `decision_from_stdout` 部分一致削除 + runner 内自己テスト
- [x] M4: README 契約列挙・npm scripts 訂正 + `check_asset_consistency` 新契約
- [x] 脅威モデル文書: README / starter-kit の「複合シェル」を `&&||;|` 限定＋改行区切りは守る形（hook ヘッダと同一コミット）
- [x] M5: FCR 次ステップ順・節リスト / skill-design-patterns 節リスト / validate キー共存+位置比較
- [x] nit: 腐った行数削除・validate-skill-edit コメント・README ディレクトリ構成
- [x] 変更対象語で全文検索し、主要コンポーネント表の漏れを実装前に確定
- [x] `mise exec -- pnpm run validate:assets` / `validate` / `test:hooks` 緑確認（9/9・34/34・35/35）

## レビュー

- [x] frontend-code-review の実行（または差分規模に応じた軽量確認）
- [x] レビュー指摘の修正（review-result.md を参照）
- [x] 修正後の差分再レビュー

## 知見保存（この PR / ブランチに載せる分）
<!-- この変更の説明・落とし穴として残す knowledge は、マージ前に同じブランチへ含める。 -->

- [ ] knowledge-capture スキルの実行（PR 差分に属する知見）
- [ ] 必要なら docs/ への追記をこのブランチでコミット

## デプロイ
<!-- base=integration/20260730-reports の feature PR。PR #13 の ready/マージはしない。 -->

- [x] feature PR 作成（`pr-create` または `gh pr create`、base=親）— https://github.com/angedessin/skills/pull/16
- [ ] CI グリーン確認
- [ ] 親へマージ
- [ ] PR #13 本文（Test plan 員数）を更新
- [ ] （人間明示後のみ）PR #13 ready / マージ — このタスクではしない

## 福利化

- [ ] compound スキルの実行（パターンをルール・知識に昇格）

## クローズ

- [ ] knowledge-capture（会話由来・横断の残りがあれば）
- [ ] hook 人間確認の観測を decisions.md に記録
- [ ] steering archive モードでアーカイブ（main マージ前に済ませる）
