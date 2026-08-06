# 決定事項: first-deployment-run

## 20260805 — 完了条件を狭め（レジストリ + 最低限スモーク）

**決定**: 必須は deploy 成功・`deployments.md` 有効行 1・drift/harvest 可視・スキル一覧 + design-doc 承認停止。CLAUDE.md 発動ポリシー等は残タスク（非ブロッカー）。依存インストール阻害チェックは空フォルダのため実質スキップ可。
**理由**: BACKLOG の完了定義は有効行 1。tmpdir との差を出すには最低限の「使える」確認が要るが、空サンドボックスに本番スモークを必須にすると到達不能。
**影響**: Step 4 残タスクは案内するが tasklist の完了ゲートにしない。

## 20260805 — 配置セットは最小

**決定**: starter-kit「最小」8 スキル。レビュー厚み・統合運用・session-retrospective は入れない。
**理由**: スモーク（design-doc 停止）に十分。検証用パスに厚みを足さない。FCR は review-* 未配置で縮退動作でよい。
**影響**: フルモード 7 エージェント経路はこの実走では検証しない。

## 20260805 — 配置先パス

**決定**: `/Users/kentaro/Desktop/_lab/ai/skill-test`。配置前に `git init` のみ（アプリ本体なし）。
**理由**: ユーザー用意の検証用ディレクトリ。スクリプト前提（ディレクトリ実在）を満たす。git 無しだと `.gitignore` 追記の意味が薄い。
**影響**: company とは別。Frozen コメントは触らない。

## 20260806 — skill-test は registry に残置

**決定**: 検証完了後も登録解除しない。長期の実運用最小配置先として有効行 1 を維持する。ディレクトリを捨てるときは `deployments.md` からも行を消す（対運用）。
**理由**: 目的が「有効行 1」。解除すると再び 0 に戻る。プレモータムの「パス消失→exit 2」は残置＋パス維持なら起きない（消すときだけ行削除が要る）。
**影響**: harvest / drift の継続巡回対象が 1 件残る。完了条件に「解除」は入れない。

## 20260806 — 配置本実行の証跡

**決定**: `/Users/kentaro/Desktop/_lab/ai/skill-test` へ最小 8 スキルを本実行配置。source-commit `9379499`。`deployments.md` 正規化有効パス 1。`check_deploy_drift.py` exit 0（8/8 + hooks OK）。
**理由**: design 完了条件。
**影響**: registry 残置。company は未登録のまま。

## 20260806 — スモーク PASS（対話 CLI）

**決定**: 配置先で design-doc 明示 → DRAFT design.md / tasklist 作成 → 承認待ち停止・実装なし、を PASS とする。スキル一覧は目視 + `ls .claude/skills`（専用 list サブコマンドは無し）。
**理由**: ユーザー CLI ログで Phase 3 STOP 文言まで到達を確認。
**影響**: 完了条件のスモークを閉じる。

## 20260806 — Write(path) 死んだ規則を削除

**決定**: マスター `.claude/settings.json`・`DEPLOY_PERMISSIONS`・`MASTER_ONLY_PERMISSIONS` からパス付き `Write(...)` を削除。正本は `Edit(path)`（編集系ツールを覆う）。`check_asset_consistency` 契約 (j) で再発を機械検出。配置済み `skill-test` の settings も同内容に更新。starter-kit / claude-code-config / guard・remind hook 文言を同期。
**理由**: Claude Code はファイルパスを Edit/Read のみ参照。Write(path) は毎回起動時警告になる死んだ規則。Edit 対があればゲート実害は無かったが、ノイズと誤解（「Write も要る」）を残す。
**影響**: 新規配置は警告なし。既存配置先は再マージまたは手直しが要る（今回 skill-test は手直し済み）。

## 20260806 — PR レビューはユーザー担当（FCR スキップ）

**決定**: frontend-code-review エージェントは回さず、ユーザーが PR 上でレビューする。
**理由**: ユーザー指示「PR作成、僕がレビュー」。
**影響**: tasklist レビュー節をクローズ。指摘対応は pr-feedback。

