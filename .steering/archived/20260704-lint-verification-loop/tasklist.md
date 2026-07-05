# Tasklist: lint-verification-loop

Last updated: 20260705

## Implementation

- [x] `.claude/hooks/post-edit-lint.sh` 作成（linter 自動検出・編集ファイルのみ・exit 2 差し戻し）
- [x] `.claude/hooks/stop-typecheck.sh` 作成（tsconfig 検出・incremental・stop_hook_active ガード）
- [x] `.claude/settings.json` に配線（PostToolUse: Edit|Write / Stop: 2 本目、タイムアウト明示）
- [x] `bash -n` + shellcheck（あれば）+ `jq` で settings.json パース確認（shellcheck 未導入のためスキップ）
- [x] 設定・ツール不在時の no-op 確認（biome 未導入・tsconfig なし・file_path なしの 4 ケースで exit 0 を確認）

## Verification（リポジトリルート）

- [x] ルートに `package.json`（private）を作成（biome.json・.gitignore の *.tsbuildinfo も配置済み）
- [x] ユーザーに `! pnpm add -D @biomejs/biome typescript` の実行を依頼（20260705 実施: biome 2.5.2 / typescript 6.0.3）
- [x] `biome.json` をルートに常設配置
- [x] lint 違反編集 → 差し戻し → 自己修正 → 通過のループ確認（スクリプト直接実行で機構検証済み。整形通知 A / 差し戻し B / 修正後通過も確認）
- [x] 一時 tsconfig + 一時 TS ファイルで型エラー → Stop 差し戻し → 修正 → 通過の確認 → 撤去（tsc 実測約 1 秒）
- [x] stop_hook_active ガードの動作確認（true 時は警告のみで exit 0 を確認）
- [x] セッション再起動後、実 hook 発火での生ループ確認（20260705 実施: PostToolUse 差し戻し / reformatted 通知 / Stop 差し戻し・通過の3点とも実 hook 発火で確認済み）

## Docs / Deploy

- [x] docs/knowledge/claude-code-config.md に配布手順（コピー対象・settings スニペット・tsc 閾値ルール）を追記（design.md 承認済みスコープ）
- [x] コミット（276dcad — hook 2 本 + settings + biome/package/lockfile + docs + .steering）

## Compound

- [x] compound スキルの実行（hook 作成で得たパターンの昇格判断。20260705: Stop hook 発火特性を docs/knowledge/claude-code-config.md に追記、他2件は既存反映済みのため見送り）

## Knowledge

- [x] knowledge-capture スキルの実行（20260705: hook 出力の AI 向け設計原則 → claude-code-config.md、Biome 採用 ADR → docs/decisions/、レビュー軸重複分析 → docs/knowledge/review-workflow.md 新規）
- [x] steering archive モードでアーカイブ
