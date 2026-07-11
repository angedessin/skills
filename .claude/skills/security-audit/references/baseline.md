# baseline — hooks / settings のあるべき基準表

Step 2 で settings.json・hooks を突き合わせる基準。配置先に settings.json の設計思想が無くても
網羅判定ができるよう、このスキルに自己完結で同梱する。無い場合はスキル本文が縮退動作（素朴確認 + 基準なしを明記）する。

## permissions.deny にあるべき（無いなら「要確認」）

- パッケージインストール: `pnpm add *`・`pnpm install*`・`pnpm dlx *`・`npm i*`・`npm install*`・`npm ci*`・`npx -y *`・`npx --yes *`・`yarn add *`・`yarn dlx *`・`bun add *`・`bunx *`・`pip install *`・`brew install *`
- シークレット読み取り（Bash 経由）: `cat .env*`・`cat *.env`・`grep * .env*`・`printenv`・`env`
- シークレット読み取り（Read 経由）: `.env*`・`*.pem`・`*.key`・`~/.ssh/**`・`~/.aws/**`・`~/.claude/.credentials.json`
- 破壊的操作: `rm -rf *`・`rm -fr *`・`git push --force*`・`git push -f*`・`git reset --hard*`・`git clean -f*`

理由: deny の Bash ルールは前置一致で `head`/`sed`/`base64`/リダイレクト等により迂回可能。
そのため deny だけに頼らず、PreToolUse の env ガード hook（コマンド全文検査・フェイルクローズ）も併設されているのが望ましい。

## permissions.ask にあるべき（無いなら「要確認」）

- 素の `npx *`（`-y`/`--yes` は deny 側）・`rm -r*`・`git push*`
- ガードレール自身の変更: `settings.json`・`settings.local.json`・`hooks/**` の Edit/Write

## hooks の健全性

- **PreToolUse の env ガード**: jq 不在で**フェイルクローズ**（`ask` に落とす）。無言素通しは NG。
- **PostToolUse**: `exit 2 + stderr`（差し戻し）か `hookSpecificOutput.additionalContext` を使う。
  `permissionDecision` を PostToolUse で使うのは無効な形式 → 検出したら「要確認」。
- **課金の自動起動禁止**: SessionStart / Stop / PostToolUse に、エージェントを N 回起動する
  スクリプト（passthrough_check.py 等）や課金スキルが接続されていないこと。接続あり → 危険。
- **Stop hook の型/lint**: `stop_hook_active` による無限ループ防止があること。

## 判定の出し方

- 各項目を「あり / 無し（要確認）/ 該当なし（この配置先では不要）」で出す。
- 「無し」を即「危険」とはしない — 配置先の運用（PR 無し・CI 無し等）で不要な項目もある。
  網羅から漏れている事実を**要確認として提示**し、要否はユーザーが判断する。
