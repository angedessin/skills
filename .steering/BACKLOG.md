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
1
## 0.5 CI の actions 更新（期限あり: 2026-10-19）

- `actions/checkout@v4` / `setup-node@v4` / `pnpm/action-setup@v4` に Node 20 deprecation の注記（run 36321311662）。Node 24 対応のメジャーへ上げ、SHA 固定するかも判断する（`20260917-report-driven-improvements` の decisions 20260921「確認手段が無いため固定しない」の再検討）
- ubuntu-latest は 2026-10-19 から Ubuntu 26 へ移行する。移行後の初回 run を確認する

---

## 0.6 guard-gated-delete の取りこぼし（`20260927-gate-bypass-s7-s8` のレビュー由来・Low）

- 対象パスの照合が大文字小文字を区別する。`rm CLAUDE.MD` は沈黙するが、macOS の既定のファイルシステムでは実ファイルが消える（write hook は 20260929 に `re.I` で対処済み）
- 先頭トークンで rm / mv を判定するため、`FOO=1 rm docs/knowledge/x.md` のような代入前置で沈黙する。ヘッダの「守らない形」にも載っていない
- delete は deny なので、誤検知の代償が write（ask）より大きい。直すときはフィクスチャの silence ケースを先に厚くする

---

## 1. 前タスクからの持ち越し（`20260725-skillset-hardening` 由来）

**一次情報**: `.steering/archived/20260725-skillset-hardening/decisions.md` のバックログ節

- ~~**(b) 配布機構の初回実走**~~ → **完了**（`20260805-first-deployment-run`。`/Users/kentaro/Desktop/_lab/ai/skill-test` へ最小セット配置・`deployments.md` 有効行 1）
- **(c) 構造改善** — ~~`docs/knowledge/skill-design-patterns.md` の肥大化~~ → **完了**
  （`20260811-skill-patterns-split`。562 → 460 行。素通り検査の運用手順と測定ログを
  `skill-test/references/passthrough-testing.md` へ分離）。**残**: 依存表の網羅・
  README のセットアップ節新設
- **(d) `passthrough_check.py` のハーネス拡張** — `## setup` 節・サンドボックスでの `git init`。
  `feature-pipeline` の Gate 3.5 のような「外向き操作が副作用」の停止契約を判定可能にする

## 1.5 rule-audit の監査スコープ拡張（20260811 のプレモータム由来）

- **`rule-audit` の Step 1 入力に `.claude/skills/*/references/` を足す** — 現在の入力は
  CLAUDE.md / `docs/knowledge/` / スキル frontmatter で、`references/*.md` は削除テストにも
  鮮度チェックにもかからない。`20260811-skill-patterns-split` が測定ログを
  `skill-test/references/passthrough-testing.md` に置くため、監査されない知識の置き場が生まれる。
  深刻度は低い（測定ログは課金して passthrough を回したときしか増えない）が、
  `references/` を持つスキルは 10 本あり、他にも腐りうる。一次情報:
  `.steering/20260811-skill-patterns-split/design.md` のプレモータム所見

## 1.6 福利化候補（`20260811-skill-patterns-split` の `.codify-needed` から移設）

アーカイブすると `session-start-check.sh` がフラグを拾わなくなる（`archived/` を除外するため）ので、
`compound` を回す代わりにここへ移した。候補は 1 件で内容は確定している。

- **`tasklist.md` を一括更新した後、実体を確認していない項目に `[x]` が付いていないか検証する** —
  20260811 に 33 件を一括チェックした際、`review-workflow.md` の重複解消が**未了なのに `[x]` が付いた**
  （スクリプトのマッチが別の行に当たった）。手で戻したが、気づかなければ「確認済み」という嘘が
  タスク記録に残っていた。CLAUDE.md の「手作業で突合した検証項目は機械検査に入れるか
  『一回限り』と明記する」の隣に来る行動ルール候補。昇格先は CLAUDE.md の「自律実行の境界」節が有力。
  一次情報: `.steering/archived/20260811-skill-patterns-split/`

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

## 4. C 群（データ待ち）— `20260917-report-driven-improvements` で対象外にした 7 項目

**一次情報**: `.steering/20260917-report-driven-improvements/design.md` の「対象外」節と `decisions.md`。
いずれも「判断材料が未収集」または「実環境での検証が要る」ため、今決めると決定ではなく推測になる。**必要な実測を取ってから着手する**。

| 項目 | 待っているデータ | 状況 |
|---|---|---|
| 承認ゲート再編 | ゲートごとの停止回数と、停止後のユーザー応答が「承認のみ」か「修正指示あり」か。停止契約は `passthrough_check.py` の検査対象でもあり、記録なしに削ると安全側の設計を勘で削ることになる | **未計測**。観測方法: 実行したパイプラインの transcript から、`▣ Gate` / 「ここで止まる」で終わる assistant ターンの数と直後のユーザー発話を数える（手順のみ決定・スクリプト化は未着手） |
| sandbox 有効化・subagent の最小権限の全面適用 | 有効化した状態で開発コマンドが通るかの実走（副作用の検証）。レビュー agent の読み取り専用化は `.claude/agents/` で実施済み | 未着手 |
| 配布方式の plugin 化再評価 | 移行の可否判断そのものが調査タスク。配置先ドリフトの解消とは独立に進められる | 未着手 |
| レビュー軸の拡張（shell / Python 向け） | フルモードの発動頻度と、軸ごとのディスパッチ実績（2 レポートが正面衝突する唯一の箇所） | **部分計測**（下記）。フロントエンド製品タスクでの実績は未取得 |
| `review-performance` と `review-security` の統合 | 同上。加えて軸ごとの effort（security = high / performance = medium）を持たせたため、統合は effort の粒度を失う方向に働く | 上と同じ |
| `compound` を `context: fork` でスキルごとフォークする案 | 知識走査は `knowledge-scanner` の隔離で目的（メイン文脈から知識全文を外す）を達成済み。fork 化はスキル追加（29 → 30 本）を伴う | `compound` の実行で走査コストが実際に下がったかを見てから |
| `disable-model-invocation` / `skillOverrides` によるマスター専用スキルの絞り込み | マスターと配置先での `/skill-doctor` の実測（レポート自身が順序を指定） | **ユーザー側で実行待ち**（下記） |

### 計測済みのデータ（20260921・一回限りの手集計）

- **フルモード発動頻度**: アーカイブ済み 33 タスクのうち `review-result.md` があるのは 11 件。うちモードを記録しているのは 8 件で **フル 6 / 軽量 2**（残り 3 件は記録なし）
- **軸ごとの実績**: フルモードでも実際にディスパッチされたのは **impl / correctness / security の 3 軸**が典型で、test / a11y / ui / perf は「対象なし」（`ディスパッチ:` 行が残る `20260731-design-contract-appendix` など）。ただしこのリポジトリの作業は SKILL.md・scripts・hooks が中心で、**フロントエンド製品のタスクとは分布が違う**（配置先での実績が要る）
- **限界**: 書式が統一されておらず（`モード:` の書き方・`ディスパッチ:` 行の有無がまちまち）、3 件はモード不明。次回以降 `review-result.md` の先頭に `モード:` と `ディスパッチ:` を必ず書く運用にすれば、同じ集計が機械的に取れる

### ユーザー側で実行が要る実測

- マスターで `/skill-doctor` を実行し、結果をこの節に貼る（組み込みコマンドでこのセッションからは実行できない。20260927 に元タスクのクローズ条件から外した — 元タスクはアーカイブするため、貼り先を元タスクの decisions.md からここへ変更）
- ~~配置先（`skill-test` / `hospital-search-mock`）でも同じ `/skill-doctor` を実行して結果を貼る~~ → 不要（20260929 時点で登録済みの配置先は 0 件。hospital-search-mock は 0927、skill-test は 0929 に登録解除）
