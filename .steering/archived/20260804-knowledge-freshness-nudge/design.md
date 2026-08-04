# 設計: knowledge-freshness-nudge

Created: 20260804
Status: **APPROVED**
Approved: 20260804

## 目的

knowledge / ルールの鮮度点検（`rule-audit`）の起動が人間の記憶に依存している状態を、SessionStart の月次ナッジで常用化し、個人段階の鮮度管理（ADR 20260715）を「起動しさえすれば腐食を検出できる」から「起動を忘れにくい」まで一段進める。

## スコープ

### 対象
- SessionStart（`session-start-check.sh`）に、最終 rule-audit から 30 日以上（または未実施）のとき **rule-audit 起動ナッジ**を注入する（**`.claude/skills/rule-audit/SKILL.md` が存在するときだけ**）
- ナッジの確認 UX を「今 / 後で / スキップ」とする。**三択 UI は capture を踏襲するが操作定義は別契約**（スキップ寿命は 30 日スヌーズ。capture の「次の Stop まで」ではない）
- 最終実施／スヌーズ時刻のマーカー（`.steering/.last-rule-audit`）の読み書き契約を hook・`rule-audit`・gitignore・deploy・文書で揃える
- ADR 20260715 の Consequences（ナッジ見送り）を Amendment で現行化し、スキップ／Step 5 のみ更新のトレードオフも Consequences に一文残す
- BACKLOG 節 4 の「ナレッジ鮮度の機械化」行を本タスクへ移して削除する

### 対象外
- 鮮度シグナル bash の `scripts/` 切り出し（決定インタビューで B/C を採らず A のみ）
- チーム段階（owner / 最終検証日 frontmatter + CI）への ADR 段階昇格
- rule-audit の cron / スケジュール自動実行（課金セッションの自動起動）
- rule-audit 本体の削除テスト・判定基準の変更
- ナッジをハードゲート化（作業ブロック・archive 停止はしない）
- **スキップと実監査の区別をマーカー上で持たない**（1 ファイル・同一 epoch。将来の観測・段階昇格で分ける必要が出たら別タスク）
- company / export 追随（Frozen）
- 配置1件実走・passthrough 拡充・design.md 境界の任意追記（BACKLOG 別項）

## 制約

- 親ブランチ: `integration/20260730-reports`。本変更は `feature/20260804-knowledge-freshness-nudge` から親への PR（base = 親）。**PR マージは人間の明示指示があるまでしない**
- 説明文だけ増やす修正は禁止（契約・手順・機械検査のどれかを動かす）
- 片側修正禁止: ナッジ文言・マーカー操作・完了時書き込みは、書く側（hook / rule-audit / deploy gitignore）と読む側（CLAUDE.md 任意再掲・starter-kit・user-guide・README）を同一コミットで揃える
- 操作定義の一次は **hook 注入文**（CLAUDE.md に正本を置かない。再掲は任意）。見出しは capture と分離（例: 【rule-audit 月次】）
- SessionStart hook は `python3` に依存しない。時刻は **GNU date または BSD date の `date +%s`** を使う（POSIX 厳密変換には無い共通拡張。失敗時は当該ナッジ節だけスキップし、capture/codify/タスク注入は継続＝フェイルオープン）
- 配布可資産（`session-start-check.sh`・`rule-audit`）に master-only 前提を残さない
- 検証の正本は `pnpm run …`
- company / export は Frozen
- 既存 capture 契約を壊さない（本ナッジは `.capture-needed` 確認より後、`.codify-needed` 確認より後）。validate キーも capture の「次の Stop」と混線させない

## 完了条件

- [x] **`.claude/skills/rule-audit/SKILL.md` が存在するときだけ**、かつマーカー欠落／非整数／空、または最終更新から **30 日（2592000 秒）以上**のとき SessionStart が rule-audit ナッジを注入する
- [x] マーカーが整数で `now - last < 2592000`（未来時刻含む）ならナッジを注入しない
- [x] `date +%s` 失敗時は本ナッジを出さず、既存 capture/codify/タスク/BACKLOG 注入は継続する
- [x] `.steering/` が無い、または rule-audit スキルが無いプロジェクトでは本ナッジなし（`.steering/` 無しは現行どおり素通し）
- [x] ナッジ確認は「今 / 後で / スキップ」。**操作定義は hook 注入文**。注入見出しで capture 三択と分離。スキップ行に「マーカー更新・30 日再ナッジ（capture の次 Stop 寿命とは別）」を含む
- [x] 「今」→ `rule-audit` を実行。**入口を問わず Step 5（レポート提示）に到達したら**マーカーを現在 epoch で更新。Step 5 未到達なら不変。適用 Step 6 の有無とは独立
- [x] Step 5 のマーカー更新は **`.steering/.last-rule-audit` への epoch 1 行書き込みのみ承認不要の例外**。削除・統合・明確化・移動その他の書き込みは従来どおり承認前禁止・提示後停止
- [x] 「後で」→ マーカー不変（次回 SessionStart で再確認可）
- [x] 「スキップ」→ マーカーを現在 epoch で更新（監査せず 30 日スヌーズ）。永久免除ではない
- [x] 注入順: capture 三択 → codify 確認 → **本ナッジ** → アクティブタスク / BACKLOG
- [x] ADR 20260715 に Amendment（個人段階に SessionStart ナッジを追加。Decision の段階表・核は不変。Consequences にスキップ／Step 5 のみ更新の Bad を一文）
- [x] マスター `.gitignore`・`deploy_skills.py` の `GITIGNORE_LINES`・user-guide のランタイムフラグ行数説明に `.steering/.last-rule-audit` を同一コミットで追加
- [x] 変更対象の全文検索洗い出しが tasklist 先頭手順どおり完了し、漏れが主要コンポーネント表に反映済み
- [x] hook フィクスチャ: (1) マーカー無し→注入 (2) 新しい→非注入 (3) `age>=2592000`→注入 (4) `age==2591999`→非注入 (5) `.steering/` 無し→素通し (6) rule-audit スキル無し→非注入 (7) 壊れたマーカー（非整数）→注入 (8) capture/codify があるとき本ナッジが後順 (9) `date` 失敗相当は他注入継続（再現手段は実装時に固定）
- [x] `pnpm run validate`（本タスクのキー共存検査を含む。capture の「次の Stop」キーと混線しない）が通る
- [x] BACKLOG 節 4 の「ナレッジ鮮度の機械化」行が削除済み

## アプローチ

最終実施／スヌーズ時刻を `.steering/.last-rule-audit`（Unix epoch 秒・1 行）に残し、SessionStart が rule-audit スキル存在かつ閾値超過時だけナッジする。確認 UI は三択だが、スキップ寿命は capture と別契約（30 日スヌーズ）で注入文に一次定義する。ハードゲートにはしない。rule-audit は Step 5 到達時にマーカーだけ例外書き込みし、「見た」ことを常用化の充足とする（剪定適用は別ゲートのまま）。

## 主要コンポーネント

| コンポーネント | 場所 | 変更後の記述・契約（原本なしで判定できる粒度） |
|---------------|------|------|
| SessionStart hook | `.claude/hooks/session-start-check.sh` | `rule-audit/SKILL.md` 存在時のみ。マーカー欠落／非整数／空または `now-last>=2592000` なら【rule-audit 月次】三択を注入。**操作定義はこの注入文**（スキップ＝マーカー更新・30 日。capture の次 Stop とは別）。`date +%s` 失敗時は本節スキップ。算術前に整数検証。capture/codify の後、アクティブタスクより前 |
| ランタイムマーカー | `.steering/.last-rule-audit` | 内容は Unix epoch 秒の 1 行。実監査とスキップを区別しない。git 追跡しない |
| gitignore | `.gitignore` | `.steering/.last-rule-audit` を既存フラグ節に追加 |
| deploy gitignore | `scripts/deploy_skills.py` | `GITIGNORE_LINES` に同パターンを追加（配置先同期） |
| rule-audit | `.claude/skills/rule-audit/SKILL.md` | Step 5 到達時にマーカー更新。**この 1 ファイルへの epoch 書き込みのみ承認不要例外**と明記。他書き込み・提示後停止は不変。スキップ三択の正本は SessionStart（スキル内に三択正本を新設しない） |
| セッション開始ルール | `CLAUDE.md` | ナッジ三択の**任意再掲**（正本は hook）。順序・スキップ寿命の別契約を再掲 |
| starter-kit | `docs/starter-kit.md` | SessionStart の rule-audit 月次ナッジ・スキル不在時非注入・マーカー契約を同期 |
| user-guide | `docs/user-guide.md` | 「月 1 目安」をナッジ付き現行形に。ランタイムフラグ行数（3→4）を同期 |
| README | `README.md` | SessionStart 説明に rule-audit ナッジを現行形で追記（図と食い違うなら同一コミットで図も） |
| ADR | `docs/decisions/20260715-docs-lifecycle-tiers.md` | Amendment: 個人段階に SessionStart ナッジ。Decision 核不変。Consequences にスキップ／Step 5 のみ更新の Bad |
| BACKLOG | `.steering/BACKLOG.md` | 節 4「ナレッジ鮮度の機械化」行を削除 |
| 機械検査 | `scripts/validate_skills.py` | ナッジ見出し・スキップ 30 日・Step 5 例外・gitignore/deploy 行の書く側・読む側共存。capture「次の Stop」と混線しないキー。空文限界はコメント明記 |

## 未解決の論点

（決定インタビュー＋プレモータム反映済み。承認時に残論点だけ確認）

- [x] 成果物の主軸 = SessionStart ナッジのみ（スクリプト切り出しなし）
- [x] 発火条件 = 最終 audit から 30 日以上 or 未実施
- [x] スキップ = マーカー更新で 30 日スヌーズ
- [x] マーカー更新タイミング = 入口問わず Step 5 到達時（未到達は不変）
- [x] ハードゲート化しない
- [x] Step 5 マーカー書き込み = 当該ファイルのみ承認不要例外（プレモータム反映）
- [x] rule-audit 未配置 = 非注入（プレモータム反映）
- [x] capture と同型主張をやめ別契約（プレモータム反映）
- [x] `date +%s` 許容と失敗時フェイルオープン（プレモータム反映）
- [x] マーカー異常系・閾値境界フィクスチャ（プレモータム反映）
- [x] deploy / user-guide の gitignore 同期を本タスク対象（プレモータム反映）
- [x] スキップと実監査の区別は持たない（対象外に明記・プレモータム反映）
- [x] ADR Amendment の Consequences Bad は推奨一文で固定（承認時確認）

---

<!-- design-doc-boundary: appendix -->

## プレモータム所見（design-premortem）

実施: 20260804。会話経緯バイアスなし。リポジトリ裏取り済み（`session-start-check.sh` 注入順・`json_escape` / `.gitignore` フラグ節 / `rule-audit` Step 5–6 / ADR 20260715 Decision・Consequences / `validate_skills.py` CAPTURE_GRANULARITY_CHECKS / `deploy_skills.py` GITIGNORE_LINES / starter-kit 推奨構成・session-start 同送条件 / capture 三択一次定義）。

- 攻撃: [1][4] Step 5 でのマーカー書き込みが、現行 `rule-audit` の承認前書き込み禁止・提示後停止と衝突
  影響: マーカー未更新の永久ナッジ、または Step 5 で書き込み解禁と誤読して剪定まで走る
  提案: Step 5 に「`.last-rule-audit` 1 行だけ例外」を契約化
  **プレモータム反映済み**: 完了条件・アプローチ・主要コンポーネント（rule-audit）に例外範囲を明記

- 攻撃: [4][5] SessionStart は最小セットでも配る一方、`rule-audit` はメタ層任意 — 未配置スキルへの起動催促
  影響: 配置先で実行不能指示が月次化し、SessionStart 全体の信頼が落ちる
  提案: スキル不在なら非注入
  **プレモータム反映済み**: 対象・完了条件・hook 行に「SKILL.md 存在時のみ」を追加

- 攻撃: [1][2] 「同型」主張だがスキップ寿命が capture（次 Stop）と非同型（30 日スヌーズ）
  影響: 操作定義の取り違え。validate「次の Stop」キーとも混線しうる
  提案: 同型をやめ、見出し分離・別 validate 目印
  **プレモータム反映済み**: スコープ・制約・完了条件・hook 行を「三択 UI 踏襲・操作定義は別契約」に変更

- 攻撃: [1][3] `date +%s` は POSIX date に無く、旧制約「POSIX のみ」と矛盾
  影響: 環境によっては hook 失敗で capture 注入ごと消える
  提案: `%s` 許容を明記し、失敗時フェイルオープン
  **プレモータム反映済み**: 制約・完了条件・hook 行・フィクスチャ (9) を更新

- 攻撃: [1][3] マーカー異常系・閾値境界が未定義・未フィクスチャ
  影響: shell 算術エラーで既存 SessionStart まで巻き込む／実装分裂
  提案: 非整数＝欠落、未来＝新しい、境界＋壊レマーカーを完了条件化
  **プレモータム反映済み**: 完了条件の判定規則とフィクスチャ (3)(4)(7) を追加

- 攻撃: [4][2] `deploy_skills.py` GITIGNORE_LINES / user-guide「3 行」が表にも対象外にも無い
  影響: 配置先でマーカーがコミット追跡される片側ドリフト
  提案: コンポーネント表に入れる
  **プレモータム反映済み**: deploy / user-guide を主要コンポーネントと完了条件に追加

- 攻撃: [5][6] スキップ＝未監査 30 日沈黙と Step 5「見た」充足が、ADR 目的に新しい Bad を足すのに Amendment 案が薄い
  影響: マーカー上は健全・実体は未監査、が常用化する
  提案: Amendment Consequences にトレードオフを書く
  **プレモータム反映済み（推奨固定）**: 対象・完了条件・ADR 行に Consequences Bad 一文を必須化。文量は未解決に残し承認時確認

- 攻撃: [3][6] Step 5 未到達／手動起動と SessionStart 経路の更新同一性のテストが弱い
  影響: 中断成功扱い or 手動 audit 後も毎月催促
  提案: 「Step 5 到達⇔更新」を入口横断で完了条件化
  **プレモータム反映済み**: 完了条件に入口問わず Step 5 到達／未到達を明記

- 攻撃: [2][5] 1 ファイルが実監査時刻とスキップスヌーズを兼ねる
  影響: スキップ率が見えず、チーム段階接続時にフォーマット破壊
  提案: 今は持たないと対象外に明記
  **プレモータム反映済み**: 対象外に「区別は持たない」を追加

（このスキルは設計を承認しない。design-doc の Phase 3 STOP に戻る）


---

> **付録** — 実装入口・resume の既定では読まない。プレモータム・TDD 突入・乖離調査など、当該節が必要なときだけ読む。人間の Phase 3 承認前は `影響範囲` と `検討した代替案` を必読。

## データフロー

```
SessionStart
  → .steering/ 無ければ exit 0
  → capture / codify 注入（既存）
  → rule-audit/SKILL.md 無ければ本節スキップ
  → date +%s 失敗なら本節スキップ（他注入継続）
  → read .last-rule-audit
       欠落/非整数/空 or age>=2592000 → 【rule-audit 月次】三択注入
       整数かつ age<2592000（未来含む） → 無注入
  → アクティブタスク / BACKLOG（既存）

ユーザー「今」→ rule-audit（入口問わず）→ Step5 到達 → マーカーのみ例外更新 → 他書き込みは停止
ユーザー「後で」→ 何もしない
ユーザー「スキップ」→ マーカー更新（30 日スヌーズ。実監査との区別なし）
```

## 影響範囲

- システム / 外部連携: なし（ローカル hook・スキルのみ）
- データ: `.steering/.last-rule-audit`（新規ランタイム・gitignore / deploy 同期）
- 他チーム / 利用者: SessionStart 配置先のうち rule-audit もある環境で月次ナッジが増える。未配置スキルへの催促はしない。ハードブロックはしない
- リグレッション懸念: SessionStart 注入文の肥大・capture/codify 順序破壊・`date +%s` 失敗時の他注入巻き込み（フェイルオープンで緩和）。ADR Decision 核の誤書き換え。deploy gitignore 未同期による配置先追跡漏れ

## テスト方針

- Unit: なし（TS 成果物なし）
- Hook フィクスチャ: 完了条件の 9 ケース（境界・壊レマーカー・スキル不在・順序含む）
- 機械: `pnpm run validate`（キー共存・capture キーと分離）/ 必要なら `pnpm run validate:assets`
- E2E / passthrough: 必須にしない。rule-audit 手順キー（マーカーパス + 例外文言）は validate 共存で担保

## 検討した代替案

| 代替案 | 却下理由 |
|--------|----------|
| 鮮度シグナルのスクリプト化のみ | 起動忘れを解けない（常用化に非直結） |
| ナッジ + スクリプト | 1 PR が厚くなる。第一歩は常用化 |
| チーム段階（owner + CI） | ADR の個人段階・摩擦実証前の予防的ハードニング |
| knowledge 更新検知を主条件 | 変更なしで腐るケースを拾えない |
| compound N 回ごと | compound 改修が乗り主軸からずれる |
| 毎回 SessionStart で 1 行 | 毎セッション固定費・摩擦大 |
| スキップでマーカーを触らない | 「スキップしたのに毎セッション出る」誤解を生む。スヌーズで閉じる |
| rule-audit 未配置でもナッジ | 実行不能指示。スキル存在ゲートで防ぐ |
| deploy gitignore を後回し | 配置先でマーカーが追跡される。本タスクで同期 |

## 調査結果

- ADR 20260715 Consequences が「起動ナッジの hook 化は無料で可能だが見送り」と明記 — 本タスクはその予告の実装
- 現行 `session-start-check.sh` は `.steering/` 前提・POSIX ユーティリティ中心・capture → codify → タスク → BACKLOG の順（`date` 未使用）
- knowledge は 5 本（個人段階の「≤10 本程度」内）
- `.gitignore` のランタイムフラグは task 配下 3 種のみ。`deploy_skills.py` `GITIGNORE_LINES` と同内容。直下マーカーは未登録
- starter-kit: SessionStart は `.steering/` 利用時に同送。rule-audit はメタ層任意

### 既存パターン調査（20260804）

- SessionStart 注入順: capture → codify →（本変更で月次ナッジ）→ タスク → BACKLOG。`json_escape` は BSD sed 対応済み
- validate キー共存: capture-granularity / design-impl-sync と同型で `KNOWLEDGE_FRESHNESS_CHECKS` を追加
- deploy `GITIGNORE_LINES` が配置先 gitignore の単一情報源（マスター `.gitignore` と対で更新）
- 注意点: fixture (9) は `PATH` 先頭の失敗 `date` で再現。フィクスチャ結果は `verification.md`
