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

## 1. rm / mv ポリシーの再設計

**起票**: 2026-07-26（`20260726-deploy-integrity` から切り出し・ユーザー判断）
**一次情報**: `.steering/archived/20260726-deploy-integrity/design.md` の「対象外 — rm / mv ポリシーの再設計」節
**優先度**: 中（実害は出ていないが、承認ゲートに整合性の穴がある）

### 目的

承認ゲート（`CLAUDE.md` / `docs/knowledge/` / `docs/decisions/`）は**書き込みだけを塞ぎ、削除・移動は素通し**。
`rm -f docs/knowledge/x.md` が実測で素通りした。かつ permissions の前置一致には flag の網羅漏れがある
（`rm -R` / `rm --recursive` / `rm -f -r` がどのルールにも当たらない）。

### 確定済みのユーザー決定

| 論点 | 決定 |
|---|---|
| 判定を deny か ask か | **`deny` を使う**（プレモータムが提案した「ask に統一」は採らない） |
| 判定精度の問題 | このタスク側で扱う |
| 位置づけ | 配置機構の修復とは独立。混ぜると配布のブロッカーが増える |

### 必ず持ち越す技術的制約（公式 docs で裏取り済み・**再調査しない**）

1. **PreToolUse hook は permissions より先に評価される。** hook が沈黙すると通常の permission flow に
   進むため、**hook は permissions の deny を救済できない**（`permissionDecision: "allow"` を返さない限り）。
   したがって permissions に置く deny は「守りたい範囲の外にだけ当たる形」でなければならない —
   **`Bash(rm -rf /*)` は前置一致で `rm -rf /Users/<...>/<project>/.tmp` にも当たるので使えない**
2. **入力 JSON には `transcript_path`・`cwd`・`tool_input.description` が必ず含まれる**ため、
   **全文検査でパス判定はできない**（プロジェクト外の絶対パスが恒常的に入っている）。
   `tool_input.command` の構造抽出が必須（`remind-config-docs.sh:31` の `grep -o` + `sed` で `jq` 非依存にできる）
3. `permissionDecision` に指定できる値: `allow` / `deny` / `ask` / `defer`
4. **非対話モード（`claude -p`）では hook の `ask` は deny に落ちる**（`docs/knowledge/claude-code-config.md`）。
   `guard-gated-write.sh` は全配置先に無条件同送されるため、配置先の CI で誤検知すると原因の遠い障害になる
5. 20260726 の実測では現行の全文検査 hook は `transcript_path` に巻き込まれていない（発火 13/13・誤検知 0）。
   ただしこれは「`.env` を含むか」「リダイレクト先が対象パスか」を見ているからで、
   **パス判定を足した瞬間に成立しなくなる**

### 併せて塞ぐべき穴

- **`mv` は削除と等価にゲートを破る**（`mv docs/knowledge/x.md /tmp/`）
- `sed -i` / 任意インタプリタ経由は脅威モデル外（敵対者ではなく滑った善意のエージェント）

### 波及

- `guard-gated-write.sh` のリネーム是非（書き込み以外も見るなら名前がずれる）。20260726 時点では
  **リネームしない**と決めた（rm / mv を切り出したので名前と実態が一致した）。このタスクで再検討する
- 配布物側の同名 hook にも同じ変更が要る。**契約 (g) が差分を検出するので片側修正は落ちる**
- 配布物の `MANIFEST.md` に「対象は書き込みのみ・削除は非対象」と明記済み。変更したらここも直す
  （契約は文書の本文までは見ない）

---

## 2. 前タスクからの持ち越し（`20260725-skillset-hardening` 由来）

**一次情報**: `.steering/archived/20260725-skillset-hardening/decisions.md` のバックログ節

- **(b) 配布機構の初回実走** — 外部プロジェクトへの実配置。20260726 に tmpdir への実配置で
  機構の動作は実証したが、**実際の配置先はまだ 0 件**（`deployments.md` の有効行 0）
- **(c) 構造改善** — `docs/knowledge/skill-design-patterns.md` が **45KB** に増えており剪定対象
  （`rule-audit` の担当）。依存表の網羅・README のセットアップ節新設も含む
- **(d) `passthrough_check.py` のハーネス拡張** — `## setup` 節・サンドボックスでの `git init`。
  `feature-pipeline` の Gate 3.5 のような「外向き操作が副作用」の停止契約を判定可能にする

## 3. 既知の環境問題（タスクではない）

- ~~**`pnpm` のバイナリが壊れており実行できない**~~ → **解消済み（2026-07-31）**: 壊れていたのは `~/Library/pnpm` のスタンドアロン。リポジトリ直下の `mise.toml`（node 24.14.0 / pnpm 10.34.5）経由を使う。このディレクトリで mise が有効なら `pnpm` は mise 側が先に解決される。確認: `mise exec -- pnpm --version`

## 4. 20260730 レポート由来の後続（`report-driven-fixes` から切り出し）

**一次情報**: `.steering/archived/20260730-report-driven-fixes/design.md` 対象外 / `.tmp/reports/20260730-*-report.md`

- ~~**P1d** — フルモード用語の正本化（7 エージェント）と @参照配線の残骸（ADR 20260715 Context / rule-audit）~~ → **完了**（`20260730-p1d-terminology-at-refs`。starter-kit / user-guide / 関連 SKILL.md 含む）
- ~~**P2（契約/付録）**~~ → **完了**（`archived/20260731-design-contract-appendix`。PR #6 → integration）
- ~~**SPIKE レーン**~~ → **完了**（`archived/20260801-spike-lane` / PR #7 → integration）
- ~~**design↔実装の同期パス明確化**~~ → **完了**（`20260802-design-impl-sync`。方針転換分類表・乖離分類・Axis 1 High・FCR/pipeline ゲート入力・validate キー共存）
- **design.md 境界の任意追記** — アクティブ design への `<!-- design-doc-boundary: appendix -->` 追記は任意・強制しない（マーカー無しは全文フォールバックのまま）
- **capture 粒度** — `.capture-needed` の「完了時」と「セッション知見あり」の分離（偽陰性を増やさない）
- **ナレッジ鮮度の機械化** — rule-audit 常用化が第一歩
- **配置1件実走** — `deployments.md` 有効行を 1 にする（company はカウントしない）
- **passthrough シナリオ拡充** — adr / debug / feature-pipeline / impl-from-design / frontend-code-review
