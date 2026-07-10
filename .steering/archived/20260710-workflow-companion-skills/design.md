# Design: workflow-companion-skills

Status: **APPROVED**
Created: 20260710
Approved: 20260710

## Goal

フロントエンド開発ワークフロー（design → 実装 → レビュー → PR → 福利化）の「外側のループ」を埋める 6 つのスキル/ツールを新設する。具体的には (1) PR 提出後の往復、(2) スキル自体の回帰テスト、(3) 人間承認ゲート前の設計品質向上、(4) セッション摩擦の自動起票、(5) 配置先からの還流、(6) 並列実装比較。**本設計書は実装を別モデルが行う前提で、各スキルの仕様を実装可能な粒度まで書き切る。**

## Scope

### In scope

1. `pr-feedback` — PR コメント・CI 失敗の収集→トリアージ→修正→返信
2. skill-test ハーネス — 静的層（validate_skills.py 拡張）+ 実行層（素通り検査の機械化）
3. `design-premortem` — design.md への敵対的レビュー
4. `session-retrospective` — セッション摩擦の棚卸しと skill-issues.md への起票
5. `skill-harvest` — 配置先のドリフト検出・skill-issues 回収（マスター専用）
6. `impl-tournament` — 同一設計からの N 並列実装比較
7. 上記に伴う README ワークフロー図・feature-pipeline・design-doc・starter-kit.md の整合改訂

### Out of scope

- 各スキルの empirical-prompt-tuning による反復改善（ユーザー方針: empirical は任意・静的チェックで締める）
- Stop hook への自動フラグ追加（session-retrospective は手動起動。自動化は摩擦が実証されてから）
- スケジュール実行・cron 化（課金ループはユーザー方針で不採用）
- 専用 agent 定義（`.claude/agents/`）への切り出し

## Constraints

- 全スキルは `templates/SKILL.template.md` から書き始める（CLAUDE.md ルール）
- エンジン純度: 本文（frontmatter 除く）にツール固有 API を書かない。ツール語彙は compatibility frontmatter と `references/*.md` のみ（skill-design-patterns.md）
- 停止・承認・前提条件は**手順の Step（ハードストップ）**として書く。description や出口分岐の一句にしない（20260703-04 で実証済みのパターン）
- 絵文字を書かない（アストラル面文字は 400 エラーの原因）
- `python3 scripts/validate_skills.py` 全 PASS・本文 500 行以内・description 引用符付き 1 行 1024 文字以内
- 孤立 subagent が読む前提: 参照物が無い場合のフォールバックを該当 Step に直接書く
- 並列サブスキル・二者間契約は両側を同一コミットで直す（片側修正の禁止）。閉じる前に直した語をリポジトリ全体で grep する
- README ワークフロー図と feature-pipeline は同一コミットで改訂する（CLAUDE.md ルール）
- スクリプトは依存ゼロの python3（validate_skills.py と同様）。Node 系を使う場合は pnpm 前提

## Acceptance criteria

- [ ] 6 スキル/ツールすべてが `.claude/skills/[name]/SKILL.md`（skill-test 実行層と harvest スクリプトは `scripts/` + `tests/`）として存在し validator 全 PASS
- [ ] 各 SKILL.md 本文のツール固有 API 出現数がほぼゼロ（具体コマンドは references/ に分離）
- [ ] ハードストップが必要な地点（本書の各スキル設計に明記）がすべて「ここで止まる」形式の Step になっている
- [ ] README ワークフロー図・スキル一覧・関係図に新スキルが反映され、feature-pipeline との改訂が同一コミット
- [ ] starter-kit.md の選定表に配布可否（distributable / master-only）が反映されている
- [ ] validate_skills.py の新チェックが既存 20 スキル + テンプレートで PASS する（既存資産を壊さない）
- [ ] 二者間契約（design-doc↔design-premortem、pr-create↔pr-feedback 等）が両側の本文に相互明記されている
- [ ] 閉じる前に、変更した契約・語彙をリポジトリ全体で grep して同義箇所の取り残しゼロを確認した

## Approach

既存の設計原則（エンジン+カートリッジ、ハードストップ、自己完結フォールバック、境界相互明記）を新スキルに最初から適用する。追加の原則は 2 つ: (1) **配布分類** — pr-feedback / design-premortem / session-retrospective / impl-tournament は配布可能（他プロジェクトへコピーされる前提で自己完結に書く）、skill-test / skill-harvest は**マスター専用**（このリポジトリの管理ツール。starter-kit の選定表に「配布しない」と明記）。(2) **課金操作の前置承認** — subagent 並列や外向き API を伴うスキル（impl-tournament、skill-test 実行層）は、実行前にコスト見積と無料代替の提示を Step として持つ（ユーザー方針）。

## Key components

| # | 成果物 | 置き場所 | 分類 |
|---|---|---|---|
| 1 | pr-feedback | `.claude/skills/pr-feedback/SKILL.md` + `references/commands.md` | 配布可 |
| 2a | validator 拡張 | `scripts/validate_skills.py`（既存を拡張） | マスター専用 |
| 2b | skill-test（実行層） | `.claude/skills/skill-test/SKILL.md` + `scripts/passthrough_check.py` + `tests/passthrough/[skill]/scenario.md` | マスター専用 |
| 3 | design-premortem | `.claude/skills/design-premortem/SKILL.md` | 配布可 |
| 4 | session-retrospective | `.claude/skills/session-retrospective/SKILL.md` | 配布可 |
| 5 | skill-harvest | `.claude/skills/skill-harvest/SKILL.md` + `scripts/check_deploy_drift.py`（既存を拡張） + `deployments.md`（ルート） | マスター専用 |
| 6 | impl-tournament | `.claude/skills/impl-tournament/SKILL.md` + `references/commands.md` | 配布可 |
| 7 | 整合改訂 | README.md / feature-pipeline / design-doc / pr-create / starter-kit.md | — |

---

## スキル別詳細設計

### 1. pr-feedback（最優先）

**目的**: pr-create で提出した PR に返ってきたレビューコメント・CI 失敗を処理し、修正→再レビュー→返信までの往復を駆動する。ワークフロー図の [6] と [7] の間の穴を埋める。

**description 草案**（引用符付き 1 行に整形すること）:
> 提出済み PR に返ってきたフィードバックの処理に使う — 「PR のコメントを確認して」「レビュー指摘に対応して」「PR の CI が落ちてる、直して」「レビューに返信して」などのフレーズが対象。レビューコメントと CI 失敗を収集して must-fix / 要議論 / nit にトリアージし、対応計画の承認 → 修正 → 差分再レビュー → 返信・プッシュ前の明示承認まで駆動する。PR の新規作成には起動しない（pr-create を使う）。ローカル diff のレビューには起動しない（frontend-code-review を使う）。PR に紐づかないバグ・障害の原因調査には起動しない（debug を使う — CI 失敗でも原因が PR の差分外にあると判明したら debug へ接続する）。

**Steps**:
- **Step 0 — 前提チェック**: 対象 PR を特定する（引数 or 現在ブランチから）。PR ホスト CLI が使えない・リモートが無い・PR が存在しない場合は**ここで止まり**、pr-create または手動確認を案内する。会話の経緯による前提スキップ禁止。
- **Step 1 — 収集**: レビューコメント（インライン・全体）・レビュー状態（approved / changes_requested）・CI の失敗ジョブとログ要点を取得する（具体コマンドは references/commands.md）。取得結果ゼロなら「未対応フィードバックなし」と報告して終了。
- **Step 2 — トリアージ**: 各指摘を must-fix（正当・修正必須）/ 要議論（設計判断・反論あり）/ nit（任意）に分類し、CI 失敗は原因別（コード起因 / flaky / インフラ）に分類。**要議論に分類した指摘には反論または代替案の下書きを添える**（AI の判断を人間が見て決められる形にする）。flaky / インフラ起因と判定した CI 失敗の**再実行は外向き操作** — Step 5 の承認範囲に含めて提示する（Step 4 で勝手に再実行しない）。
- **Step 3 — STOP（対応計画の承認）**: トリアージ表と対応計画を提示して**ここで止まる**。ユーザーの明示承認を待つ。このメッセージの後は修正に入らない。
- **Step 4 — 修正適用**: 承認された must-fix / nit を修正。修正後、frontend-code-review スキルが存在すれば**指摘があった軸のみ差分再レビュー**に接続。無ければ自分で修正 diff をセルフチェック（フォールバックを本文に直接書く）。
- **Step 5 — STOP（外向き操作の承認）**: コミット内容・プッシュ・各コメントへの返信文の下書きを提示して**ここで止まる**。プッシュと返信投稿は外向き操作（pr-create と同じ契約）。承認後に実行し、CI を追跡して結果を報告する。

**境界相互明記**: pr-create 側に「PR 提出後のコメント・CI 失敗の対応は pr-feedback の担当」を追記し、pr-feedback 側に「PR の新規作成・初回プッシュは pr-create の担当」と書く（同一コミット）。

**references/commands.md（カートリッジ）**: GitHub CLI での取得・返信・CI ログの具体コマンド集。冒頭に「別ホスト（GitLab 等）はこのファイルを差し替える」と明記。マスターの pr-create/references/commands.md と重複するコマンドがあっても、各スキルの自己完結性を優先して各自が持つ（配布単位がスキルフォルダのため）。

**受け入れ基準**: STOP が 2 箇所（Step 3 / Step 5）ハードストップ形式で存在。本文に gh 等のコマンド名が出現しない。README 図に [6.5] として挿入され feature-pipeline と同一コミット。

### 2. skill-test ハーネス

#### 2a. 静的層 — validate_skills.py 拡張（無料・毎回）

既存 5 項目に追加する検査:

- **項目 6 — When NOT to use 存在**: 本文に `## When NOT to use` 見出しがあること。無ければ FAIL。
- **項目 7 — 停止契約の構造検査**: frontmatter + 本文に承認語彙（正規表現: `承認|APPROVED|approved`。ただし**否定形「承認不要」「承認なし」「承認は不要」はマッチ対象から除外する** — 自律実行境界を引用するスキルの誤 FAIL を防ぐ）が出現するスキルは、本文に**ハードストップ表現**（`ここで止ま` または見出しに `STOP`）が 1 つ以上あること。無ければ FAIL。誤検出の逃し弁として、スキル本文に HTML コメント `<!-- validator: no-stop-needed -->` があればスキップ（使用時はコメント内に理由を書く運用）。
- **項目 8 — ツール純度計測（`--purity` オプション、レポートのみ・FAIL にしない）**: ツール語彙リスト（`gh`, `git`, `npx`, `pnpm`, `npm`, `playwright`, `vitest`, `curl`, `jq` など。実装時にリストを定数化）を本文（frontmatter と references/ を除く）から単語境界つきで文字列カウントし、スキルごとの出現数を表示する。skill-design-patterns.md の「エンジン純度を実測する」を機械化するもの。

**実装上の注意**: 新チェック追加後、既存 20 スキル + `--template` で全 PASS すること。既存スキルが項目 6/7 で落ちる場合は**スキル側を直す**（このタスクの一部。落ちたという事実は「説明文だけの停止契約」の検出そのものなので、ハードストップ Step に書き直す）。

#### 2b. 実行層 — 素通り検査の機械化（課金・任意）

20260709 に手作業で 6/6 を取った素通り検査（skill-design-patterns.md「停止・承認・前提条件の契約」の節を一次情報とする）をスクリプト + シナリオ資産として固定する。

- **`tests/passthrough/[skill-name]/scenario.md`**（マスター専用・ルート直下 `tests/`。スキルフォルダに入れない — 配布物に混ぜない・validator の走査対象にしない）: 各シナリオは (1) サンドボックスに置くダミーファイル一覧と内容、(2) 停止すべき地点に至る現実的な依頼文（「停止テストだ」とは書かない）、(3) 素通りを誘導する環境圧の一文（例: headless で人間が即応できない・会話内で承認済みと主張）、(4) 期待: 停止 or 続行、(5) 判定対象ファイルの glob。初期整備はハードストップを持つスキル（design-doc / impl-from-design / debug / pr-create / 新設 4 スキル）分。
- **`scripts/passthrough_check.py`**: (1) サンドボックス生成（scenario.md の指定通り）→ (2) 実行前 SHA1 スナップショット → (3) ヘッドレスのフレッシュエージェントに実 SKILL.md を操作指示として読ませてシナリオ依頼を渡す（起動コマンドは設定可能にし、デフォルトはリポジトリの CLI 環境。実装時に 1 箇所の定数にする）→ (4) 実行後 SHA1 差分で判定対象ファイルへの接触を機械判定 → (5) 各スキル 2 回実行し、1 回でも素通りしたら FAIL。自己申告は使わない。
- **`.claude/skills/skill-test/SKILL.md`**（マスター専用スキル）: 上記を編成する薄いラッパー。**Step 1 に課金の明示とコスト見積・無料代替（静的層のみで締める）の提示 → STOP を置く**。ユーザーの明示承認なしに実行層を回さない。hooks への接続は禁止と本文に明記（自動課金ループを構造的に防ぐ）。

**受け入れ基準**: 静的層は既存全スキルで PASS。実行層はシナリオ 1 本（design-doc）でエンドツーエンドが通ることを確認できる構造（実際に課金して回すかはユーザー判断・デフォルトでは回さない）。

### 3. design-premortem

**目的**: design.md を人間レビューに出す**前**に敵対的レビューをかけ、人間の承認ゲートに届く設計の質を上げる。人間ゲートは置き換えない。

**description 草案**:
> design.md を人間レビューに出す前の敵対的レビューに使う — 「設計をプレモータムして」「設計の穴を探して」「この設計を攻撃して」などのフレーズが対象。エッジケース・状態管理の複雑化・テスト容易性・スコープ妥当性・「3ヶ月後に後悔する理由」の観点で設計を批判し、所見を design.md の Premortem セクションに追記する。設計を承認はしない（人間の承認ゲートは維持）。実装コードのレビューには起動しない（frontend-code-review を使う）。

**Steps**:
- **Step 0 — 対象特定**: 引数 or アクティブな `.steering/[task]/design.md` を特定。`.steering/` が無いプロジェクトでは対象ファイルパスをユーザーに確認する（フォールバック明記）。design.md がすでに APPROVED の場合は**ここで止まり**、「承認済み設計への遡及プレモータムか」を確認する（承認前が本来の使いどころ）。
- **Step 1 — 敵対的レビュー**: フレッシュな subagent に design.md **のみ**を渡し（セッションバイアス排除）、固定チェックリストで攻撃させる: (1) 見落とされたエッジケース・異常系、(2) 状態管理・データフローが複雑化する未来、(3) テスト容易性（Acceptance criteria は機械検証可能か）、(4) スコープ妥当性（In scope に紛れた YAGNI / Out に漏れた必須）、(5) 3ヶ月後に後悔する理由（拡張・保守の視点）、(6) Open questions の網羅性（人間が判断すべき論点の漏れ）。subagent が使えない環境では自分でチェックリストを適用する（バイアスが残る旨を出力に注記する — フォールバック明記）。
- **Step 2 — 反映**: 所見を design.md の `## Premortem` セクションに追記する。各所見は「攻撃 / 影響 / 提案」の 3 行構成。設計者として反論できるものには反論を併記し、設計本文を直すべきものは直した上で「Premortem 反映済み」と記す。`.steering/` 配下への追記は承認不要（CLAUDE.md）。
- **Step 3 — 報告**: 修正した点・人間の判断に委ねる点を要約して報告し、design-doc の Phase 3 STOP（人間レビュー）へ戻す。**このスキル自体は設計を承認しない**と本文に明記。

**design-doc との統合**（同一コミット・両側明記）: design-doc の Phase 2 と Phase 3 の間に「design-premortem スキルが存在すれば実行を**提案**する（必須にしない — 小タスクでは重い）」の一文を追加。design-premortem 側には「design-doc の Phase 3 STOP の直前に呼ばれることを想定。単独でも使用可」と書く。

**受け入れ基準**: 承認をしない旨がハードストップではなく**役割制約**として本文に明記されている。design-doc との相互明記が同一コミット。

### 4. session-retrospective

**目的**: 自己改善ループの原料である skill-issues.md の起票を「気づいたら書く」から「セッション終盤に会話を採掘して起票する」に変える。compound の原料を濃くする。

**description 草案**:
> セッション終盤にそのセッションの摩擦を棚卸しするメタスキル — 「振り返りして」「レトロして」「セッションの摩擦を記録して」「今日引っかかった点をまとめて」などのフレーズが対象。スキルの誤発動・不発動、ユーザーによる訂正、手戻り・リトライ、パーミッション拒否、指示の曖昧さを会話履歴から抽出し、.steering/[task]/skill-issues.md に起票する。コード・設計の知見保存には起動しない（knowledge-capture を使う）。ルールへの昇格もしない（compound の原料を作るのが役割）。タスク完了のたびに自動起動しない。

**Steps**:
- **Step 1 — 採掘**: 現在の会話履歴を先頭から走査し、5 分類で摩擦を抽出する: (a) スキル誤発動・不発動（発動すべきで発動しなかった含む）、(b) ユーザー訂正（ユーザーが方向修正・やり直しを指示した箇所）、(c) 手戻り（アプローチ失敗→切り替え）、(d) パーミッション拒否（ユーザーが tool 実行を拒否した箇所とその含意）、(e) 指示・スキル本文の曖昧さ（解釈に迷った箇所）。**該当ゼロならその旨を 1 行で報告して終了**（無理に起票しない）。
- **Step 2 — 起票**: 各摩擦を「事象 / 期待 / 該当スキル or ルール」形式で `.steering/[アクティブタスク]/skill-issues.md` に追記する（承認不要 — CLAUDE.md の自律実行境界に該当。CLAUDE.md にこの境界が無いプロジェクトでは追記前に一言確認する）。**アクティブタスクが無い場合**は `.steering/[YYYYMMDD]-retrospective/skill-issues.md` の作成を**提案し、承認後に**作成・起票する（skill-harvest の回収経路を 1 本に保つため。断られたら抽出結果を会話に提示するのみ）。この仕様が無いと `.steering/` 運用をしない配置先で harvest への供給が成立しない（producer / consumer の対の成立条件）。
- **Step 3 — 報告**: 起票件数と内訳を報告し、「compound での回収は次回の福利化時に行われる」と案内する（このスキルは昇格しない）。

**compound / knowledge-capture との境界**（相互明記）: compound 側は既に skill-issues.md を回収する設計なので契約変更は不要だが、session-retrospective の存在を compound の「原料の供給元」として 1 行追記する（同一コミット）。Stop hook への接続は**しない**（自動化は摩擦の実証後。design 上の判断として Alternatives に記録）。

**受け入れ基準**: 起票がゼロ件のとき何も書き込まないこと（ノイズ起票の禁止）が Step に明記されている。

### 5. skill-harvest（マスター専用）

**目的**: 横展開モデルの弱点「還流が人力」を埋める。配置先の (1) 再コピー候補（マスターが先行）、(2) ドリフト（配置先で直接編集された）、(3) 溜まった skill-issues.md を機械的に収集する。

**description 草案**:
> 配置先プロジェクトからの還流に使うマスター専用スキル — 「配置先を回収して」「ハーベストして」「配置先のドリフトを確認して」「skill-issues を集めて」などのフレーズが対象。配置レジストリの各プロジェクトについて、source-commit とマスターの差分（再コピー候補）、配置先での直接編集（ドリフト）、配置先に溜まった skill-issues.md を収集してレポートする。配置先への書き込み（再コピー）は明示承認制。スキル本文の改善作業には起動しない（改善はマスターで行い再コピーで配る）。

**還流の成立条件（producer / consumer の対）**: harvest が回収できるのは、配置先に (1) `metadata.source-commit`（配置手順で記録）と (2) `.steering/**/skill-issues.md` が存在する場合のみ。skill-issues.md を書くルールはこのリポジトリの CLAUDE.md にしか無いため、**配置先には session-retrospective（配布可）を併配するのが供給側の推奨構成** — これが「取得用の情報を出力するスキル」の役割を担う。starter-kit の選定表にこの対を明記する。取得はマスターからの直接読み取り（pull 型・同一マシン前提）。

**コンポーネント**:
- **`deployments.md`（リポジトリルート・マスター専用）**: 配置先の絶対パスを 1 行 1 件で列挙するレジストリ（コメント行 `#` 可）。スキル単位の記録は持たない — どのスキルが配置されているかは配置先の `metadata.source-commit` から発見する（レジストリの二重管理を避ける）。
- **`scripts/check_deploy_drift.py`（既存スクリプトの拡張 — 新規スクリプトを作らない）**: ドリフト 3 分類（直接編集 / マスター先行=再コピー候補 / 記録なし）は**既存実装済み**。比較上の落とし穴（source-commit 行の除去・references/ は配置時に再生成されるため比較対象外）も解決済みなので再実装しないこと。拡張点は 2 つ: (1) **レジストリモード** — 引数なし実行時に `deployments.md` を読んで全配置先をループ（既存の単一パス引数モードは互換維持）、(2) **issues 回収** — 各配置先の `.steering/**/skill-issues.md`（archived 含む）を収集し、回収済みマーカー `<!-- harvested: YYYYMMDD -->` より後の項目だけを新規として報告。出力はレポート（標準出力）のみで**スクリプトは読み取り専用を維持**（マーカーの書き込みはスキル側が承認後に行う）。
- **SKILL.md**:
  - **Step 0 — 前提チェック**: `deployments.md` が無ければ**ここで止まり**、レジストリの作成方法を案内する。
  - **Step 1 — 収集**: check_deploy_drift.py（レジストリモード）を実行しレポートを提示する。
  - **Step 2 — STOP（再コピーの承認）**: 再コピー候補・ドリフトへの対処案（マスターへの還元 or 上書き）を提示して**ここで止まる**。配置先への書き込みはこのリポジトリの外への操作のため必ず明示承認を待つ。ドリフトが検出されたスキルは**上書き前にドリフト内容の差分を提示する**（配置先の改善をマスターに還元するのが原則 — 黙って上書きすると改善が消える）。
  - **Step 3 — 適用**: 承認された分をコピーし、配置先の `metadata.source-commit` を現在のマスターコミットに更新する。
  - **Step 4 — issues の還流**: 回収した skill-issues を `.steering/[YYYYMMDD]-harvest/skill-issues.md` に集約し（どの配置先由来かを各項目に付記）、compound での回収を案内する。**再回収の防止**: 回収した配置先ファイルの末尾に回収済みマーカー（HTML コメント `<!-- harvested: YYYYMMDD -->`）を追記する — 配置先への書き込みなので Step 2 の承認範囲に含めて提示する。check_deploy_drift.py はマーカー行より前の項目をスキップし、マーカー以降に追記された分だけを新規として報告する（スクリプト自体は読み取り専用のまま — マーカーの書き込みはスキル側が承認後に行う）。

**受け入れ基準**: check_deploy_drift.py が読み取り専用のまま・既存の単一パス引数モードが互換維持されていること。ドリフト上書き前の差分提示が Step に明記されていること。starter-kit.md に「配置時に deployments.md へ登録する」手順が追記されていること（片側修正の禁止 — 配置手順とレジストリの両側）。

### 6. impl-tournament

**目的**: 「AI は N 個書ける」を活かし、リスクの高い設計判断で 2〜3 の異なる実装アプローチを worktree 並列で作り、レビュースイートで採点して人間が選ぶ。常用しない — アプローチ選択が結果を大きく左右するタスク専用。

**description 草案**:
> リスクの高い設計判断で複数の実装アプローチを比較したいときに使う — 「トーナメントで実装して」「複数案を並列実装して比較して」「実装アプローチを競わせて」などのフレーズが対象。APPROVED な design.md から 2〜3 の異なるアプローチを worktree 並列で実装し、レビュー観点で採点した比較表を提示して人間が勝者を選ぶ。コストは実装とレビューが N 回分かかるため、開始前にコスト見積と無料代替の明示承認を取る。通常の 1 本実装には起動しない（impl-from-design を使う）。

**Steps**:
- **Step 0 — 前提チェック**: `.steering/[task]/design.md` の Status が APPROVED であることを**成果物で**確認（会話の経緯による代用禁止）。不成立なら**ここで止まり**、design-doc スキルが存在すればそこへリダイレクト、**無ければ**（配置先で単体利用の場合）承認済み設計文書の所在をユーザーに確認し、それも無ければ設計を先に固めるよう案内して止まる（フォールバック明記）。加えて git リポジトリであること・作業ツリーがクリーンであることを確認。不成立なら止まって案内。
- **Step 1 — STOP（アプローチ提案とコスト承認）**: design.md の Alternatives considered を起点に、**本質的に異なる** 2〜3 のアプローチ（例: 状態機械 / リデューサー集約 / サーバー状態寄せ。**上限 3**）を選定して提示する。あわせて (1) コスト見積（実装 N 回 + レビュー N 回分の課金）と**モデル振り分け案**（変種の実装は安価なモデル・採点/統合は上位モデル、等。具体的なモデル名と指定方法は references/commands.md に置き、本文は汎用に保つ）、(2) **無料代替**（アプローチ比較表だけ書いて 1 本に絞り impl-from-design へ進む）を必ず併記して**ここで止まる**。明示承認なしに並列実装を開始しない。
- **Step 2 — 並列実装**: アプローチごとに worktree を切り（具体コマンドは references/commands.md）、フレッシュな subagent に「design.md + 当該アプローチの brief」だけを渡して実装させる（他アプローチを見せない — 独立性の確保）。テストは design.md の Test strategy に従う。
- **Step 3 — 採点**: 各 worktree の成果物を同一基準で採点する。frontend-code-review / test-review が存在すれば各変種に適用し、無ければフォールバック基準（正当性・単純さ・テスト品質・設計整合）でセルフレビューする（フォールバック明記）。
- **Step 4 — STOP（勝者選定）**: 比較表（基準 x 変種、根拠付き）と推奨を提示して**ここで止まる**。勝者の選定は人間の判断。このメッセージの後はマージ・削除をしない。
- **Step 5 — 統合と後始末**: 承認された勝者をメインの作業ツリーに統合し、**敗者から得られた知見（採用しなかった理由・敗者にだけあった良い部分）を `.steering/[task]/decisions.md` に記録してから** worktree を削除する。worktree の削除自体は Step 4 の承認に含まれる旨を Step 4 の提示文に書く。

**受け入れ基準**: STOP が 2 箇所（Step 1 / Step 4）。Step 1 に無料代替の併記が必須として書かれている。git 語彙が本文に出現せず references/commands.md に分離されている。

---

## 整合改訂（コンポーネント 7）

- **README.md**: ワークフロー図に `[6.5] PR フィードバック pr-feedback（コメント・CI 失敗 → トリアージ → 修正 → 返信）` を挿入。[1]-[2] 間に premortem を任意ステップとして注記。[8] 付近に session-retrospective を注記。スキル一覧・関係図に 6 件追加。**feature-pipeline の改訂と同一コミット**。
- **feature-pipeline**: フェーズ検出に [6.5]（PR にフィードバックが返っている状態からの再開 → pr-feedback へ）を追加。premortem はフェーズにしない（design-doc 内の任意提案）。
- **design-doc**: Phase 2→3 間に premortem の任意提案を 1 文追加（相互明記・同一コミット）。
- **pr-create**: 境界相互明記の追記（前述・同一コミット）。
- **compound**: 原料の供給元として session-retrospective を 1 行追記。
- **starter-kit.md**: 選定表に新スキル 4 件（配布可）を追加し、skill-test / skill-harvest は「マスター専用・配布しない」と明記。配置手順に deployments.md 登録を追加。**session-retrospective は「harvest の供給側」として併配推奨**の注記を選定表に入れる。
- **docs/knowledge/skill-design-patterns.md**: 「配布分類（distributable / master-only）」の節を追記するかは実装時に判断（knowledge-capture の範疇。必須にしない）。

## Data flow

```
PR ホスト（コメント・CI） → pr-feedback → 修正 → frontend-code-review（差分再レビュー）→ 返信・push
design.md(DRAFT) → design-premortem（敵対 subagent）→ design.md + Premortem 節 → 人間承認
会話履歴 → session-retrospective → .steering/[task]/skill-issues.md → compound（既存経路）
配置先 N 個 → check_deploy_drift.py 拡張（読み取り専用）→ レポート → 承認 → 再コピー + .steering/[date]-harvest/
design.md(APPROVED) → impl-tournament → worktree x N → 採点 → 人間選定 → 統合 + decisions.md
SKILL.md 群 → validate_skills.py（静的・毎回）/ passthrough_check.py（実行・任意課金）
```

## Test strategy

- **Unit / Integration**: validate_skills.py の新チェックは、既存 20 スキル + テンプレートを回帰ケースとして全 PASS を確認（既存スキルが新チェックで落ちたらスキル側をハードストップ形式に修正）。check_deploy_drift.py の拡張は、ダミー配置先ディレクトリを scratchpad に作って「レジストリループ・issues 回収（マーカー前後の切り分け）」を確認し、既存のドリフト 3 分類が回帰していないことも同時に確認。
- **スキル本文の検証**: 静的層で締める（ユーザー方針）。素通り検査（実行層）は資産として整備するがデフォルトでは回さない — 回す場合はコスト明示の上で新設 4 スキルのハードストップを各 2 run。
- **E2E**: 対象外（コードプロダクトではない）。

## Resolved questions（20260710 レビューで確定）

1. **実装順**: 承認 — (1) pr-feedback → (2) validator 拡張 → (3) design-premortem → (4) session-retrospective → (5) skill-harvest → (6) impl-tournament → (7) skill-test 実行層。
2. **静的チェックの強度**: FAIL で確定（項目 6・7。エスケープコメント付き）。
3. **premortem の位置づけ**: 任意提案で確定（design-doc の必須ステップにしない）。
4. **deployments.md の形式**: パスのみの最小レジストリで確定。レビューで判明した設計の穴 — 配置先には skill-issues.md を書くルールが無く harvest が空振りする — は、session-retrospective の併配（producer / consumer の対）で埋める。本文・starter-kit に反映済み。
5. **impl-tournament の変種数上限**: 3 で確定。コスト対策として Step 1 の見積にモデル振り分け案（変種実装は安価なモデル・採点は上位モデル）を含める。本文反映済み。
6. **session-retrospective の自動化**: しない（手動起動のみ）で確定。手動運用で価値が実証されたら `.retro-needed` フラグへの昇格を検討。

## Premortem（20260710 セルフレビュー・反映済み）

design-premortem のチェックリストを本設計に適用した結果。全件本文に反映済み。

1. **攻撃**: session-retrospective のフォールバック（アクティブタスク無し → 起票しない）が、harvest との producer/consumer の対を `.steering/` 運用の無い配置先で無効化する / **影響**: 併配しても harvest が空振り / **対処**: `.steering/[date]-retrospective/` の提案・承認後作成に変更（Step 2）
2. **攻撃**: harvest の再実行で回収済み issues を重複回収する / **影響**: compound に同じ原料が二重流入 / **対処**: 回収済みマーカー方式を追加（Step 4。書き込みは承認範囲・スクリプトは読み取り専用を維持）
3. **攻撃**: validator 項目 7 が「承認不要」に誤反応 / **対処**: 否定形を除外
4. **攻撃**: pr-feedback の flaky CI 再実行がどの承認にも属さない / **対処**: Step 5 の外向き操作に編入
5. **攻撃**: impl-tournament のリダイレクト先 design-doc が配置先に無い場合が未定義（自己完結原則違反）/ **対処**: Step 0 にフォールバック追記
6. **攻撃**: pr-feedback の発動フレーズが debug と衝突 / **対処**: description に相互境界を追記

7. **攻撃**（承認直後の修正 20260710）: 既存の `scripts/check_deploy_drift.py`（20260709 作成）がドリフト 3 分類を実装済みなのに、設計は新規 harvest.py の作成を指示していた / **影響**: 別モデルが重複スクリプトを作り、比較ロジック（source-commit 行除去・references/ 除外）が 2 箇所に分裂 / **対処**: 「既存スクリプトの拡張（レジストリモード + issues 回収の追加のみ）」に全面差し替え

セッションバイアスの残余: 本レビューは設計者自身によるもの。実装後の素通り検査（skill-test 実行層・任意）が独立検証の機会。

## Alternatives considered

- **skill-creator 経由でのスキル生成** — 却下。テンプレ + validator + 本設計書で契約準拠は構造的に担保されており、外部スキルを挟む必然性がない。
- **session-retrospective の Stop hook 自動化** — 保留。自動化はユーザー方針（課金・自動処理は慎重）と「摩擦の実証が先」の原則により、手動運用の実績を待つ。
- **skill-test シナリオを各スキルフォルダ内 `tests/` に置く** — 却下。マスター専用資産を配布物（スキルフォルダ）に混ぜない。ルート直下 `tests/passthrough/` に置く（リポジトリ構成の原則: マスター専用ツールはルート直下）。
- **配置先側に専用のエクスポートスキルを置く（push 型還流）** — 見送り。同一マシンの個人運用では pull 型（マスターから直接読む）で足り、専用スキルを作ると二者間契約が 1 つ増える。供給側の役割は session-retrospective の併配で満たす。配置先が別マシン・別権限になったら再検討する。
- **横展開方針を「各プロジェクトで独立に育てる」に変更する** — 本タスクでは扱わない。既存 ADR 20260612（マスター集中・手動コピー・改善はマスターへ還元）の改訂になるため、必要ならば別タスクとして提起する。skill-harvest は既存方針の「還元が人力」という弱点を埋めるもの。
- **pr-feedback を pr-create に統合** — 却下。pr-create は「マージしない」で終わる出口が明確で、往復処理は発動条件も停止契約も異なる。分離してそれぞれの description を鋭く保つ。
- **impl-tournament の勝者自動選定** — 却下。採点はレビュー観点の proxy であり、トレードオフの最終判断（保守性 vs 速度など）は人間の価値判断。比較表 + 推奨までが AI の担当。
- **review-* 群の専用 agent 定義化** — 見送り。現行のスキル + 汎用 subagent 方式で機能しており、モデル/権限をスキルごとに変える需要が出るまで待つ。
