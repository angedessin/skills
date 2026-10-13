# 設計: skillset-renewal

Created: 20261006（v4: ゼロベース刷新・評価で決める）
Status: **DRAFT — awaiting review**

<!-- Status は DRAFT / SPIKE / APPROVED の 3 値。既定は DRAFT。
     読み取り: Status 行の最初の語彙トークン ∈ {DRAFT,SPIKE,APPROVED}、以外は停止。
     実装可否の正本: DRAFT のみ実装禁止。SPIKE/APPROVED は実装可（SPIKE は外向き不可）。 -->

## 目的

スキル一式をゼロベースで作り直す。どのスキルも、フロントエンドの実際の作業で「素のモデルより良い結果を出す」ことを評価で示せた場合だけ残す。あわせて周辺の仕組みを Claude Code の標準（`settings.json`・sandbox・公式のレビュー構成）に乗せ直し、配布は「最初に 1 回コピーし、以後は配置先で育てる」形にして配布用の仕組みを撤去し、知識と記録は白紙から溜め直す。

ゼロベースにする理由は次の 3 つ。

- **書かれた時期:** スキルは 2026 年 6〜9 月に、旧世代のモデル向けに書かれた。公式（Fable 5 の prompting）は「旧モデル向けのスキルは規定しすぎて品質を下げうる。素の振る舞いの方が良ければ削除せよ」としている。本文の合計は約 14.5 万字ある
- **検証の不在:** スキルの調整はこのリポジトリのメタ作業（スキル・hook・Python の編集）の中で行われ、配置先は 0 件。フロントエンドの実作業での効果は一度も測られていない
- **継ぎ足しの複雑さ:** 本文の多くは事故のたびに足した注記で、スキル間の共有契約が 123 か所ある。周辺には約 2,900 行の Python（フラグ・状態機械・配布・整合性検査）がある

計測（付録「計測結果」）の位置づけは次のとおり。

- **skill-doctor（使用回数）:** マスターでのメタ作業の利用を数えたもので、フロントエンド作業での価値は語らない。削除にも維持にも使わない
- **prompt-audit:** 既知の悪い書き方の静的チェックで、効果や規定しすぎは測らない。個別の矛盾の指摘（#1〜#5）だけを使う

判定の根拠は、本タスクで行う比較評価（「スキルの評価」節）に置く。

## スコープ

### 対象
- スキルのゼロベースの作り直し（構造の判断による削除と、評価による判定）
- 評価専用のサンプルアプリ（リポジトリの外）と評価課題
- `.claude/agents/`（レビュー agent の作り直し）
- `.claude/settings.json` の中身の見直しと、配置先向け雛形の作成
- hooks の整理（フラグ系の撤去）
- 配布の簡素化（配布用のスキルとスクリプトを撤去し、README のコピー手順・依存の一覧と settings の雛形に置き換える。Claude Code 専用）
- 白紙化
  - `.steering/archived/` の撤去
  - `docs/knowledge/` と `docs/decisions/` の作り直し
  - BACKLOG の棚卸し
- `CLAUDE.md`・`README.md`・`docs/user-guide.md`・`docs/starter-kit.md`・`templates/`・`prompts/`
- `scripts/`・`tests/`（撤去した仕組みの検査を消し、新構成に合わせる）
- CI（`.github/workflows/validate.yml`）の削除。静的検査はローカルで回す

### 対象外
- Cursor での利用（Claude Code 専用にする。ユーザー決定）
- 配置先プロジェクトのアプリコード
- リポジトリ外の整理。次の 2 つは本タスクでは触らず、手順だけ案内する
  - `~/.claude/` のスキル（pr-create の二重登録の確認など）
  - claude.ai から同期している未使用スキル 8 本
- feature-pipeline の作り直し（削除だけ行う。各スキルが安定したあと、必要になったら別タスクで薄く作る）

## 制約

- 公式ドキュメントに根拠がある変更を基本とし、独自の目標値はその旨を明記する
- 承認制の対象への書き込みは Edit / Write ツールで行い、各フェーズでユーザーの承認を得る
  - 対象: `CLAUDE.md`・`SKILL.md`・`docs/`・`.claude/settings*`・`.claude/hooks/`
- 停止契約（外向き操作・本人の承認ゲート）は SKILL.md 本文に残す。prompt-audit も残すべきと判定している
- 課金を伴う検証（`claude -p` での計測・eval・passthrough 実走）は、実行前にコストを提示して承認を取る
- サードパーティの plugin（skill-creator・公式 code-review plugin を参考にする場合）は、取り込む前に目視で確認する
- permissions は各プロジェクトの `.claude/settings.json`（コミットして共有するもの）に書く
- git-flow で進める。作業は develop から切ったマージ用ブランチ `feature/skillset-renewal` に集める。区切りごとに子ブランチ（`feature/renewal-01-reset` など）で作業してマージ用ブランチへ PR でマージし、コミットごとに静的検査を緑に保つ。develop へのマージは最後の 1 回で、その前にアーカイブを済ませる。main へは release ブランチで出す
- **前提:** 作業を始める前に、リポジトリ `angedessin/skills` を非公開にする（ユーザーの操作。現在は PUBLIC）
  - `.steering/` の作業記録には案件名なども残っており、作業ツリーから消しても git の履歴には残るため、先に非公開にしておく

## 完了条件

- [ ] 刷新前の状態に git タグ `pre-renewal-20261006` が打たれている
- [ ] 評価専用のサンプルアプリと、候補スキルごとの作業課題・採点基準がある
- [ ] 候補スキルの全部について、3 条件の比較結果と「残す・置き換える・削除」の判定が decisions.md にある
- [ ] 残したスキルはすべて新しい「書き方の型」で書き直されている（現行の本文をそのまま残したものが無い）
- [ ] 残したスキルはすべてテストケースを持ち、刷新の後も回帰テストとして回せる（静的検査は毎コミット、発動テストは説明文の変更時、効果の評価は作成時と大きな書き直し時。課金を伴う実行は毎回見積もって承認を取る）
- [ ] スキルの集合が、判定結果と構造の判断で決めた削除の両方に一致する
- [ ] `.steering/archived/` が作業ツリーに無い（タグから参照できる）
- [ ] `docs/knowledge/` と `docs/decisions/` の白紙化
  - 新しい形で作り直されている
  - 持ち込んだ項目には、持ち込んだ理由（無いと何を間違えるか）が 1 行ずつある
- [ ] feature-pipeline・`pipeline_state.py`・`tests/state/` が削除されている
- [ ] フラグ（`.capture-needed` など）とフラグ系 hook（`session-stop.sh`）が撤去され、セッション開始時の三択が無い
- [ ] 改訂後の `.claude/settings.json`
  - sandbox が有効になっている
  - `$schema` がある
  - 重複したルールが整理されている
  - guard-env-read は削除されている（guard-gated-write・guard-gated-delete は残す）
  - `tests/sandbox/` の検査（「有効にする前に確かめること」）が緑
- [ ] 配置先向けの `settings.json` 雛形
  - permissions・sandbox・配る hook の登録を含む
- [ ] 配布用の仕組みの撤去
  - skill-deploy・skill-harvest・`deploy_skills.py`・`check_deploy_drift.py`・`deployments*.md` が削除されている
  - README に、コピー手順と依存の一覧（一緒に持っていくスキル・agent・hook、マスター専用の印）がある
  - validate が、依存の一覧と実際のスキル・agent の参照を突き合わせる
- [ ] レビューの評価セット（過去の誤検知・修正済み指摘＋見逃し用に仕込んだバグ）がある
- [ ] 新しいレビューが現行より誤検知の平均件数を下げ、仕込みバグの検出数を減らしていない（評価セットで計測し、結果を decisions.md に残す）
- [ ] 書き直し後のスキルに対して prompt-audit をもう一度回し、High・Medium の所見が無い
- [ ] 検証用の使い捨て配置先に README の手順でコピーし、スキル・hook・sandbox 下での lint と typecheck が動くことを確認した（ログを decisions.md に残す）
- [ ] 静的検査（`validate`・`validate:assets`・`test:hooks`・`lint`・`tests/assets`）が新構成で緑
- [ ] `CLAUDE.md` が行動ルールだけで 50 行以内（独自目標。validate で行数を検査する）
- [ ] decisions.md の判定表とスキルの集合が一致する（validate で突き合わせる）

## アプローチ

5 段階で進める。

1. **白紙化**
   - タグを打つ
   - `.steering/archived/` を撤去する。その前に、レビュー評価セットの材料（過去の review-result.md）を抜き出しておく
   - knowledge・ADR は新しい形で作り直す。持ち込むのは、審査を通った落とし穴だけにする
2. **構造の判断で削る**（評価を待たない）
   - feature-pipeline・状態機械・フラグ・配布用の仕組み（skill-deploy・skill-harvest とスクリプト）を、検査と一緒に消す
3. **評価の土台を作る**
   - 評価専用のサンプルアプリをリポジトリの外に作る
   - 候補スキルごとに作業課題と採点基準を作る
   - 現行スキルと素のモデルで回して基準値を取る
4. **書き直して比べる**
   - 候補スキルを新しい「書き方の型」でゼロから書き直す
   - 素のモデル・現行・書き直し版の 3 条件で比べ、残す・置き換える・削除するを決める
   - レビューは公式の構成で作り直し、評価セットで測る
   - `settings.json` を見直す
5. **配る準備**
   - README にコピー手順と依存の一覧を書き、settings の雛形を置く（「配布」節）
   - 検証用の配置先に手順どおりコピーして動作を確かめる

## 主要コンポーネント

### 刷新後のワークフロー

作業の大きさで 3 段階に分ける。

| 段階 | 例 | 流れ | `.steering/` |
|---|---|---|---|
| 小さな作業 | typo・数行の修正・設定の変更・さくっと作るモックや試作・調査だけの依頼 | Claude がそのまま進める。冒頭で「小さな作業として直接進めます」と 1 行で宣言する。レビューと知見保存は頼まれたときだけ | 作らない |
| 中くらいの作業 | 1 セッションで終わるが、決めることがある（API の形・コンポーネントの分け方など） | design-doc が会話の中で設計を示して止まる → OK をもらって実装 → frontend-code-review | 作らない |
| 大きな作業 | 複数セッションにまたがる・あとで経緯を辿りたい | design-doc（`.steering/` を作成・承認待ちで停止）→ design-premortem（任意）→ impl-from-design ⇄ tdd / e2e → frontend-code-review → knowledge-capture → steering のアーカイブ（capture の確認を 1 回）→ pr-create → マージ（人間） | 作る |

> この表は暫定。各スキルを残すかは評価で決まるため、ワークフローの確定と CLAUDE.md の書き直しは評価の判定が出た後に行う。たとえば design-doc が削除になった場合、中くらい・大きな作業の流れは作り直す。

- **段階を上げる条件:** 次のどれかに当たれば、小さな作業として扱わない
  - 承認制のパス（CLAUDE.md・docs・`.claude/`・settings）に触る
  - 3 ファイル以上を変える
  - 公開している API・型・コンポーネントの使い方を変える
  - 原因がわからない不具合を調べる
- **段階の決め方:** 上の条件に当たらない範囲で、Claude が段階を決めて宣言する。迷う場合（たとえば小さく見えるが設計の判断を含む）だけユーザーに聞く。ユーザーはいつでも段階を変えられる（「ちゃんと設計して」「直接やって」）
- **中くらいの作業の記録:** `.steering/` を作らないので、会話の中で決めた設計は compaction で消える。実装を始める前に、決めたことを 5 行程度に要約して会話に残し、最後にコミットメッセージか PR の本文へ写す
  - frontend-code-review の結果も `.steering/` が無ければ会話に出すだけにする（`review-result.md` は大きな作業だけ）
  - 現行の CLAUDE.md は「新しいタスクは必ず design-doc。縮退は必ずユーザーに確認」で、小さな作業でも毎回確認が入る
  - prompt-audit も、この規則と design-doc 側の判定（「30 分以内のバグ修正はそのまま実装」）の食い違いを指摘している（#6）
- **モックの扱い:** 捨てる前提の試作は小さな作業として扱い、テストは求めない。試作を本実装に育てるときに、大きな作業として design-doc から始める
  - 既存の SPIKE（`.steering/` の中で探索実装する）は大きな作業の中の探索用として残す
- **途中で大きくなった場合:** 小さな作業のつもりが判断を含み始めたら、Claude がそこで止まり、段階を上げるか聞く

### スキル（ゼロベース）

**構造の判断で削除する（評価しない）**

| スキル | 理由 |
|---|---|
| `feature-pipeline` | 部品が固まるまでオーケストレーターは作らない。状態機械（`pipeline_state.py`）も一緒に消す |
| `skill-deploy`・`skill-harvest` | 配布は最初の 1 回のコピーだけで、以後は配置先で育てる。更新と回収の仕組みは要らない（ユーザー決定）。README の手順で置き換える |
| `empirical-prompt-tuning` | 公式の skill-creator の評価手順で置き換える。prompt-audit の High もここにある |
| `review-a11y`・`review-correctness`・`review-performance`・`review-security`・`review-ui`・`impl-review`・`test-review` | レビューを作り直し、観点は agent に持たせる（「レビューの構成」節） |
**評価して決める候補**

| グループ | スキル | 作業課題の例（サンプルアプリ上） | 素のモデルでは崩れそうな点（評価で確かめる） |
|---|---|---|---|
| 設計 | `design-doc`・`steering`・`design-premortem` | 「一覧画面に絞り込みを足す」の設計。2 セッション目で再開する | 承認前に実装に入る・セッションをまたぐと経緯を失う |
| 実装 | `impl-from-design`・`tdd`・`e2e` | 承認済み design.md からの実装。バリデーションのテストファースト実装。主要導線の E2E | 設計からの逸脱・テストが実装をなぞるだけになる・flaky な E2E |
| レビュー | `frontend-code-review` | 仕込みバグ入りの差分（評価セット） | 誤検知・見逃し |
| 知識 | `knowledge-capture`・`compound`・`rule-audit`・`session-retrospective` | 作業後の知見保存。ルールの昇格と剪定 | 承認前の CLAUDE.md 書き込み・どうでもいい知見の保存 |

評価しないスキル（評価の規模の決定による）:

| スキル | 扱い |
|---|---|
| `pr-create` | 新しい型で書き直し、push と PR 作成の前で止まるかを `plugin eval` のケース（`tool_used` の `max: 0`）で確かめる |
| `debug`・`pr-feedback`・`security-audit`・`impl-tournament` | 削除する。必要になったら新しい型で作り直す |
| `adr`・`skill-test`（マスター専用） | 評価の対象外（マスターの保守用）。書き直しだけ行う。skill-test は、静的検査と `plugin eval` の実行（課金の見積もりと承認を含む）をまとめる薄い入口に作り直す（自作の passthrough は削除するため） |
### スキルの評価

公式の skill-creator が勧める「スキルあり・なしの比較」を、3 条件に広げる。

| 条件 | 中身 |
|---|---|
| A: 素のモデル | スキルなし（Claude Code の標準とバンドルスキルだけ）。CLAUDE.md のうちスキルに触れない部分だけを持つ |
| B: 現行 | 現行のスキル（タグ `pre-renewal-20261006` の版） |
| C: 書き直し版 | 新しい「書き方の型」でゼロから書いたスキル |

- **評価の道具:** Claude Code 公式の `claude plugin eval`（v2.1.296 で確認）。自作の実行スクリプトは作らない（自作の Python の保守が刷新の理由の一つで、CLI の変化への追従も自分の負担になるため）。評価のケースは刷新の後も回帰テストとして残す
  - B・C はそれぞれ評価用の `plugin.json` で plugin として読み込ませる（配布はコピーのまま。`plugin.json` は評価のためだけに置く）
  - A（素のモデル）は道具の no-plugin baseline を使う。B を流すときに A も回し、C を流すときは `--ablation none` で A を重ねて払わない
  - CLAUDE.md の扱い: スキルに触れない部分（ブランチ運用・承認制など）は `append_system_prompt` で全条件に入れる。スキルに触れる部分（「design-doc を使う」など）は B・C の plugin 同梱の SessionStart hook でだけ注入する（試作で、隔離下でも plugin の hook が動き、no-plugin の条件には入らないことを確認した）。実際の作業では CLAUDE.md が常にあるため、それとの差でスキルの価値を測る
  - 機能がサーバー側で止められた場合（公式ドキュメントに記載あり）に限り、自作の実行スクリプトで代える
- **評価の場所:** 評価専用のサンプルアプリ（React・TypeScript・Vitest・React Testing Library・MSW・Playwright）。リポジトリの外に作り、ケースの準備スクリプト（`context.scaffold_script`）で毎回の空の作業場所に複製する
- **課題の数:** 候補スキル 1 本あたり 2〜3 件
- **採点の観点**
  - **結果の質:** 課題ごとに採点基準を先に書く（例: テストが振る舞いを検証しているか・設計から逸脱していないか）
  - **停止契約:** 止まるべき場所で止まったか。`tool_used` の採点（`max: 0`）で、外向きの操作（`git push`・`gh pr create` など）を試みなかったかを判定する
    - 「止まったか」（禁止の操作を試みなかったか）と「止まり方の質」（レビューを求めたか・Status の書式など）は別の採点項目に分ける。試作では、スキルなしの条件が src に触れずに止まったのに、レビューを明示的に求めなかったことで停止の項目が不合格になった
  - **コスト:** トークン量と所要時間（道具の JSON 結果から取る）
- **採点の方法:** 機械で判定できるもの（ファイル・ツール呼び出し・正規表現）は機械で判定する。残りは採点基準に沿って `llm` の採点役が判定する。最終判断はユーザーが結果を見て行う
- **判定のルール**（上から順に当てはめる）

  | 結果 | 判定 |
  |---|---|
  | 停止契約: B・C のどちらかが 1 回でも破った | その条件は不合格（品質に関係なく） |
  | A が品質で最良、または A と最良の条件との差が閾値未満で、A も停止契約を守る | 削除する |
  | C が B 以上（差が閾値未満の場合は、トークン量の少ない方） | C に置き換える |
  | C が B より悪い | 固定しておいた未使用の課題で C を直し、再評価する（1 回まで）。それでも悪ければ、B を新しい型に合わせる最小の手直しに留め、理由を decisions.md に残す |

  - 品質の差の閾値は、採点基準の満点の 10%（課題ごとの平均で比べる）。独自の基準
  - スキルの組み合わせで効くもの（design-doc と impl-from-design の Status 契約など）は、依存表を作り、片方だけを外す条件も回す
  - 判定は decisions.md の決まった書式の表（スキル・条件ごとの得点・停止・トークン・判定）に残す。validate はこの表と実際のスキルの集合を突き合わせる

**評価の手順の固定**（結論が歪まないようにする）

道具が満たすもの:

| 問題 | 道具での扱い |
|---|---|
| 混入 | 毎回、隔離された非対話セッションで動く。ユーザー設定・hooks・CLAUDE.md・MCP・他の plugin・メモリは読み込まれない。作業場所も毎回空から始まる |
| ばらつき | 課題 × 条件ごとに 3 回回し、平均で比べる（既定の `runs: 3`）。停止契約は 3 回中 1 回でも破れたら不合格 |
| 費用 | 費用の見積もりが結果に出る。`--max-cost-usd` で上限を掛ける |

自分で用意するもの:

| 問題 | 対策 |
|---|---|
| B の再現 | 現行のスキルは scripts・hook・CLAUDE.md・`.steering/` の構成に依存する。タグから、スキル・agent・hook・必要な scripts をまとめた「B の plugin」を作る。プロジェクトの CLAUDE.md は隔離で読み込まれない（準備スクリプトで書いても読まれない）ため、上の「CLAUDE.md の扱い」のとおり `append_system_prompt` と plugin の hook に分けて近似する。この近似は B に不利な方向の差になりうることを判定時に考慮する |
| ツールの許可 | 許可していないツールはセッションから消え、試みも記録されない。停止の判定が無意味にならないよう、Write・Edit・Bash を `--allow-tools` で許可する（Bash は OS の sandbox 内で動き、ネットワークは使えない） |
| サンプルアプリの準備 | 準備スクリプトは 120 秒の制限があり、実行中の Bash はネットワークを使えない。`pnpm install` 済みの `node_modules` ごと複製する手順にする |
| 課題の有利な作り込み | C を書き始める前に、課題・採点基準・仕込みバグをコミットして固定する。普段の作業に近い課題も混ぜる。再評価用に、使わない課題を各グループ 1 件取っておく |
| 採点の偏り | `llm` の採点役は会話のログを見るとスキル名から条件がわかるため、最終回答と生成ファイル（`focus: last_message` / `source: file`）を中心に採点する。採点役は `--judge-model` で実行と別のモデルにする。グループごとに 2 件を人も採点し、採点役との一致を確かめる |
| バージョンの変化 | Claude Code のバージョンとモデル名を毎回の結果に記録する。評価の期間中は自動更新を止める |
| 対話が要る課題 | 承認待ちで止まる・続きから再開する課題は、会話の記録（`context.history_file`）から 1 ターン再開する形で書く。複数ターンの台本は書けないため、課題を 1 ターンの区切りに分ける |
| 材料 | 現行の skill-issues.md・blockers.md・decisions.md に残る「モデルが実際に崩れた事例」を、白紙化の前に抜き出して課題の候補にする |

- **回し方**
  - 書き直しはグループ単位で進める（設計 → 実装 → レビュー → PR → 知識の順）
  - グループごとに A・B・C を回して判定する
  - 1 グループ目の実費（利用枠の消費）を測ってから、残りの規模を決める

### 書き方の型（書き直しの共通ルール）

- 冒頭 20 行以内に「いつ使うか・何をするか・どこで止まるか」を書く（compaction 後は先頭しか残らない）
- 停止契約（外向き操作・本人の承認ゲート）は本文に置き、手順として固定する。それ以外は目標と判断基準だけを書き、手順の細部はモデルに任せる
- 書くのは「何をするか」。経緯や事故の記録は書かない（必要なら knowledge へ）
- 一律の自己検証やサブエージェント検証は指示しない。fresh-context の検証は、レビューと長い自律実行にだけ置く
- description は主な用途を先頭に置き、発動語の例は `when_to_use` に分ける
- スキル間で共有する契約の語は最小にする（Status の 3 値と `.steering/` の構成程度）
- 本文の目安は 6,000 字以内（compaction 後に再添付される先頭 5,000 トークンに対する安全マージン。独自目標）

### レビューの構成

**精度が低い原因（推定）**

1. **領域のずれ:** このリポジトリの過去 13 件のレビューは、スキル・hook・Python・Markdown が対象だった。フロントエンド用の 7 軸を当てたため、多くの軸は「対象なし」になり、残る軸は一般論の指摘に寄った
2. **検証の工程が無い:** 一次レビューの指摘がそのまま残る。公式 plugin は、指摘ごとに別の agent で検証している
3. **規約の知識が薄い:** 規約担当（impl-review）は `docs/knowledge/` を読むが、中身はスキル設計と Claude Code の設定だけで、React・TypeScript の規約が無い。根拠にできる規則が無いと、好みの指摘が増える

1 と 2 は構成の問題、3 は知識の問題。対策は次の 2 つ。

- **構成:** 中核（バグ・規約・検証）は言語を問わない形にし、フロントエンドの軸は該当ファイルの変更時だけ足す
- **知識:** 規約担当は、根拠となる規則（CLAUDE.md・`docs/knowledge/`）を引用できない指摘を出さない。規則が無いことに気づいたら「規約が無い」と 1 行で報告し、knowledge-capture の候補にする

公式 code-review plugin（[commands/code-review.md](https://github.com/anthropics/claude-code/blob/main/plugins/code-review/commands/code-review.md)）の構成を参考にする。

1. **適用判定:** 変更が無い・自明な変更ならレビューしない
2. **規約の収集:** 変更ファイルに関係する CLAUDE.md・`docs/knowledge/`・design.md のパスを集める
3. **並列の一次レビュー**
   - **常に走らせるもの:**
     - バグ担当の 2 体（Opus 系）。1 体は差分だけを見る。もう 1 体は変更コードの周辺まで見る
     - 規約担当の 1 体（Sonnet 系）。違反した規則を引用できる場合だけ指摘する
   - **変更内容に応じて足すもの:**
     - UI とアクセシビリティの 1 体（`*.tsx` の変更時）
     - テスト品質の 1 体（テストファイルの変更時）
     - パフォーマンスとセキュリティは、該当する変更があるときだけ
   - 各 agent に「指摘しないもの」を明示する: 既存の問題・リンタで拾える問題・入力次第の推測・好みの問題
4. **指摘ごとの検証:** 一次レビューの指摘 1 件ごとに、別の agent が本当に問題かを確かめる。確かめられなかった指摘は捨てる
5. **出力:** 検証を通った指摘だけを `review-result.md` に書く。捨てた件数も残す（誤検知率の計測に使う）

レビュー agent は 7 本から 4〜5 本（バグ・規約・UI と a11y・テスト・検証役）にまとめる。各軸のチェック項目は agent 本文に持たせ、`skills:` の preload はやめる。

### 評価セット（レビュー）

| 種類 | 材料 | 測るもの |
|---|---|---|
| 誤検知 | 過去の review-result.md で「誤検知」とされた指摘（約 7 件） | 新しいレビューが同じ指摘を出さないか |
| 真の指摘 | 過去に修正まで行った指摘（約 11 件）。修正前のコードを git から取り出す | 新しいレビューが同じ問題を見つけるか |
| 見逃し | React・TypeScript の典型的なバグ（stale closure・非同期のレース・null の取りこぼし・a11y の欠落など）を仕込んだ小さな差分を 10 件ほど作る | 見逃し率 |

過去の材料（誤検知・真の指摘）はスキル・hook・Python の差分なので、マスターでの精度を測る。仕込みバグはフロントエンドの差分なので、配置先での精度を測る。この 2 つは分けて集計する。

- **指標:** 差分 1 件ごとに、出た指摘を人が「本物 / 誤検知」にラベル付けし、誤検知の総数と仕込みバグの検出数を数える。過去の指摘と同じかどうかではなく、新しく出た誤検知も数える
- **回数:** 各差分を方式ごとに 3 回回す
- **判定:** 新方式が採用になるのは、誤検知の平均件数が現行より少なく、仕込みバグの検出数が現行以上のとき
- **固定の順序:** 仕込みバグの差分は、新しいレビュー agent の観点を書く前に作ってコミットで固定する。公開されている React のバグ事例も混ぜる
- **現行の基準値:** 現行レビューの基準値は、review-* スキルを削除する前（タグの状態の一式）で取る
- **過去の差分の取り出し:** review-result.md には指摘時点のコミットが無いものがある。抜き出しの作業で、日付と対象ファイルからコミットを特定する（特定できないものは使わない）

置き場所は `tests/review-eval/`。実行は課金のため承認制にし、現行のレビューと新しいレビューの両方で回して比べる。

### settings.json

公式（[Settings](https://code.claude.com/docs/en/settings)・[Permissions](https://code.claude.com/docs/en/permissions)・[Sandboxing](https://code.claude.com/docs/en/sandboxing)）に照らした見直し。

**現状の問題**

- **Bash の文字列パターンは抜けやすい:** 公式も「Bash の引数を制限するパターンは脆い」と明記している。`sh -c` 経由やパス指定で呼ぶと deny が効かない
  - 現状はこれを自作の guard hook 3 本（guard-gated-write・guard-gated-delete・guard-env-read）と大量の deny で補っている
  - hook 側も取りこぼしが残っている（BACKLOG 0.6）
- **sandbox が無い:** sandbox は Bash とその子プロセスを OS レベルで制限する（macOS は Seatbelt）
  - 標準で `.claude/` の設定・skills・agents・hooks への書き込みを禁止する
  - `denyWrite` と `denyRead` で任意のパスを足せる
- **重複がある:**
  - `.env` の読み取り禁止が三重になっている（`Read` の deny・`Bash(cat .env*)` 系の deny・hook）
  - docs の ask が `*`・`**`・`**/*` の 3 行ずつある
  - `Bash(ls)` の allow は組み込みの読み取り専用コマンドなので不要の見込み

**変更案（マスターの `.claude/settings.json`）**

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "ask": [
      "Bash(git push*)", "Bash(npx *)", "Bash(rm -r*)",
      "Edit(./CLAUDE.md)", "Edit(~/.claude/CLAUDE.md)",
      "Edit(./docs/**)", "Edit(./.claude/**)"
    ],
    "deny": [
      "Read(./**/.env*)", "Read(./**/*.pem)", "Read(./**/*.key)",
      "Read(~/.ssh/**)", "Read(~/.aws/**)", "Read(~/.claude/.credentials.json)",
      "Bash(git push --force*)", "Bash(git push -f*)", "Bash(git push * +*)",
      "Bash(git reset --hard*)", "Bash(git clean -f*)", "Bash(rm -rf *)", "Bash(rm -fr *)",
      "Bash(pnpm add *)", "Bash(npm install *)", "…（パッケージ追加系は現状どおり）"
    ],
    "disableBypassPermissionsMode": "disable"
  },
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "excludedCommands": ["git checkout *", "git switch *", "git merge *", "git rebase *", "git stash *", "git restore *", "git rm *", "git mv *", "git pull *", "git push *"],
    "filesystem": {
      "denyRead": ["./**/.env*", "./**/*.env", "~/.ssh", "~/.aws"]
    },
    "network": {
      "allowedDomains": ["github.com", "*.github.com", "registry.npmjs.org"]
    }
  },
  "hooks": { "…": "guard-gated-write・guard-gated-delete と、マスター専用（validate-skill-edit・remind-config-docs）" }
}
```

（deny の `Read(./*.env)`・`Read(./**/*.env)`・`Bash(printenv*)`・`Bash(env)` は現状どおり残す。削るのは `Bash(cat .env*)`・`Bash(cat *.env)`・`Bash(grep * .env*)`・`Bash(grep * *.env)` の 4 行だけ。sandbox の `denyRead` が全プロセスに効くため）

**変更の要点**

| 項目 | 変更 |
|---|---|
| sandbox の役割 | 守るのは 3 つ。秘密の読み取り（`denyRead`）、通信先（`allowedDomains`）、書き込み範囲（作業ディレクトリと一時ディレクトリだけ） |
| 承認制のパスの保護 | sandbox には「承認すれば進む（ask）」が無く、`denyWrite` にすると git の操作まで失敗する。リポジトリの成果物（CLAUDE.md・docs）は `denyWrite` に入れない。Bash からの書き込みは、従来どおり guard-gated-write・guard-gated-delete（ask）で守る |
| guard-env-read | 削除する。sandbox の `denyRead` が全プロセスに効き、Read ツールは `Read` の deny が守る |
| git の作業ツリー操作 | sandbox は `.claude/` への書き込みを標準で禁止する。そのため、`.claude/` のファイルを書き換える git 操作（ブランチ切り替え・マージ・削除など）は sandbox の中では失敗する。これらは `excludedCommands` で sandbox の外に出し、通常の承認の流れに乗せる（論点） |
| sandbox の外での再試行 | `allowUnsandboxedCommands: false`。失敗したコマンドを、sandbox の外で黙って再試行させない |
| ファイルの削除 | Claude Code の組み込みツールに削除の機能は無い。削除は `git rm`（上の除外で sandbox の外）で行う |
| ask のまとめ | docs は `./docs/**` の 1 行に、`.claude/` も 1 行にまとめる |
| `$schema` | 入れる（エディタでの補完と検証のため） |
| 確認なしモード | `disableBypassPermissionsMode` で自分でも入れないようにする |

**有効にする前に確かめること**（sandbox の中で実際にコマンドを流す検査として `tests/sandbox/` に置き、課金なしで繰り返せるようにする）

- stop-typecheck・post-edit-lint・mise 経由の pnpm・検査スクリプトが動く
- `.env` を `cat`・`grep -r`・`python` で読めない
- SSH での `git push` と `gh pr create` が通る（`excludedCommands` 経由）
- ブランチ切り替えとマージが通る

**評価の実行場所**

`claude plugin eval` は、sandbox を有効にした Claude Code の中からではなく、通常のターミナルから実行する。sandbox の中からだと、Anthropic の API への通信と、リポジトリ外の評価アプリへの書き込みが通らないため。

配置先向けの雛形は `templates/settings.template.json` に置く。中身は permissions・sandbox・配る hook の登録の 3 つ。公式の位置づけでは、`.claude/settings.json` はプロジェクトごとにコミットして共有する設定。スキル側の `allowed-tools` は「スキルの使用中は確認なしで使ってよいツール」を許可するもので、制限には使えない。

### 配布（最初に 1 回コピーし、以後は配置先で育てる）

ユーザー決定により、plugin ではなくコピーで配る。マスターはスターターキット（ベース）で、コピーした後は配置先で案件に合わせて育てる。マスターと配置先を揃え続けることはしない。

**plugin にしない理由**（公式ドキュメントで確認）

- plugin のスキルは配置先で書き換えられない（更新のたびに上書きされる）
- plugin のスキルを 1 本だけオフにできない（`skillOverrides` は plugin のスキルに効かず、オン・オフは plugin 単位）
- 配置先で調整できるのは、`userConfig` の値の埋め込みと、CLAUDE.md・docs を読ませることまで

**運用の方針**

- 配置先での書き換えは自由（現行 CLAUDE.md の「配置先で直接編集しない」「改善はマスターに還元して再コピー」を撤回する）
- 更新（マスターの変更を配置先へ流す）と回収（配置先の変更やフィードバックを集める）の仕組みは持たない
- スキルの改善はマスターでだけ行う（ユーザー決定）。改善の材料は、評価用のサンプルアプリでの評価と、マスターでの利用。改善の効果も、サンプルアプリで回して確かめる
  - 実案件で気づいたことを、ユーザーがマスターで課題として起こすのは自由。ただし、そのための仕組み（回収スキル・報告の書式）は作らない
- 配置先には `.claude/skills/` にそのままコピーする。スキル名は `/design-doc` のような素の名前になる

**残すもの**

| もの | 中身 |
|---|---|
| README のコピー手順 | コピーするディレクトリ（`.claude/skills/<選んだもの>`・`.claude/agents/`・`.claude/hooks/`）と、settings の雛形の使い方 |
| README の依存の一覧 | 一緒に持っていくもの（例: impl-from-design には design-doc、frontend-code-review にはレビュー agent）と、マスター専用の印（adr・skill-test）。手でコピーすると片方だけ持っていく事故が起きるため。validate が一覧と実際の参照を突き合わせる |
| `templates/settings.template.json` | permissions・sandbox・配る hook の登録。配置先でゼロから書くと抜けが出るため |

- スキルは自己完結に書く（配置先に CLAUDE.md・docs・`.steering/` が無くても動く）。スキルの書き直しの中で守る
- 撤去する仕組みの規模: スキル 2 本と、`deploy_skills.py`（490 行）・`check_deploy_drift.py`（272 行）。実際の配置先は検証用の 1 件だけだった

### 白紙化

| 対象 | 扱い |
|---|---|
| git タグ | `pre-renewal-20261006` を最初に打ち、リモートに push する（旧資料をタグから参照するため） |
| `.steering/archived/` | レビュー評価セットの材料を抜き出したあと、作業ツリーから削除する。参照はタグから |
| `docs/knowledge/` | 新しく作り直す。現行 3 ファイルから持ち込むのは、公式ドキュメントに無く、無いと Claude が間違える落とし穴のうち、新しいスキルが参照しそうなものだけ。Claude が候補を絞り、その候補だけを人がレビューする |
| `docs/decisions/`（ADR） | 現行の 10 本を削除する（ユーザー了承）。新しい ADR を 1 本（刷新の決定）書き、旧 ADR はタグから参照する |
| `.steering/BACKLOG.md` | 全項目が過去のタスクを基準にしているので、棚卸しして本タスクに取り込むか捨てる（下表）。ファイル自体は残し、刷新後の候補だけを置く |
| `.gitignore` のフラグ行 | 古いフラグが混入しないよう残す |

### BACKLOG の棚卸し（案）

| 節 | 内容 | 扱い |
|---|---|---|
| 0.5 | CI の actions 更新（期限 2026-10-19） | 捨てる（CI ごと削除するため） |
| 0.6 | guard-gated-delete の取りこぼし | 残す（guard-gated-delete は sandbox で置き換えず残すため。本タスクの対象外） |
| 1 | 依存表の網羅・README の節新設・passthrough のハーネス拡張（feature-pipeline の Gate 3.5 用） | 捨てる（README は書き直す。feature-pipeline は削除する） |
| 1.5 | rule-audit が `references/` を監査しない | 本タスクに取り込む（rule-audit の改善で入力に足す） |
| 1.6 | tasklist の一括 `[x]` を実体と照合するルール | 本タスクに取り込む（CLAUDE.md の書き直しで判断する） |
| 2 | mise 経由の pnpm | 捨てる（knowledge 持ち込み候補として審査する） |
| 3 | 20260730 レポートの後続（ほぼ完了） | 捨てる |
| 4 | データ待ちの 7 項目 | 本タスクで決着する（配布の作り直し・sandbox・skill-doctor の計測・レビュー軸の再編）。承認ゲートの再編は、停止契約を残す方針で決着とする |

### スキル以外の撤去と移設

| 対象 | 扱い |
|---|---|
| `scripts/pipeline_state.py`・`tests/state/` | 削除（使っているのは feature-pipeline と検査だけ） |
| `scripts/deploy_skills.py`・`check_deploy_drift.py`・`deployments*.md` | 削除（permissions の正本は settings の雛形へ移す。コピー手順は README へ） |
| `.claude/hooks/session-stop.sh` | 削除 |
| `.claude/hooks/session-start-check.sh` | アクティブタスクの一覧だけを注入する形に縮める。配置先にもコピーで配る |
| guard-gated-write・guard-gated-delete | 残す（sandbox には ask が無いため）。配置先にもコピーで配る |
| guard-env-read | sandbox の `denyRead` で置き換えて削除する。配置先には settings の雛形で sandbox を配る |
| post-edit-lint・stop-typecheck | 残す。配置先にもコピーで配る |
| `scripts/check_asset_consistency.py`・`tests/assets/` | 撤去した仕組みの契約を消す。資産の変更と同じコミットで直す |
| `scripts/validate_skills.py` | 撤去したスキルに紐づく項目を消す |

## 未解決の論点

- [x] **sandbox の設定内容** → 「settings.json」節の変更案のとおり（ユーザー決定）。sandbox は読み取り・通信・書き込み範囲を守り、承認制のパスは guard hook（ask）で守る
- [x] **git の作業ツリー操作を sandbox の外に出すか** → `excludedCommands` で外に出す（ユーザー決定）
- [x] **`failIfUnavailable` の値** → マスター（macOS）では `true`、配置先の雛形では `false`（ユーザー決定）
- [x] **サンプルアプリの置き場所と中身** → `~/Desktop/_lab/ai/skills-eval-app/`（このリポジトリの外。ユーザー決定）。検索・一覧・フォーム・API 呼び出し（MSW）を持つ小さなアプリで、評価用のバグを仕込める程度の規模にする
- [x] **PR グループの評価方法** → 評価しない（評価の規模の決定に従う）。評価専用リポジトリは作らない
- [x] **評価の規模と、評価しない既定** → 推奨案（ユーザー決定。「課金してでもやるべきことに絞る」）
  - 評価するのは、利用の中心になる 4 グループ（設計・実装・レビュー・知識）だけ
  - 調査・PR・その他（debug・pr-create・pr-feedback・security-audit・impl-tournament）は評価せずに決める。停止契約を持つ pr-create は新しい型で書き直し、`plugin eval` の停止のケースで確かめる。それ以外は削除し、必要になったら作り直す
  - **やめる条件:** 1 グループ目（設計）の実費が見込みの 2 倍を超えたら、残りのグループを課題 1 件・1 回に縮める
  - **規模の決め方:** まず設計グループ（約 70 実行・5 時間枠 2 回分の見込み）だけを回し、週間枠の消費を測ってから残りの規模を決める（ユーザー決定。試作の実測は 1 実行あたり 5 時間枠の約 2.5%・定価換算約 0.35 ドル）
- [x] **評価で普段の plugin を外すか** → 比較（A・B・C）では外す。加えて、採用が決まった一式を普段の環境（plugin あり）で 1 回だけ流す（ユーザー決定）
  - 外す理由: 外さないと、差がスキルによるものか plugin によるものか切り分けられない
  - 1 回流す理由: 実際の作業では feature-dev（code-reviewer など）や code-simplifier と同時に読み込まれる。説明文の競合による誤発動や、レビューの二重実行が起きないかは、普段の環境でしか確かめられない
  - 競合が見つかったら、スキルの `when_to_use` を直すか、その plugin を無効にするかを人が決める
- [x] **人によるラベル付けの負担** → 人が判定する。3 回の試行は維持し、人がラベルを付ける数を次の 3 つで減らす（ユーザー決定。Claude に判定させると、レビューと同じ偏りの物差しになるため）
  - 仕込みバグは場所がわかっているので、検出したかは機械で判定する。人は付けない
  - 過去の材料には、すでにラベル（誤検知・真の指摘）がある。同じ指摘かどうかは採点役が照合し、人は新しく出た指摘だけを見る
  - 3 回の試行で重なる指摘は、採点役がまとめてから人に出す（同じ指摘には 1 回だけ付ける）
  - 見込み: 新しい指摘は数十〜100 件程度で、1〜2 時間。まとめ方が正しいかは、最初の 3 差分で人が確かめる
- [x] **段階的にマージするか** → develop ではなくマージ用ブランチ `feature/skillset-renewal` に段階的にマージする（ユーザー決定。20261013 に git-flow へ移行し、親ブランチ `renew/skillset` から置き換え）
  - 区切りごと（白紙化と構造の削除 → 評価とスキルの置き換え → sandbox と配布）に、子ブランチ（例: `feature/renewal-01-reset`）からマージ用ブランチへ PR を出してマージする
  - 子ブランチはマージ用ブランチから切る。`feature/skillset-renewal/01-reset` のような階層名は、同名のブランチがあると git の制約で作れないため使わない。`.steering/` はマージ用ブランチで一本化する
  - develop へのマージは最後の 1 回だけで、その前にアーカイブを済ませる。刷新の途中状態（スキル・検査器が揃っていない時期）を develop に入れないため
  - 刷新中に develop へ別の作業が入ったら、develop をマージ用ブランチへ取り込んで差を小さく保つ
  - main へは release ブランチで出す
- [x] **非公開化の副作用の確認** → 影響なし（20261006 に確認）。CI は削除する。main にブランチ保護は設定されていない。Actions の請求設定（支払い方法・budget）は権限が無く未確認だが、CI を消すので関係しない
- [x] **小さな作業の決め方** → 「刷新後のワークフロー」節のとおり、Claude が段階を宣言し、迷うときだけ聞く（ユーザー決定）。CLAUDE.md の「縮退は必ずユーザーに確認」を緩めることになる
- [x] **`disableBypassPermissionsMode` を入れるか** → 入れる（ユーザー決定。自分で確認なしモードに入れなくなるだけで、普段の使い方は変わらない）
- [x] **knowledge に持ち込む項目** → 全件は確認しない（ユーザー決定）。Claude が現行 3 ファイルを読み、新しいスキルが参照しそうな項目だけを候補に挙げて人のレビューに回す。それ以外は確認せずに捨てる（タグから参照できる）
- [x] **レビュー評価セットの規模と課金** → 誤検知 7・真の指摘 11・仕込みバグ 10 の約 28 件（公開事例を足す場合はその分）を、現行と新方式で 3 回ずつ回す。費用は事前に見積もって提示する（ユーザー決定）
- [x] **レビューの判定基準** → 「レビュー」節の指標と判定のとおり（誤検知の平均件数が現行より少なく、仕込みバグの検出数が現行以上）。誤検知の判定は人が行う
- [x] `debug` の名前 → 不要（debug は評価せず削除するため。作り直すときに名前空間での共存を確かめる）
- [x] **配布の形** → plugin をやめ、コピーで配る（ユーザー決定。配置先でスキル全体をカスタマイズ・調整したいため）。これにより、plugin の名前・install scope・マスターの読み込み経路の決定は取り消し
- [x] **配布用の仕組み** → 撤去する（ユーザー決定。配布後は配置先で育てるため）。README のコピー手順・依存の一覧と settings の雛形だけを残す
- [x] **CI を残すか** → 削除する（ユーザー決定）。静的検査はローカルで回す。BACKLOG 0.5 は不要になる
- [x] タスクの分割 → しない（ユーザー決定）
- [x] Cursor → 対象外（ユーザー決定）

---

<!-- design-doc-boundary: appendix -->

> **付録** — 実装入口・resume の既定では読まない。プレモータム・TDD 突入・乖離調査など、当該節が必要なときだけ読む。人間の Phase 3 承認前は `影響範囲` と `検討した代替案` を必読。

## プレモータム所見（design-premortem）

### v4 に対する所見（20261006・2 回目）

premortem-attacker で実施した（会話の文脈なし・リポジトリ参照あり）。所見は 27 件（High 12）。主要な主張は呼び出し側で裏取りした。

- **確認できたこと**
  - Claude Code の組み込みツールに削除の機能は無い（公式のツール一覧）
  - リポジトリは PUBLIC で、fork は 0 件
- **公式ドキュメントと食い違ったこと:** 非公開 marketplace の自動更新は、git の認証情報ヘルパーで認証される。`GITHUB_TOKEN` は単独では効かない

**反映済み（設計本文を修正）: 22 件**

- **sandbox**
  - git の作業ツリー操作が `.claude/` の標準の書き込み禁止に当たる（S1） → `excludedCommands` で sandbox の外に出す案にした（論点）
  - 成果物を `denyWrite` に入れると承認の余地なく失敗する（S1・S6） → `denyWrite` をやめ、承認制のパスは guard-gated-write・guard-gated-delete（ask）で守り続ける。guard-env-read だけを sandbox で置き換える
  - 「Delete ツール」は Cursor のツールで、Claude Code には無い（S2） → 削除は sandbox の外に出した `git rm` で行うと明記した
  - `claude -p` の通信先と評価アプリへの書き込みが sandbox で通らない（S3） → 評価と passthrough は通常のターミナルから実行すると明記した
  - SSH の push が通るか未確認（S4） → 有効にする前に確かめる項目に足した
  - deny の削除で `*.env` と `printenv` の保護が消える（S5） → 消すのは `cat`・`grep` の 4 行だけと明記した
  - sandbox の挙動を検査する手段が無い（S6） → 実際にコマンドを流す `tests/sandbox/` を足した
  - 完了条件の矛盾（S7） → hook の扱いに合わせて書き直した
- **3 条件評価**
  - 混入（E1） → 評価専用の設定・auto memory を切る・毎回新しいパスで回す
  - B の再現（E2） → タグから「B の一式」を作る
  - 権限モードで A が有利になる（E3） → acceptEdits に固定し、試みたかどうかで停止を判定する
  - ばらつき（E4） → 3 回の試行と、品質の閾値（満点の 10%）
  - 判定ルールの抜け（E5） → A が最良の場合と依存表を足した
  - 課題の作り込みと過学習（E6） → 事前に固定し、再評価用の課題を取っておく
  - 採点の偏り（E7） → 痕跡を伏せる・別のモデルで採点・人との一致を確かめる
  - バージョンの変化（E8） → 記録と自動更新の停止
  - 対話が要る課題（E9） → `--resume` と台本
- **レビュー評価**
  - 指標の定義（R1） → 人がラベル付けして、誤検知の総数と仕込みバグの検出数で判定する
  - 仕込みバグの固定（R2） → agent の観点を書く前に固定し、公開事例も混ぜる
  - コミットの特定（R3） → 特定できない材料は使わない
  - 現行の基準値（R4） → 削除の前に取る
- **白紙化**
  - 崩れた事例の抜き出し（B1） → skill-issues.md などから課題候補を抜き出す
  - タグの push（B4） → 足した
- **ワークフロー**
  - 中くらいの作業の記録とレビューの出力先（W1） → 5 行の要約と、会話への出力
  - 評価の結果を先取りしている（W2） → 表を暫定とし、確定を評価の後にした
  - 段階を上げる条件が曖昧（W3） → 4 つの具体的な条件を足した
- **不整合**
  - マスターの読み込み方の食い違い（P2） → データフローを論点の扱いに揃えた
  - 完了条件の機械検査（P3） → 判定表と CLAUDE.md の行数を validate で検査する
  - session-retrospective の重複（P5） → 知識グループの評価に一本化した

**反論したもの: 3 件**

- **portability の検査の撤去（P4）**
  - 反論: Agent Skills の可搬性としては不要になる。ただし、配るスキルにマスター専用の名前や語彙が混ざるのを検出する役目は残る
  - 判断: 撤去せず、目的を「マスター語彙の混入検出」と明記して残す
- **fork 経由の流出（B2）**
  - 反論: fork は 0 件で、公開中の fork は無い。clone されたかは知りようがない
  - 判断: 履歴の書き換えはしない（論点にもしない）
- **自動更新に `GITHUB_TOKEN` が要る（B3 の一部）**
  - 反論: 公式ドキュメントに反する。必要なのは認証情報ヘルパーで、このマシンは SSH で認証できる
  - 判断: 対応しない。Actions の無料枠とブランチ保護の変化は、非公開化の副作用として論点に入れる

**人間の判断に委ねる: 未解決の論点へ追加・更新（6 件）**

- git の作業ツリー操作を sandbox の外に出すか（S1）
- `failIfUnavailable` の値（S8）
- 評価の規模と、評価しない既定・やめる条件（E10。High）
- 評価で普段の plugin を外すか（E1）
- 人によるラベル付けの負担（R1）
- 段階的に main へマージするか（P1。High。CLAUDE.md のアーカイブ規則とぶつかる）

（このプレモータムは設計を承認しない。design-doc の Phase 3 の人間レビューに戻る）

### v2 に対する所見（20261006・1 回目）

20261006、v2 に対して実施した（premortem-attacker・所見 40 件弱）。v3 では次のように扱った。

- **v3 でも有効なので反映したもの**
  - 配置先 0 件
  - 停止契約を本文に残す
  - 移行の途中で guard と検査が切れないようにする
  - guard の対象パスに `plugins/` を加える
  - permissions の正本の移動先
  - マージ前のアーカイブ
  - `.gitignore` のフラグ行
  - 作業ブランチ
  - skill-creator の採用前確認
  - pr-create に disable-model-invocation を付けない
- **v3 で前提ごと消えたもの**
  - feature-pipeline の観測値とフラグ廃止の整合（feature-pipeline と状態機械を削除する）
  - ADR を 1 本ずつ Superseded にする作業の漏れ（ADR を白紙化する）
  - 統合スキルの description の肥大（よく使うスキルは統合しない）
  - Cursor の読み込み（対象外にした）
- **v3・v4 で新たに生じたもの:** 白紙化・sandbox・レビュー評価セット・ゼロベースの評価。これらは v2 のプレモータムでは見ていない。必要なら v4 に対して再度プレモータムを行う

## データフロー

```
[マスター（ベース）]
  .claude/{skills,agents,hooks}（配布可とマスター専用）
  templates/settings.template.json（配置先の permissions・sandbox・hook 登録）
  README（コピー手順・依存の一覧）

[配置（最初の 1 回）]
  README の依存の一覧を見てスキルを選ぶ → .claude/{skills,agents,hooks} をコピー
  → settings の雛形を .claude/settings.json として置き、案件に合わせて直す → 配置先でコミット

[以後]
  配置先で案件に合わせて育てる。マスターとは同期せず、配置先からのフィードバックも受け付けない
  スキルの改善はマスターでだけ行い、サンプルアプリの評価で確かめる

[タスクの流れ]
  design-doc（承認待ちで停止）→ design-premortem（任意）→ impl-from-design ⇄ tdd / e2e
  → frontend-code-review（一次レビュー → 指摘ごとの検証）
  → knowledge-capture → steering のアーカイブ（capture の確認を 1 回）
  → pr-create → マージ（人間）
```

## 影響範囲

- システム / 外部連携: GitHub Actions の CI を削除する。sandbox を有効にすると、ネットワークやファイルに触るコマンドの一部が承認待ちか失敗になる（論点で範囲を決める）
- データ: `.steering/archived/` と旧 knowledge・ADR は作業ツリーから消え、タグからだけ参照できる。過去の判断の経緯を探すときは `git show pre-renewal-20261006:<path>` を使う
- 利用者: 自分 1 人。削除するスキルの名前は使えなくなる。評価で削除が決まったスキルも同様
- リグレッション懸念:
  - 新しいレビューで見逃しが増える（評価セットで計測し、増えたら構成を戻す）
  - sandbox で hook（stop-typecheck・post-edit-lint）が動かなくなる（先に確かめる）
  - knowledge の白紙化で、過去に踏んだ落とし穴を再び踏む（持ち込みの審査で補う）
  - feature-pipeline の削除で、工程のつなぎを毎回手で指示する手間が増える（増えたら薄く作り直す）
  - マスターの改善が既存の配置先に届かない（育てる方針として受け入れる）
  - 実案件での不具合がマスターに届かず、マスターの改善がメタ作業とサンプルアプリに偏る（サンプルアプリの評価課題を、実作業に近い形に保つことで補う）

## テスト方針

- 静的: `validate`・`validate:assets`・`test:hooks`・`lint`・`tests/assets` を新構成に追従させ、グループごとに緑にする
- スキル: 「スキルの評価」節の 3 条件比較をグループごとに行う（利用枠を消費する。1 グループ目の実費を見てから規模を決める）
- レビュー: `tests/review-eval/` を現行と新方式で回し、誤検知率と見逃しを比べる（利用枠を消費する）
- 停止契約: `plugin eval` の停止のケース（`tool_used` の `max: 0`）で確かめる。対象は design-doc・pr-create・knowledge-capture の 3 本（課金・承認制）。自作の passthrough（`passthrough_check.py`・`tests/passthrough/`）は置き換えが済んだら削除する
- 配置: 検証用の使い捨て配置先に README の手順でコピーし、スキル・hook の発火・sandbox 下での lint と typecheck を確かめる。依存の一覧の抜けは validate で検査する

## 検討した代替案

| 代替案 | 却下理由 |
|---|---|
| 全スキルを統合して 14 本前後にし、本文を全面的に書き直す（v2） | 統合の効果（一覧の常時コストの削減）は 29 本で 3,000 トークン弱と小さい。書き直しの判断が評価に基づいていない |
| よく使うスキルは改善に留める（v3） | 根拠にした使用回数はマスターのメタ作業のもので、フロントエンドでの価値を示さない。prompt-audit も効果や規定しすぎを測らない。弱いデータで維持を決めることになる |
| 評価なしで全面的に書き直す | 書き直し版の方が良いという主張にも根拠が無くなる。停止契約が壊れても気づけない |
| 実案件のプロジェクトで評価する | 会社の案件のコードとやりとりを評価に使うことになる。条件ごとにまっさらな状態から始めにくい |
| feature-pipeline を残して書き直す | 部品を書き直す最中にオーケストレーターも書き直すと二重に壊れる。使用は 95 日間で 3 回 |
| `.steering/archived/` と旧 knowledge を残す | 検索のたびに古い契約名を拾うノイズになる。経緯は git タグで十分に辿れる |
| レビューの 7 軸を維持し、プロンプトだけ強める | 検証の工程が無いことが誤検知の主因。公式 plugin は軸を絞り、指摘ごとの検証で精度を上げている |
| permissions を配らず、各配置先で手書きする | 公式の位置づけでは `.claude/settings.json` はプロジェクトにコミットする共有設定。雛形を置いてコピーで配るのが標準に沿う |
| スキルの `allowed-tools` で使ってよいツールを制限する | `allowed-tools` は確認なしで使える範囲を広げるもので、制限には使えない |
| plugin と marketplace で配る（v4 の当初案） | 配置先でスキル本文を書き換えられず、1 本単位でオフにもできない。ユーザーは配置先でスキル全体をカスタマイズしたい（ユーザー決定） |
| plugin を用途ごとに 2〜3 個に分ける | 1 本単位の選択には近づくが、本文の書き換えはできないまま |
| コピー配布の仕組みを作り直す（配置・3-way マージでの更新・回収） | 配置先で育てるなら、マスターと揃え続ける仕組みは要らない。実際の配置先は検証用の 1 件だけで、約 760 行の Python と 2 本のスキルに見合わない（ユーザー決定） |
| 再コピーで配置先を上書きする（現行） | 配置先のカスタマイズが消える |

## 調査結果

### 計測結果（20261006。`claude -p` で実行。生データは measure/）

- **prompt-audit:** 所見 10 件（High 1・Medium 5・Low 4）
  - High は empirical-prompt-tuning の「確認なしで直接修正」で、CLAUDE.md の承認制と矛盾する
  - Medium は次の 3 件
    - 同じファイル内の矛盾（1 修正 1 イテレーション）
    - 古いツール名（Task tool）
    - 経緯の語り（impl-review・review-a11y）
  - 強調表現・思考誘導・旧モデル向けの回避策はほとんど無い
- **skill-doctor:** Claude Code での使用回数
  - design-doc 73・impl-from-design 53・steering 38・frontend-code-review 34・knowledge-capture 29・compound 19・design-premortem 9・skill-test 5・adr 4・skill-harvest 4・rule-audit 3・impl-review 3・review-a11y 3・review-ui 3・feature-pipeline 3・skill-deploy 3・pr-create 2・debug 2・empirical-prompt-tuning 2・review-performance 2・その他 0〜1
  - 一覧の常時コストは 1 本あたり約 40〜230 トークン
- **過去のレビュー結果:** 13 件。誤検知と記録された指摘が約 7 件、修正まで行った指摘が約 11 件
- **スキル本文の規模:** 合計約 14.5 万字（本文が 6,500 字を超えるもの: feature-pipeline・frontend-code-review・design-doc・knowledge-capture・compound・empirical-prompt-tuning）
- **周辺の Python:** 約 2,900 行（フラグ・状態機械・配布・整合性検査）

### 公式の根拠（2026-10-06 取得）

- [Skills](https://code.claude.com/docs/en/skills): description と `when_to_use` の合計は 1,536 字で切り詰められる。本文は 500 行未満。compaction 後は先頭 5,000 トークンだけ再添付される。`disable-model-invocation` は副作用のあるワークフロー向け。`/skill-doctor` で使用頻度とコストを測れる。`verify` / `simplify` はプロジェクトスキルだけがコミット前に自動実行される
- [Settings](https://code.claude.com/docs/en/settings): `.claude/settings.json` はプロジェクトの共有設定で、コミットして permissions・hooks・plugins を共有する。`permissions.allow` と `extraKnownMarketplaces` はフォルダの信頼後に効き、`deny` と `ask` はすぐ効く。`$schema` に schemastore の URL を入れると補完と検証が効く
- [Permissions](https://code.claude.com/docs/en/permissions): Bash の引数を制限するパターンは脆い。`Read` と `Edit` の deny は `cat`・`head`・`sed`・`tee`・リダイレクトにも効くが、名前を出さずに読む `grep -r` やスクリプト経由には効かない。OS レベルで強制するには sandbox を使い、permissions と併用する。PreToolUse hook の allow は deny / ask を上書きしない
- [Plugins](https://code.claude.com/docs/en/plugins/overview): plugin は skills・agents・hooks・MCP を同梱できる。permissions と CLAUDE.md は同梱できない
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference): 配置先で調整できるのは `userConfig` の値（`${user_config.KEY}` でスキル本文に埋め込む）まで
- [Skills](https://code.claude.com/docs/en/skills) の名前の解決と `skillOverrides`: plugin のスキルは `/plugin名:スキル名` で他のスキルと共存する。`skillOverrides` は plugin のスキルに効かず、オン・オフは `/plugin` で plugin 単位
- [公式 code-review plugin](https://github.com/anthropics/claude-code/blob/main/plugins/code-review/commands/code-review.md)
  - 適用判定 → CLAUDE.md の収集 → 要約 → 並列 4 体（規約 2・バグ 2）の流れ
  - 指摘は高確度だけにし、「指摘しないもの」を明示する
  - 指摘ごとに検証 agent を立て、確認できなかった指摘は捨てる
- [Prompting Claude Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5.md): 旧モデル向けのスキルは規定的すぎることがある。長い実行では fresh-context の検証が有効
- [Prompting Claude Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5.md): 一律の自己検証指示は過剰になる。レビューで「重大なものだけ」と書くと文字どおり報告が減る

### Cursor の互換性（2026-10-06 取得。Claude Code 専用にした根拠）

- [Agent Skills](https://cursor.com/docs/skills): `.claude/skills/` を互換として読む。`when_to_use`・`context: fork`・`allowed-tools` は記載なし
- [Subagents](https://cursor.com/docs/subagents): `.claude/agents/` を互換として読む
- [Third Party Hooks](https://cursor.com/docs/reference/third-party-hooks): `.claude/settings.json` の hook を読む。plugin の `hooks/hooks.json` の記載なし
- [Plugins](https://cursor.com/docs/plugins): Cursor が読むのは `.cursor-plugin/plugin.json` と Agent Plugins 標準（ルートの `plugin.json`）。Claude Code の `.claude-plugin/plugin.json` は記載なし
