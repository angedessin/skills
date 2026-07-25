# タスクリスト: レビュー積み残しの解消

## 0. 最優先（セッション再起動後の最初）

- [ ] `echo test > docs/decisions/_probe.md` を実行し、確認ダイアログが出るか観察する
- [ ] `docs/knowledge/` 配下の Edit でも同様に確認する（ask 側）
- [ ] `docs/decisions/_probe.md` を削除する
- [ ] 結果に応じて記述/実装を訂正する（出なければ「効いている」という記述を撤回する）

## 1. スクリプトの品質指摘

- [ ] `validate_skills.py`: 未知フラグの Traceback を塞ぐ（`args[0].startswith("-")` の一般ガード。既存 6 経路に触れない）
- [ ] `check_export_stopcontract.py`: `--verbose` の仕様一致
- [ ] `check_export_stopcontract.py`: 報告の切り詰めで差分の実体が見えるようにする
- [ ] `check_export_stopcontract.py`: 非同梱スキル名の除去に語境界を入れる
- [ ] `check_export_stopcontract.py`: `read_body()` の型注釈を実体に合わせる
- [ ] `check_export_stopcontract.py`: `STACK_WORDS` に `.test.tsx` / `.spec.tsx` を追加
- [ ] `check_export_stopcontract.py`: `--master` 不在時のエラー文言を分ける

## 2. 権限の射程

- [ ] 配布物 `settings.example.json` に `docs/decisions/` の ask を追加
- [ ] global CLAUDE.md と `.claude/skills/**` を ask に含めるかを判断する（スキル本文の編集は主活動なので摩擦とのトレードオフ）

## 3. 観察

- [ ] `remind-config-docs.sh` の効果を観察する（注入された内容を実際に守ったか）。効かなければ外す

## 4. 完了処理

- [ ] 静的検査（全 PASS・portability 0 件）
- [ ] `knowledge-capture` / `compound`（知見があれば）
- [ ] `steering` archive
