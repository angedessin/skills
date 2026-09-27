# タスクリスト: report-driven-improvements

Last updated: 20260927

## 0. 主要コンポーネントの確定（実装の一部・最初にやる）

- [x] `grep -rn "capture_done" .claude/ scripts/ tests/ docs/ README.md` で consumer を機械的に洗い出し、design.md の「5 箇所」に漏れがないか確定する
- [x] `grep -rn "判定表\|現在地\|Phase 3.5\|Phase 3.7" .claude/ README.md docs/` でフェーズ順序を書いている箇所（README のワークフロー図を含む）を洗い出す
- [x] `grep -rn "tasklist" .claude/skills/*/SKILL.md .claude/skills/*/references/*.md` で tasklist テンプレの写しがある箇所を確定する（正本は `design-doc/references/templates.md`）
- [x] `grep -rn "subagent\|サブエージェント\|エージェント\|code-explorer" .claude/skills/ scripts/` でサブエージェント起動・モデル指定の記述箇所を再確認する（design.md の棚卸し表に漏れがないか）

## 1. P0 — 状態機械（Critical 2 件 + High 1 件）

- [x] `tests/state/` を作り、**現行の判定表の意味を写した** `resolve_phase()` と table-driven test を書く（この時点で到達可能性テストが FAIL することを確認 = Critical 1 の再現）
- [x] capture 2 段のテストケースを追加し、FAIL することを確認する（Critical 2 の再現）
- [x] `feature-pipeline/SKILL.md` の判定表を修正（3.7 を 3.5 の上へ・行 ID 付与・capture 2 段）→ テストが PASS することを確認
- [x] `design-doc/references/templates.md` のデプロイ節に `PR:` / `CI:` / `Feedback:` の 3 行を追加
- [x] `knowledge-capture/SKILL.md` に PR 前 / 最終の分岐と `pr_capture_done` の書き込みを追加
- [x] `steering/SKILL.md` / `steering/references/spec.md` にフラグを追加し、tasklist テンプレを正本と同一工程順へ同期
- [x] `.gitignore` と `scripts/deploy_skills.py` の除外リストに `pr_capture_done` を追加
- [x] `check_asset_consistency.py` に検査 (11) 表↔関数 / (12) spec↔templates を追加し、`:50-56` の「順序は検査対象外」コメントを削除
- [x] （レビュー I1 で判明した脱落）`pr_capture_done` / `capture_done` の producer / consumer 突合を契約 (r) として追加

## 2. P1 — CI

- [x] `.github/workflows/validate.yml` を作成（validate / assets / portability / hooks / lint / passthrough dry-run / tests/state）
- [x] portability 警告 2 件を先に解消してから strict 扱いにする（`templates.md:137` / `feature-pipeline/SKILL.md:236` の日付エピソード。行番号は 20260921 時点）
- [x] ローカルで全コマンドが CI と同じ順で通ることを確認する

## 3. P1 — モデル / エフォート / 権限（全ディスパッチ箇所）

- [x] `.claude/agents/` にレビュー 7 軸の定義を作成（`tools` は読み取り専用・`effort` は軸ごと・`skills` でサブスキルをプリロード）
- [x] `premortem-attacker`（opus / high）・`codebase-explorer`（haiku / low）・`tournament-variant`（sonnet）・`tournament-scorer`（opus / high）・`knowledge-scanner`（haiku / low）を作成
- [x] `compound/SKILL.md` の Step 1 / Step 4 を `knowledge-scanner` へのディスパッチに置き換え（Step 2 の昇格判断は本体に残す・定義が無い環境のフォールバックを明記）
- [x] `frontend-code-review` / `impl-from-design` / `design-premortem` / `impl-tournament` の本文を「役割名で指す + 定義が無ければ従来フォールバック」に統一
- [x] `impl-tournament/references/commands.md:35-36` の散文でのモデル指定を削除し、定義側に移したことを明記
- [x] `empirical-prompt-tuning/SKILL.md` に「実行者はセッション設定を継承させる（指定しない）」理由を 1 行追記
- [x] `grep -rn "Haiku 相当\|Opus 相当\|安価なモデル" .claude/skills/` が 0 件になることを確認
- [x] `check_asset_consistency.py` に検査 (13) SKILL.md↔agent 定義の突合を追加
- [x] agent 定義の frontmatter 検査（必須キー・読み取り専用定義に書き込みツールが混ざらないこと）を追加
- [x] （スキップ）スキル frontmatter への `model` / `effort` 明示 — 論点 3 の結論が「入れない」（decisions.md 20260920）。よって上の `validate_skills.py` 確認は「新フィールドを足していないので既存検査が通る」ことの確認にとどまる
- [x] `validate_skills.py` が新フィールドで落ちないことを確認（必須キーのみ検査の想定を実地確認）

## 3b. P1 — passthrough のモデル可変化

- [x] `scripts/passthrough_check.py:51` の `--model sonnet` 固定を CLI 引数化（既定は現行維持）
- [x] 実走結果に使用モデルを記録するようにし、`skill-test/references/passthrough-testing.md` の測定ログ書式を同時改訂
- [x] dry-run が従来どおり 21/21 通ることを確認（課金実走はしない）

## 4. P1 — 参照分離

- [x] `design-doc/SKILL.md` の「SPIKE レーン」→ `references/spike-lane.md`、「方針転換が起きた場合」→ `references/pivot.md`
- [x] `feature-pipeline/SKILL.md` の PR 関連詳細 → `references/pr-phases.md`
- [x] 分離後に本文からポインタで参照されていること・`validate` が通ることを確認

## 5. 衛生改善（P3）

- [x] `biome migrate` を実行し `biome.json` を現行キーへ移行
- [x] `remind-config-docs.sh` の注入要約と `docs/knowledge/claude-code-config.md` のドリフト検査を `check_asset_consistency.py` に追加

## 6. 配置先ドリフト（分類まで）

- [x] `skill-harvest` で配置先 2 件のドリフト 14 件を分類（直接編集 / マスター先行 / 記録なし）
- [x] 配置先固有スキル `next-dev-loop` の還流可否を判断材料として提示
- [x] 再コピー / 取り込みの方針をユーザーに提示（**実行は承認後。本タスクの完了条件は提示まで**）

## 7. C 群の判断材料（実測）

- [x] （BACKLOG へ移設・20260927）マスターリポジトリで `/skill-doctor` を実行し結果を記録 — ユーザー側実行待ちでクローズを止めないため、`BACKLOG.md` の C 群節へ移した
- [x] （BACKLOG へ移設・20260927）配置先プロジェクトで `/skill-doctor` を実行し結果を記録 — 同上
- [x] `frontend-code-review` のフルモード発動頻度と、承認ゲートでの停止回数の観測方法を決めて記録する
- [x] `BACKLOG.md` に「C 群（データ待ち）」の節を作り、対象外 7 項目と必要な実測を書く

## レビュー

- [x] frontend-code-review の実行（対象: Python スクリプト・SKILL.md・agent 定義・CI の差分。impl / correctness / security の 3 軸・ユーザー承認済み）
- [x] レビュー指摘の修正（review-result.md を参照。27/32 件を修正。残りは I3 未達の記録・I4 ユーザー側実行待ち・I6 ADR・S4 受容して記録・S7/S8 ユーザー判断）
- [x] 修正後の差分再レビュー（20260927・重点 4 件 S1/S2/C1/I9 に限定 + 静的検査全緑。review-result.md のサマリー参照）

## 知見保存（この PR / ブランチに載せる分）
<!-- この変更の説明・落とし穴として残す knowledge は、マージ前に同じブランチへ含める。 -->

- [x] knowledge-capture スキルの実行（PR 差分に属する知見）— 20260927 の最終 capture に包含
- [x] 必要なら docs/ への追記をこのブランチでコミット（main 直コミット運用・最終 capture の追記と同時にコミット）

## デプロイ
<!-- このリポジトリは main へ直接コミット。PR は明示要求時のみ。 -->

- [x] main へのコミット（20260927・テーマ別 4 コミット: 7f00cff 状態機械 / 4d4e44d agent 定義 / 225fe85 参照分離 / bd65b72 CI・検査）
- [x] CI グリーン確認（20260927・run 36321311662 で全ステップ green。注記: actions v4 の Node 20 deprecation）
- PR: none
- CI: green
- Feedback: no

## 福利化

- [x] compound スキルの実行（パターンをルール・知識に昇格）— 20260927・codify-log.md 参照

## クローズ

- [x] knowledge-capture（会話由来・横断の残りがあれば）— 20260927 最終 capture（claude-code-config・environment-setup-patterns・BACKLOG 0.5）
- [x] steering archive モードでアーカイブ

Archived: 20260927
