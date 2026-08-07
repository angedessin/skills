# タスクリスト: company-repackage

Last updated: 20260807（実装完了・レビュー待ち）

## 実装前

- [x] `design.md` 承認（プレモータム反映後の再レビュー）
- [x] 未解決: 会社 `modified` を残すか捨てるか → 全て捨てて main 正
- [x] 未解決: 独立フォーク方針節の文面 → 原則独立＋停止契約は上流同期

## 実装

- [x] `main` を `export/company` に merge（`e05d020`）
- [x] 会社 `modified` / 現行 skills と main の差分一覧を作り、残すパッチを決定（残すパッチ: なし）
- [x] 同名 10 スキルを main ベースで同期（`tdd/references/patterns.md` はコピーしない）
- [x] Angular / Jasmine 再適用、非同梱スキル名除去、`source-commit` 更新（10 本すべて `e02a95d`）
- [x] 明示した会社パッチを三点マージ（該当なし＝ゼロ件で確定）
- [x] hooks を 6 本に固定して main 追随（delete 追加。除外 3 本は入れない。理由文から非同梱名除去）
- [x] `settings.example.json`: delete 登録、npx/install deny 維持、`_comment` を本数・python3 依存に更新（PreToolUse を 1 matcher に統合）
- [x] MANIFEST: 変換レシピ、例外同期方針、死んだ検査参照削除、hook 6・依存
- [x] HANDOVER / MIGRATION-GUIDE を整合（python3 欠如時の delete 挙動含む）
- [x] `export/company/tests/` 更新要否を判定（decisions に結果）→ シナリオ本体は有効・根拠コメントのみ更新

## 検証

- [x] スキル数 10
- [x] `patterns.md` 不在
- [x] 許可差分を除いた main との停止契約 diff が空（許可差分: Angular/Jasmine 語彙・MR 運用・非同梱名除去・patterns.md 不在のみ）
- [x] grep: 非同梱名 0 / 誤スタック語彙 0 / 死んだ検査名 0 / 「削除は非対象」は履歴節に注記付きで残置
- [x] hooks 6 ≡ 文書 ≡ settings（機械照合で一致）、npx/install deny 残存（npx 3 / install 系 23）

## レビュー

- [x] 3 文書のノイズ監査（配置する Claude 視点）→ 保守者向け 124 行を `export/COMPANY-MAINTENANCE.md` へ分離・MANIFEST を現状先頭に再構成・重複をポインタに縮退
- [x] 素通り検査 knowledge-capture `--runs 4` → **4/4 PASS**
- [ ] コードレビュー実施
- [ ] 指摘修正

## デプロイ

- [ ] ユーザー承認後 commit
- [ ] ユーザー承認後 push
- [ ] 会社配置は HANDOVER 別セッション

## 福利化 / 知見保存 / クローズ

- [ ] 必要なら compound / knowledge-capture
- [ ] archive
