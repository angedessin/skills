# スキル課題: first-deployment-run

## 20260806 — skill-deploy / settings.json 配布サブセット

**事象**: 配置先で `claude -p` 起動時に、settings.json の `permissions.ask` にある `Write(…)` ルールについて「Write は file permission checks にマッチしない。Edit(path) だけを使え」という警告が多数出た（Edit と Write を対で配っている現行 DEPLOY_PERMISSIONS）。
**期待**: 配布サブセットの ask ルールが現行 Claude Code のパーミッションモデルと整合し、死んだ Write ルールで警告を出さない（Edit のみ）。
**解消**: 20260806 — マスター / DEPLOY / MASTER_ONLY から Write(path) 削除。契約 (j) 追加。skill-test 手直し済み。

## 20260806 — 配置直後 headless スモーク

**事象**: 未信頼ワークスペースでは allow が無視され、design.md 書き込みが対話の permission 承認待ちになり、完了条件の「DRAFT 提示後の承認停止」を headless で検証できない。
**期待**: starter-kit / skill-deploy Step 4 の「先に対話で信頼ダイアログ」が完了条件の前提として明示され続ける。
**解消**: 対話 CLI でスモーク PASS（同日）。headless 限界は仕様どおり。
