# Tasklist: workflow-hardening-slimming

Last updated: 20260611

## Implementation

### Group A — バグ修正（独立・先行）

- [x] frontend-code-review: Phase 1 の diff ベースを「base branch との merge-base + 未コミット」合算に変更
- [x] frontend-code-review: トリアージを `--name-status -M` ベースに修正 + 未マッチ→ロジック変更フォールバック
- [x] frontend-code-review: Phase 2A にディスパッチプロンプトのテンプレート新設（SKILL.md パス明記）
- [x] frontend-code-review: Phase 3 に同一 file:line 指摘の統合ルール追加
- [x] frontend-code-review: 再確認フローを「指摘があった軸のみの差分再レビュー」に置換
- [x] settings.json: `Read(./.env*)` 系 deny 追加 → `jq .` でパース確認 OK

### Group B — .steering スリム化（design-doc → templates → hook → 参照元の順）

- [x] design-doc: requirements.md 廃止、design.md に Goal/Scope/Acceptance 統合、複数セッション基準を明文化
- [x] templates.md: design.md テンプレート統合・requirements.md テンプレート削除・skill-issues.md テンプレート追加
- [x] session-stop.sh: フラグ作成のみに縮小 → `bash -n` OK + 一時リポジトリで3ケース（フラグ作成/重複なし/capture_done スキップ）検証 OK
- [x] steering SKILL.md + references/spec.md: requirements.md / session-log.md / .last-log-hash 参照削除（後方互換の注記のみ残す）
- [x] knowledge-capture: 入力を decisions.md / review-result.md / 会話コンテキストに変更
- [x] impl-from-design: requirements.md 参照なしを grep で確認（変更不要）

### Group C — 進化ループ強化

- [x] compound: Step 1 入力に skill-issues.md / codify-log.md 追加・session-log.md 削除
- [x] compound: Step 2 に codify-log.md × review-result.md 突合（昇格済みルールの再発検知）追加
- [x] CLAUDE.md: skill-issues.md 追記ルール追加

### Group D — README

- [x] README: 「ワークフロー図 + 各スキル概要 + SKILL.md リンク」構成にスリム化

### 横断検証

- [x] `grep -rn "requirements\.md\|session-log\.md\|last-log-hash" .claude/ CLAUDE.md README.md` → 残存ヒットはすべて意図的な後方互換の記述のみ
- [x] empirical-prompt-tuning を frontend-code-review に 1 イテレーション → 不明瞭点5件・実行不能1件を検出し、SKILL.md に4修正を適用（空スコープ規定・templates.md パス明記・モード提示の明確化・重要度閾値の定義）

## Review

- [x] frontend-code-review の実行（EPT の subagent が改訂版スキルを実行する形で実施。Low 5件検出）
- [x] レビュー指摘の修正（4件修正・1件は意図的と判断。review-result.md 参照）
- [x] 修正後の再確認（`jq` / `bash -n` で再検証。Status: RESOLVED）

## Deploy

- [x] コミット（remote なしのためローカルコミットのみ。1ac3743 / 38b5f98 ほかで完了済み）

## Compound

- [x] compound スキルの実行（パターンをルール・知識に昇格）

## Knowledge

- [x] knowledge-capture スキルの実行（docs/decisions/20260611-slim-steering-artifacts.md 作成）
- [x] steering archive モードでアーカイブ

Archived: 20260612
