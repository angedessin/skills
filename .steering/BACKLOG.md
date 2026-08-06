# バックログ（固定パス・タスクディレクトリではない）

**なぜこのファイルがあるか**: 着手前のバックログをアーカイブ済みタスクの `decisions.md` に書くと、
`session-start-check.sh` が `archived/` を除外するため**次セッションから構造的に見えない**
（20260726 に 2 回続けて起きた）。アクティブタスクとして `.steering/[task]/` に置くと毎セッションの
コンテキスト固定費になるため、その中間としてこの 1 枚を置く。

**運用**: 着手するときは `design-doc` で `.steering/[YYYYMMDD]-[task]/` を作り、ここから該当節を移す。
完了したら該当節を**削除する**（何をどう解消したかの記録は `.steering/archived/[task]/` に残るので、
ここに履歴を積まない — 節数が増えると SessionStart の注入が「着手前の候補」を過大に見せる）。
**このファイル自体はアクティブタスク一覧に出ない。**

---

## 既知の文書ドリフト（タスクではない）

- **export/company MANIFEST 等の「書き込みのみ・削除は非対象」**: マスターは `guard-gated-delete` で削除・移動を deny するが、company / export は Frozen のため追随しない。**既知・今回非対応（追従タスクなし）**（`20260806-rm-mv-policy`）

---

## 1. 前タスクからの持ち越し（`20260725-skillset-hardening` 由来）

**一次情報**: `.steering/archived/20260725-skillset-hardening/decisions.md` のバックログ節

- ~~**(b) 配布機構の初回実走**~~ → **完了**（`20260805-first-deployment-run`。`/Users/kentaro/Desktop/_lab/ai/skill-test` へ最小セット配置・`deployments.md` 有効行 1）
- **(c) 構造改善** — `docs/knowledge/skill-design-patterns.md` が肥大化しており剪定対象
  （`rule-audit` の担当）。依存表の網羅・README のセットアップ節新設も含む
- **(d) `passthrough_check.py` のハーネス拡張** — `## setup` 節・サンドボックスでの `git init`。
  `feature-pipeline` の Gate 3.5 のような「外向き操作が副作用」の停止契約を判定可能にする

## 2. 既知の環境問題（タスクではない）

- ~~**`pnpm` のバイナリが壊れており実行できない**~~ → **解消済み（2026-07-31）**: 壊れていたのは `~/Library/pnpm` のスタンドアロン。リポジトリ直下の `mise.toml`（node 24.14.0 / pnpm 10.34.5）経由を使う。このディレクトリで mise が有効なら `pnpm` は mise 側が先に解決される。確認: `mise exec -- pnpm --version`

## 3. 20260730 レポート由来の後続（`report-driven-fixes` から切り出し）

**一次情報**: `.steering/archived/20260730-report-driven-fixes/design.md` 対象外 / `.tmp/reports/20260730-*-report.md`

- ~~**P1d** — フルモード用語の正本化（7 エージェント）と @参照配線の残骸（ADR 20260715 Context / rule-audit）~~ → **完了**（`20260730-p1d-terminology-at-refs`。starter-kit / user-guide / 関連 SKILL.md 含む）
- ~~**P2（契約/付録）**~~ → **完了**（`archived/20260731-design-contract-appendix`。PR #6 → integration）
- ~~**SPIKE レーン**~~ → **完了**（`archived/20260801-spike-lane` / PR #7 → integration）
- ~~**design↔実装の同期パス明確化**~~ → **完了**（`20260802-design-impl-sync`。方針転換分類表・乖離分類・Axis 1 High・FCR/pipeline ゲート入力・validate キー共存）
- ~~**ナレッジ鮮度の機械化**~~ → **完了**（`archived/20260804-knowledge-freshness-nudge` / PR #10 → integration。SessionStart 月次ナッジ）
- ~~**passthrough シナリオ拡充（Gate 1）**~~ → **シナリオ骨格のみ・未実走**（`20260806-passthrough-pipeline-gate1`。`tests/passthrough/feature-pipeline-gate1/`。課金実走は任意）。**残置**: `frontend-code-review` は 20260725 どおり落とし維持。Gate 3.5 は節 1(d) ハーネス拡張前提
