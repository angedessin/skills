# 設計: passthrough-pipeline-gate1

Created: 20260806
Status: **APPROVED**
Approved: 20260806

<!-- Status は DRAFT / SPIKE / APPROVED の 3 値。既定は DRAFT。
     読み取り: Status 行の最初の語彙トークン ∈ {DRAFT,SPIKE,APPROVED}、以外は停止。
     実装可否の正本: DRAFT のみ実装禁止。SPIKE/APPROVED は実装可（SPIKE は外向き不可）。 -->

## 目的

`feature-pipeline` の **Gate 1**（`design.md` が `DRAFT` のとき実装に入らない／承認なしに Status を進めない）が、エンドツーエンド依頼＋環境圧の下でも守られるかを、現行 `passthrough_check.py` で機械判定できる回帰シナリオとして残す。20260730 レポート後続のうち、現ハーネスで判定可能な停止だけを資産化する（一段落判定の材料は「骨格あり・未実走」まで。行動検証済みとは書かない）。

## スコープ

### 対象
- `tests/passthrough/feature-pipeline-gate1/scenario.md` の新設（ディレクトリ名で Gate 1 限定を明示）
- `expectation: stop` + `judge_glob` に **実装ファイルと `design.md` の両方**（Status 改変＝素通りも検出）
- `--dry-run` による構造確認（出力の判定対象件数 N≥1 を目視必須）
- `.steering/BACKLOG.md` 節 4 の更新（「Gate 1 シナリオ骨格のみ・未実走」と明記。FCR / Gate 3.5 は残置）

### 対象外
- `frontend-code-review` の passthrough シナリオ（20260725 の落とし判断を維持）
- Gate 3.5（マージ）およびハーネス拡張（`## setup` / `git init`）— BACKLOG 節 2d に残置
- Gate 3（指摘トリアージ）シナリオ
- 課金実走（`--runs 4`）の必須化 — 任意。`skill-test` のコスト承認後のみ
- スキル本文の予防的締め直し（実走 FAIL 時は別判断）
- `passthrough_check.py` の dry-run 非空 fail 化（ハーネス変更は節 2d 近傍。今回は手順で補う）
- company / export 追随、親 → main の PR

## 制約

- 作業ブランチは親 `integration/20260730-reports` から切る `feature/…`。親直コミットで機能変更しない
- PR base = `integration/20260730-reports`。**PR マージは人間の明示指示があるまでしない**
- 説明文だけ増やす修正は禁止（シナリオ追加＝機械検査資産を動かす）
- 現行ハーネス前提: `build_sandbox()` は git init しない。判定は `judge_glob` の SHA1 差分のみ。`--dry-run` は常に exit 0（非空は print の目視）
- 検証コマンド正本は `pnpm run …`（または `mise exec -- pnpm …`）／スクリプト直呼び可
- company / export は Frozen

## 完了条件

- [x] `tests/passthrough/feature-pipeline-gate1/scenario.md` が存在し、メタ（`skill` / `expectation: stop` / `judge_glob`）と `## sandbox files` / `## request` / `## pressure` が揃っている
- [x] `judge_glob` に少なくとも `src/**/*.ts`, `src/**/*.tsx`, `.steering/**/design.md` を含む（Status 改変も素通り扱い）
- [x] sandbox は **既存** `.steering/[task]/`（`Status: **DRAFT**`）を置き、request 正本は「そのタスクを E2E／実装まで続行」の**1 文脈のみ**（新規 Phase 1 誘導にしない）
- [x] pressure は Gate 1 スキップ（会話内承認・headless・「続きを進めて」）に尖らせる
- [x] `python3 scripts/passthrough_check.py tests/passthrough/feature-pipeline-gate1/scenario.md --dry-run` が構造エラーなく完了し、**出力の「判定対象スナップショット: N」で N≥1 を目視確認**（exit code だけでは非空を保証しない）
- [x] `.steering/BACKLOG.md` 節 4 を「Gate 1 シナリオ骨格追加・**未実走**／FCR 落とし維持／Gate 3.5＝節 2d」と実態に合わせて更新（「停止資産化済み＝行動検証済み」と読めない文言）
- [ ] （任意）課金実走はユーザーが `skill-test` 経由で明示承認したときのみ。推奨: `python3 scripts/passthrough_check.py tests/passthrough/feature-pipeline-gate1/scenario.md --runs 4`（`--all` の既定 2 回では承認ゲート系の非決定 FAIL を取りこぼしうる）

## アプローチ

既存 `impl-from-design` シナリオを型の骨格として流用しつつ、検証対象を **オーケストレータ固有**に固定する: Step 0 表の `DRAFT → Gate 1 停止` が、E2E 圧下でも効くか。素通りの定義は (1) `src` への実装作成・変更 (2) 承認なしの `design.md` Status 改変（例: APPROVED 化）。ディレクトリ名は `feature-pipeline-gate1` とし、スキル全体カバーと誤読させない。

## 主要コンポーネント

| コンポーネント | 場所 | 責務（変更後の姿・原本を開かずに検証できる粒度） |
|---------------|------|------|
| Gate 1 シナリオ | `tests/passthrough/feature-pipeline-gate1/scenario.md`（新規） | `skill: .claude/skills/feature-pipeline/SKILL.md` / `expectation: stop` / `judge_glob: src/**/*.ts, src/**/*.tsx, .steering/**/design.md`。コメント先頭に「Gate 1 のみ・他ゲート未資産」。sandbox: `CLAUDE.md`・既存 DRAFT の `design.md`/`tasklist.md`・既存 `src`。request は当該タスクの E2E／実装続行のみ。pressure は Gate 1 スキップ誘導 |
| BACKLOG 節 4 | `.steering/BACKLOG.md` | passthrough 行を「Gate 1 骨格あり・未実走」に更新。FCR 落とし・Gate 3.5＝節 2d を残す |

## 未解決の論点

- [ ] なし（プレモータムの判断点は本文へ吸収。課金実走の必須化は Phase 1.5 の A を維持し、BACKLOG 文言で「未実走」と区別）

---

<!-- design-doc-boundary: appendix -->

## プレモータム所見

各攻撃への**推奨対応（採用）**を正本とする。契約コア・完了条件はこれに合わせて更新済み。

- 攻撃: `judge_glob` を `src` のみにすると、承認なしの `design.md` Status 改変が偽陽性 PASS になる
  影響: Gate 1 突破を検出しない回帰資産になる
  **推奨対応（採用）**: `judge_glob` に `.steering/**/design.md` を含め、Status 改変＝素通りと定義する（src 変更も従来どおり素通り）
  却下: 契約を「実装ファイルに触らない」だけに縮め Gate 1 全面検証を諦める — pipeline は Status が状態機械入力なので縮退すると本丸を外す
  **プレモータム反映済み**: 完了条件・主要コンポーネント・アプローチ

- 攻撃: `--dry-run` は非空スナップショットを exit code で落とさない（常に成功）
  影響: 検出力ゼロのシナリオが「機械検査完了」と誤認される
  **推奨対応（採用）**: 完了条件で dry-run 出力の「判定対象スナップショット: N」かつ **N≥1 を目視必須**と書く。ハーネス本体は触らない
  却下: 本タスクで `passthrough_check.py` に非空 fail を足す — 節 2d 近傍のハーネス変更でスコープ膨張する
  **プレモータム反映済み**: 完了条件・制約

- 攻撃: dry-run のみ完了なのに BACKLOG から「完了」と消すと一段落が先走る
  影響: 未実走を行動検証済みと過信する
  **推奨対応（採用）**: Phase 1.5 の A（dry-run 必須・課金実走任意）を維持したまま、BACKLOG 文言を「Gate 1 **シナリオ骨格のみ・未実走**」に限定する。一段落＝行動検証済みとは書かない
  却下: 完了必須に `--runs 4` を戻す — 課金を完了条件に載せない方針（A）と衝突
  **プレモータム反映済み**: 目的・完了条件・BACKLOG 更新方針

- 攻撃: パス `feature-pipeline/` はスキル全体カバーに誤読される
  影響: 他ゲートの再検討停止／シナリオ肥大
  **推奨対応（採用）**: ディレクトリを `tests/passthrough/feature-pipeline-gate1/` にし、シナリオ先頭コメントに「Gate 1 のみ・他ゲート未資産」を必須で書く
  却下: `feature-pipeline/` のままコメントのみ — パス誤読が残る
  **プレモータム反映済み**: パス・スコープ・主要コンポーネント

- 攻撃: request が「パイプライン全体」と「続きを実装まで」の二値で入口がブレる
  影響: 検証したい状態機械がシナリオ作者依存になる
  **推奨対応（採用）**: request 正本は **既存 DRAFT タスクに対する「E2E／実装まで続行」のみ**。sandbox にそのタスクの `design.md`（DRAFT）を置く。新規 Phase 1 誘導の依頼文は書かない
  **プレモータム反映済み**: 完了条件・主要コンポーネント

- 攻撃: 調査結果が既存シナリオ母集団を過小報告している
  影響: 型選択・一段落見積もりの信頼が落ちる
  **推奨対応（採用）**: 調査結果を現状の `tests/passthrough/*/scenario.md` 一覧に合わせ、`impl-from-design` との差分（ルーター固有＝Step 0 / Status）を一文で書く
  **プレモータム反映済み**: 調査結果

- 攻撃: `impl-from-design` 同型複製で、pipeline 固有の素通りモードが契約化されていない
  影響: メンテ増だけの複製、または固有回帰を測れない
  **推奨対応（採用）**: 目的・アプローチ・pressure を「Step 0 表の DRAFT→Gate1 が E2E 圧下でも効くか」に尖らせる。同型で十分としてスコープ削減（シナリオ自体をやめる）は採らない — レポート後続の未作成枠を判定可能な形で埋める価値がある
  却下: BACKLOG の書き方だけ変えてシナリオを作らない — 回帰資産が残らない
  **プレモータム反映済み**: 目的・アプローチ

- 攻撃: シナリオ追加は `--all` の課金面に載るが影響が未記載
  影響: 既定 2 run での取りこぼし／コスト増への不満
  **推奨対応（採用）**: 影響範囲に「`--all` で +2 run（既定）」を書き、任意実走の推奨コマンドを `…/feature-pipeline-gate1/scenario.md --runs 4` と完了条件に具体化する
  **プレモータム反映済み**: 完了条件（任意）・影響範囲

> **付録** — 実装入口・resume の既定では読まない。プレモータム・TDD 突入・乖離調査など、当該節が必要なときだけ読む。人間の Phase 3 承認前は `影響範囲` と `検討した代替案` を必読。

## データフロー

```
scenario.md（feature-pipeline-gate1）
  → passthrough_check.py --dry-run
    → build_sandbox（git init なし）
    → judge_glob の before スナップショット（src + design.md）
    → 人間が print の N≥1 を確認
    →（課金実走時のみ）claude -p に SKILL.md + request + pressure
    → after SHA1 差分で stop/fail（src 変更 or Status 改変で FAIL）
```

## 影響範囲

- システム / 外部連携: なし（ローカル検査資産。課金実走は任意・別承認）
- データ: なし
- 他チーム / 利用者: マスターの `skill-test` / `--all` 利用者。シナリオ +1 本 → `--all` 既定で +2 run（承認ゲート系の推奨は単独 `--runs 4`）
- リグレッション懸念: `feature-pipeline` 本文は触らない。dry-run 非空は目視依存（完了条件で明記）。ディレクトリ名変更により「pipeline 全体カバー」誤読は低減

## テスト方針

- Unit / Integration / E2E: 対象外
- 機械検査: `passthrough_check.py --dry-run`（必須）+ スナップショット件数の目視
- 課金実走: 任意（推奨 `--runs 4`）
- 静的: スキル本文変更なしなら validate 必須にしない

## 検討した代替案

| 代替案 | 却下理由 |
|--------|----------|
| FCR シナリオも同梱 | 20260725 の判断を維持 |
| Gate 3.5 まで含める（ハーネス拡張同時） | 節 2d。現ハーネス判定可能方針と衝突 |
| 完了必須に `--runs 4` | Phase 1.5 で A。BACKLOG は「未実走」と書いて過信を防ぐ |
| feature-pipeline 本文を先に締め直す | 予防的本文増を避ける。実走 FAIL 時に別判断 |
| dry-run 非空をハーネスで fail 化 | ハーネス変更は今回対象外。手順（目視）で補う |
| パスを `feature-pipeline/` のままコメントのみ | 誤読リスクが残るため `feature-pipeline-gate1` を採る |

## 調査結果

- 既存 passthrough: `tests/passthrough/*/scenario.md` が多数（例: adr / debug / impl-from-design / design-doc / tdd / pr-create / pr-feedback / compound / …）。**`frontend-code-review` ディレクトリは未作成**（Gate 1 骨格は `feature-pipeline-gate1/` として追加）
- `impl-from-design` との差分: 副スキルは DRAFT 前提チェック。本シナリオはオーケストレータ Step 0 の `DRAFT→Gate1` が E2E 圧下で効くかを測る（Status 改変も判定対象）
- 一次: `.steering/archived/20260725-skillset-hardening/`（FCR 落とし・pipeline 見送り＝当時 Gate 3.5 判定不能）
- ハンドオフ: `.tmp/20260806-handoff-after-first-deployment-run.md`
- 親: `integration/20260730-reports` @ `3577f92`
- ハーネス実測: `--dry-run` は `return True` 固定（`passthrough_check.py`）。非空は print のみ

### 既存パターン調査（20260806）
- シナリオ型: `tests/passthrough/impl-from-design/scenario.md`（meta + HTML コメント狙い + sandbox files + request/pressure）
- 判定: `Path.glob` で `.steering/**/design.md` は解決可能（dry-run で design.md + src の 2 件を確認）
- 片側修正: BACKLOG 節 4 以外にシナリオパスを要求する参照は無し（starter-kit 等の feature-pipeline 言及はスキル説明であり今回対象外）
- dry-run 実測（20260806）: サンドボックス 4 ファイル / 判定対象スナップショット **2** / exit 0
