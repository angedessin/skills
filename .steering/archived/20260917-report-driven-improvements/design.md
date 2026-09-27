# 設計: report-driven-improvements

Status: **APPROVED**
Approved: 20260919
Created: 20260917

一次情報: `reports/skill-improvement-report.md`（コスト構造レビュー・20260917）/
`reports/workflow-evaluation-20260829.md`（客観評価・総合 3.8/5.0・対象 commit `b09b247`）。
両方とも `.tmp/` は gitignore 対象のため、タスク配下に複製して正本化した。

## 目的

2 件の外部レポートが指摘した所見のうち、**再現を確認できた欠陥**と**実測を待たずに確実に効く改善**を反映する。
中心は「全静的検査 34/34 PASS のまま Critical 2 件が存在していた」という事実で、
これは個々のバグではなく**状態機械の意味的正しさを機械検査していない**という構造的な穴を示す。
したがって本タスクは「2 件を直す」ではなく「同型の欠陥が次に入ったら検査が落ちる状態にする」までを目的とする。
併せて、Claude Code が公式に持つ設定機構（skill / subagent frontmatter の `model`・`effort`・`tools`）が
このリポジトリで一切使われていないため、レポートのモデル/エフォート割当を設定として実装する。

## スコープ

### 対象

| # | 項目 | 由来 |
|---|---|---|
| 1 | `feature-pipeline` 判定表の Phase 3.7 到達不能を修正 | 評価レポート Critical 1 |
| 2 | capture の 2 段化（`pr_capture_done` を追加） | 評価レポート Critical 2 |
| 3 | `steering/references/spec.md` の tasklist テンプレを正本へ同期 | 評価レポート High 1 |
| 4 | 判定表の純粋関数化 + table-driven test + 表↔関数の同期検査 | 評価レポート High 2 / P1 |
| 5 | GitHub Actions で無料検査を実行 | 評価レポート High 4 / P1 |
| 6 | **リポジトリ内の全サブエージェント起動箇所**を `.claude/agents/` の定義に集約し、役割ごとに `model` / `effort` / 読み取り専用 `tools` を指定 | コストレポート §5・§6 + 評価レポート §5.1「レビュー agent の権限を限定していない」 |
| 6b | `passthrough_check.py` の `--model sonnet` ハードコードを可変化し、実走時のモデルを結果に記録 | 評価レポート High 3「現行モデルでの実走証跡がない」 |
| 6c | `compound` の知識走査（`docs/knowledge/` 全文 = 約 23,000 トークンの無条件読み）を読み取り専用サブエージェントへ隔離 | コストレポート §2-② |
| 7 | スキル frontmatter への `model` / `effort` 明示（単独起動時の設定） | コストレポート §5 |
| 8 | `design-doc` / `feature-pipeline` のエッジケース手順を `references/` へ分離 | コストレポート §2-③ |
| 9 | 配置先ドリフト 14 件の分類（意図的なローカル適応 / 事故）と還流方針の提示 | 評価レポート High 6 |
| 10 | 衛生改善: `biome migrate`・portability 警告 2 件・`remind-config-docs.sh` の要約ドリフト検査 | 評価レポート P3 |
| 11 | C 群（後述）の判断に必要な実測の実施と記録 | コストレポート §0・§7 |

### 対象外（BACKLOG へ「データ待ち」として節立てする）

| 項目 | 対象外の理由 |
|---|---|
| 承認ゲート再編 | 「停止が多い」は主観所見で、評価レポート自身が §5.8 / §9 で摩擦を定量していないと明記。停止契約は `passthrough_check.py` の検査対象でもあり、記録なしにゲートを削ると安全側の設計を勘で削ることになる。項目 11 の実測（どのゲートが何回止めたか）を先に取る |
| sandbox 有効化・subagent への最小権限の全面適用 | 設定の当否が実環境でしか判明せず、開発コマンドが通らなくなる副作用の検証に実走が要る。**ただしレビュー agent の読み取り専用化だけは項目 6 に含める**（新規定義ファイルなので既存動作を壊さない） |
| 配布方式の plugin 化再評価 | 移行の可否判断自体が調査タスクで、移行コストも大きい。配置先ドリフトの解消（項目 9）とは独立に進められる |
| レビュー軸の拡張（shell / Python 向けの軸追加） | **2 レポートが正面衝突する唯一の箇所**（評価レポートは「軸を足せ」、コストレポートは「7 エージェントは重いから減らせ」）。フルモード発動頻度の実測なしに決めると、どちらかの後悔が確定する |
| `review-performance` と `review-security` の統合 | 同上。加えて項目 6 で軸ごとに effort を変える設計にすると（security=high / performance=medium）、統合は effort の粒度を失う方向に働く。実測後に再評価する |
| `compound` を `context: fork` でスキルごとフォークする案（レポートの実装案そのまま） | `context: fork` はスキル単位でしか効かないため `compound-scan` の新規追加（29→30 本）になり、レポート §4 自身の結論（個数を減らすのではなく常時ロード範囲を絞る）と緊張する。また fork 先は会話履歴を見ないため、会話由来の候補を引数で渡す設計が別途必要。**目的（メイン文脈から 23k トークンを外す）は項目 6c のサブエージェント隔離で達成できる**ため、機構だけ差し替えて採用する |
| `disable-model-invocation` / `skillOverrides` によるマスター専用 5 スキルの絞り込み | コストレポート §3-7 自身が「マスターで `/skill-doctor` を回してから判断」と順序を指定している。項目 11 の実測が先 |

## 制約

- Claude Code 2.1.274（`background: false` は v2.1.218+、`CLAUDE_CODE_SUBAGENT_MODEL` の優先順位は v2.1.251 で変更済み。いずれも満たす）
- Python は標準ライブラリのみ（`scripts/` の既存方針）。新規の npm 依存を足さない
- `validate_skills.py` の構造契約を維持: SKILL.md は 500 行以下・`metadata.version` 必須・`When NOT to use` 見出し必須・アストラル面文字禁止
- スキルは自己完結（配置先に `.claude/agents/` や `scripts/` が無くても動くフォールバックを本文に書く）
- 配置先（`deployments.md` の 2 件）への書き込みは承認制。本タスクでは既定で書き込まない
- main へ直接コミットする（PR は明示要求時のみ）

## 完了条件

- [ ] `tests/state/` の table-driven test が、**修正前の判定表を入力すると FAIL する**ことを確認したうえで（欠陥の再現）、修正後に PASS する
- [ ] 到達可能性テストが「全フェーズが少なくとも 1 つの状態から到達可能」を検査し、Phase 3.7 到達不能の再発を落とす
- [ ] `pr_capture_done` と `capture_done` の producer / consumer が `check_asset_consistency.py` で双方向に突合される
- [ ] `steering/references/spec.md` の tasklist テンプレが `design-doc/references/templates.md` と同一工程順になり、両者の同期が機械検査される
- [ ] GitHub Actions で `validate` / `validate:assets` / `validate:portability` / `test:hooks` / `lint` / passthrough dry-run / `tests/state` が push・PR 時に実行され、green
- [ ] `validate:portability` の警告が 0 件
- [ ] `.claude/agents/` にレビュー 7 軸 + premortem-attacker + codebase-explorer + tournament-variant / -scorer + knowledge-scanner の計 12 本があり、各定義が `model`・`effort`・`tools` を持つ
- [ ] `compound` が `docs/knowledge/` 全文をメイン文脈に読み込まなくなる（走査はサブエージェント側で完結し、返るのは要約）
- [ ] サブエージェントを起動する全スキル（`frontend-code-review` / `impl-from-design` / `design-premortem` / `impl-tournament`）が、定義が無い環境でも現行どおり動くフォールバックを本文に持つ
- [ ] モデル / エフォートの値が SKILL.md や references の散文に残っていない（`grep -rn "Haiku 相当\|Opus 相当" .claude/skills/` が 0 件）
- [ ] `passthrough_check.py` が `--model` を引数で受け取り、実走結果に使用モデルが記録される
- [ ] `design-doc` / `feature-pipeline` の SKILL.md 本文が短くなり、分離先の `references/` が本文から参照されている
- [ ] `biome check .` の deprecated 情報が消える
- [ ] 配置先ドリフト 14 件が「意図的 / 事故 / マスター先行」に分類され、還流または再コピーの判断がユーザーに提示されている（実行は承認後）
- [ ] `/skill-doctor` の実測（マスター + 配置先）と、フルモード発動頻度の記録が `decisions.md` に残っている
- [ ] `BACKLOG.md` に C 群が「データ待ち」として節立てされている

## アプローチ

判定表の**行の意味**（条件・フェーズ名・優先順位）を `scripts/pipeline_state.py` の純粋関数へ写し、
SKILL.md の表を正本のまま残したうえで、`check_asset_consistency.py` が
「表の行集合 ≡ 関数の分岐集合」を突合する（正本二重化のリスクを同期検査で押さえる）。
状態の観測可能性が Critical 1 の遠因でもあるため、PR の状態（URL / CI / レビュー）は
会話ではなく `tasklist.md` のデプロイ節に固定キーの 3 行として記録し、判定関数の入力にする。
capture は `capture_done` の意味を「最終（マージ後）capture 完了」に固定し、PR 前の分だけを
新フラグ `pr_capture_done` で表す（consumer 5 箇所のうち意味が変わるのは 2 箇所だけで、
アーカイブのハードストップと Stop フェイルセーフは無変更のまま正しく動く）。
モデル / エフォート割当は、**役割ごとの `.claude/agents/` 定義を単一の正本**にする。
サブエージェントを起動するスキル（レビュー 7 軸・code-explorer・premortem・tournament）は
本文で役割名を指すだけにし、モデル・エフォート・ツール権限の値は定義側だけに書く
（現状 `impl-tournament/references/commands.md:35-36` のように「Haiku 相当に指定」と
散文で書かれた指示は機構を持たず、実際には何も指定されていない）。
スキル単独起動時の設定だけを SKILL.md frontmatter で補う。

## 主要コンポーネント

| 場所 | 変更内容（変更後の姿） |
|---|---|
| `.claude/skills/feature-pipeline/SKILL.md` | 判定表を差し替え。Phase 3.7 行を Phase 3.5 行**より上**に置き、条件を成果物ベースへ: 「tasklist デプロイ節の `PR: <URL>` が空でなく、かつ `Feedback: yes`」。Phase 4 行の条件を `capture_done` が無い に加え `pr_capture_done` の有無で PR 前 / 最終を書き分ける。表の各行に安定 ID（`P1`/`G1`/`P2`…）を付与し、同期検査の突合キーにする。PR 往復の詳細手順は `references/pr-phases.md` へ移す |
| `.claude/skills/feature-pipeline/references/pr-phases.md`（新規） | Phase 3.5 / 3.7 の手順本文（PR 作成 → CI 確認 → フィードバック回収 → pr-feedback 委譲 → tasklist のデプロイ節更新）。SKILL.md からは 1 行のポインタで参照 |
| `scripts/pipeline_state.py`（新規・master-only） | `resolve_phase(PipelineState) -> str` の純粋関数。入力は `design_status` / `impl_unchecked` / `review_status` / `deploy_unchecked` / `pr_url` / `pr_feedback` / `pr_capture_done` / `capture_done`。未知・欠落 Status は `HALT_UNKNOWN_STATUS` を返す（fail-closed）。表の行 ID を戻り値に含め、どの行で確定したかを検査可能にする |
| `tests/state/test_pipeline_state.py`（新規） | table-driven。(a) 各行 ID が少なくとも 1 つの入力で確定すること（到達可能性 = Critical 1 の回帰）、(b) 行の優先順位（上が勝つ）、(c) 未知 Status の fail-closed、(d) PR 前 capture 後にマージ後 capture が飛ばされないこと（Critical 2 の回帰）。`python3 tests/state/run.py` で実行（pytest 非依存・標準ライブラリのみ） |
| `scripts/check_asset_consistency.py` | 検査を 2 本追加。(11) `feature-pipeline/SKILL.md` の判定表の行 ID 集合 ≡ `pipeline_state.py` の行 ID 集合。(12) `steering/references/spec.md` の tasklist テンプレの節見出し列 ≡ `design-doc/references/templates.md` の節見出し列。現行の「フェーズ順序は検査対象外」というコメント（`:50-56`）を削除し、順序を検査対象にする。さらに (13) SKILL.md が名指しする agent 名 ⊆ `.claude/agents/` の定義名、かつ定義はいずれかのスキルから参照されている（producer / consumer の既存突合と同型） |
| `.claude/skills/knowledge-capture/SKILL.md` | Step 0 の分岐に「PR 前 capture か最終 capture か」の判定を追加（tasklist のデプロイ節にマージ済みチェックがあるか、または呼び出し元の指定で決める）。完了時のフラグ書き込みを 2 分岐にする: PR 前 → `pr_capture_done`、最終 → `capture_done`。`capture_done` 既存時の再実行案内は現行どおり |
| `.claude/skills/steering/SKILL.md` / `references/spec.md` | ディレクトリ図のフラグ一覧に `pr_capture_done` を追加（意味: PR 差分に属する知見の保存済み）。アーカイブのハードストップは `capture_done` のまま据え置き（意味が変わらないため）。spec 内の tasklist テンプレを `templates.md` と同一工程順（実装 → レビュー → 知見保存(PR分) → デプロイ → 福利化 → クローズ）に差し替える |
| `.claude/skills/design-doc/references/templates.md` | tasklist のデプロイ節に固定キー 3 行を追加: `- PR: <URL or none>` / `- CI: <green\|failing\|none>` / `- Feedback: <yes\|no>`。工程順は現行のまま（こちらが正本） |
| `scripts/deploy_skills.py` | 除外リスト（`.steering/**/capture_done` の隣）に `.steering/**/pr_capture_done` を追加。`.claude/agents/` は今回配布対象に含めない（配布は BACKLOG） |
| `.gitignore` | `.steering/**/pr_capture_done` を追加（既存のランタイムフラグ群と同じ扱い） |
| `.github/workflows/validate.yml`（新規） | `push` / `pull_request` で ubuntu-latest 上に Node 24 + pnpm 10.34.5 をセットアップし、`pnpm run validate` / `validate:assets` / `validate:portability` / `test:hooks` / `lint`、`python3 scripts/passthrough_check.py --all --dry-run`、`python3 tests/state/run.py` を実行。課金を伴う passthrough 実走は**入れない** |
| `.claude/agents/review-{security,correctness,impl,test,a11y,performance,ui}.md`（新規 7 本・master-only） | 各定義に `description` / `tools`（`Read` `Grep` `Glob` `Bash(git diff *)` のみ = 読み取り専用） / `model: sonnet` / `effort`（security・correctness・impl = `high`、test・a11y・performance・ui = `medium`） / `skills:`（対応するサブスキルをプリロード） |
| `.claude/agents/premortem-attacker.md`（新規） | `design-premortem` の攻撃役。`model: opus` / `effort: high` / `tools` は読み取り専用。**このスキルは存在意義が推論力に依存する**ため唯一「上げ方向」を既定にする役割 |
| `.claude/agents/codebase-explorer.md`（新規） | `impl-from-design` Step 1.5 の既存パターン調査。`model: haiku` / `effort: low` / `tools` は読み取り専用。プラグイン由来の `feature-dev:code-explorer` とは名前を分け、定義が無い環境では現行どおり `feature-dev:code-explorer` へフォールバックする |
| `.claude/agents/knowledge-scanner.md`（新規） | `compound` Step 1（重複確認）/ Step 4（ルール違反箇所の洗い出し）の走査役。`model: haiku` / `effort: low` / `tools` は `Read` `Grep` `Glob` のみ。返すのは候補リストと違反箇所リストの要約だけで、`docs/knowledge/` 全文（約 23,000 トークン）をメイン文脈に載せない |
| `.claude/skills/compound/SKILL.md` | Step 1 / Step 4 の走査を `knowledge-scanner` へのディスパッチに置き換える。**昇格先の判断・優先順位付け（Step 2）は本体に残す**（コストレポート §5 も high 判断が必要としている軸）。定義が無い環境では現行どおり自分で全文読みするフォールバックを残す |
| `.claude/agents/tournament-variant.md` / `tournament-scorer.md`（新規 2 本） | `impl-tournament` の変種実装（`model: sonnet` / 書き込み可）と採点（`model: opus` / `effort: high` / 読み取り専用）。現在 `references/commands.md:35-36` に散文で書かれている割当を、実際に効く定義へ移す |
| `.claude/skills/frontend-code-review/SKILL.md` | Phase 2A のディスパッチ先を「`.claude/agents/` の定義があればその subagent_type を使い、無ければ現行どおり汎用エージェントにサブスキル本文を渡す」の 2 段フォールバックにする（自己完結を維持） |
| `.claude/skills/{impl-from-design,design-premortem,impl-tournament}/SKILL.md`（+ `impl-tournament/references/commands.md`） | 起動先を役割名（agent 定義名）で指す形に統一し、モデル・エフォートの値は本文から削除する（正本は定義側）。いずれも「定義が無ければ従来どおり汎用エージェント / 自己実行」のフォールバックを本文に残す |
| `.claude/skills/empirical-prompt-tuning/SKILL.md` | **変更しないことを明記**する 1 行を足す。実行者はセッション設定を継承させるのが仕様（本番相当の挙動を測るため）で、モデル/エフォートを指定すると評価の目的が壊れる |
| `scripts/passthrough_check.py` | `AGENT_CMD:51` の `--model sonnet` 固定をやめ、`--model`（既定はセッション非依存に `sonnet` のまま）を CLI 引数で上書き可能にする。実走結果の記録に使用モデルを含める（`skill-test/references/passthrough-testing.md` の測定ログ書式も同時改訂） |
| 各 SKILL.md の frontmatter（対象を限定） | コストレポート §5 の割当のうち、**セッション設定より下げる方向の指定のみ**を入れる（`steering` / `pr-create` / `knowledge-capture` / `session-retrospective` / `adr` = `effort: medium`）。それ以外は無指定（セッション継承）にして副作用を避ける。`design-premortem` / `impl-tournament` の上げ方向は frontmatter ではなく agent 定義側で効かせる |
| `.claude/skills/design-doc/SKILL.md` | 「SPIKE レーン」節と「方針転換が起きた場合」節を `references/spike-lane.md` / `references/pivot.md` へ移し、本文にはトリガ条件 + ポインタだけ残す（287 行 → 約 210 行の見込み） |
| `.claude/skills/design-doc/references/templates.md:137` / `.claude/skills/feature-pipeline/SKILL.md:229` | portability 警告の原因である日付付き内部エピソード（`20260730`）を、配置先の読み手にも通じる一般的な理由文へ書き換える |
| `biome.json` | `linter.rules.recommended` を Biome 2.x の現行キーへ移行（`biome migrate` の出力に従う） |
| `.claude/hooks/remind-config-docs.sh` + `scripts/check_asset_consistency.py` | hook が注入する要約と `docs/knowledge/claude-code-config.md` の正本が乖離していないかの検査を追加（要約内の各見出し語が正本に存在すること） |
| `.steering/BACKLOG.md` | 「C 群（データ待ち）」の節を新設し、対象外 7 項目と、その判断に必要な実測項目を書く |

## 未解決の論点

1. **PR 状態の記録先** — `tasklist.md` のデプロイ節に固定キー 3 行を足す案を推奨（新ファイルを増やさず、既存 consumer が既に tasklist を読むため）。評価レポートは `pr-state.md` の新設を推奨しており、どちらでも判定は可能。**レビューで確定してほしい**
2. **`pipeline_state.py` の配布分類** — master-only にすると、配置先では `feature-pipeline` の判定表が機械検査されない状態が続く。配布可にすると配置先にも `scripts/` と `tests/` を送ることになり、deploy_skills.py の対象が広がる。今回は master-only を推奨（配置先での検査は plugin 化の判断と一緒に扱う）
3. **frontmatter の `effort` がセッション設定を上書きする副作用** — 公式仕様では skill の `effort` は「セッションの effort を上書き」する。ユーザーが `xhigh` で回していても該当スキル起動中は `medium` に落ちる。上の表では下げ方向の指定を 5 スキルに限定したが、**そもそも下げ方向を入れない**選択もある（実測前は無指定が安全）。判断を求める
4. **`model: sonnet` の固定 vs 無指定** — エイリアス指定はモデル世代更新に追随するが、配置先組織の `availableModels` 制限で無効化される場合がある（その場合はセッションのモデルが維持される＝安全側）。7 agents に固定値を書くか、`inherit` にして effort だけ指定するか
5. **`.claude/agents/` の配布** — 定義は 11 本になるが `deploy_skills.py` は `.claude/agents/` を配布対象にしていない。配置先では常にフォールバック経路（現行動作）になる。配布対応を本タスクに含めるか、plugin 化の判断（BACKLOG）と一緒に扱うか。**含めない案を推奨**（配置先の `.claude/agents/` を上書きする操作はリポジトリ外への書き込みで、承認と検証の粒度が別）
6. **agent 定義名の衝突回避** — `impl-from-design` は現在プラグイン由来の `feature-dev:code-explorer` を起動している。自前定義を `codebase-explorer` という別名にしてフォールバック先を `feature-dev:code-explorer` にする案を推奨するが、「同名で上書きして常に自前を使う」設計も選べる
7. **項目 9（配置先ドリフト）の扱い** — 14 件のうち 1 件は配置先にしか無いスキル（`next-dev-loop`）で、これは還流候補にもなる。「意図的なローカル適応」と「事故」の判定は最終的にユーザーの意思決定であり、本タスクでは分類と提示までを完了条件にしている。実際の再コピー / 取り込みを本タスクに含めるかは要判断
8. **【20260920 追記・実装前調査で判明】項目 6（`.claude/agents/` 12 本）が Accepted ADR `20260706-no-custom-reviewer-agent` と衝突する** — 再検討トリガー（誤編集事故の観測）は未充足で、design.md は ADR に言及していない。選択肢: (a) 新 ADR で 20260706 を supersede（`adr` スキル）した上で項目 6 を実施 / (b) 項目 6 を「事故の観測待ち」として見送り、モデル・エフォート指定の対象を agent 定義を要しない箇所（`passthrough_check.py`・`compound` の走査隔離など）に絞る / (c) 読み取り専用化だけの最小版に絞る（ADR 自身が再検討時の最小版として挙げている）。併せて項目 7（frontmatter への `effort` 追加）は `20260722-agentskills-non-adoption` の「frontmatter を 4 キーに揃える」方針との整合説明が要る

<!-- design-doc-boundary: appendix -->

## データフロー

```
[.steering/[task]/ の成果物]
   design.md(Status) ┐
   tasklist.md(実装/デプロイ節の PR・CI・Feedback) ┼─→ resolve_phase()（純粋関数・行 ID を返す）
   review-result.md(Status) ┘                     │
   pr_capture_done / capture_done ────────────────┘
                                                   ↓
                              feature-pipeline SKILL.md の判定表（正本・人が読む）
                                                   ↑
                              check_asset_consistency.py が行 ID 集合を突合
```

knowledge-capture の書き込み先が 2 系統に分かれる:

```
PR 前 capture  → docs/ への追記をブランチに含める → pr_capture_done
最終 capture   → 横断知見を保存                   → capture_done → steering archive 可
```

## 影響範囲

- **`feature-pipeline` の resume 挙動が変わる**: これまで PR 作成後は常に Phase 3.5 に留まっていたが、`Feedback: yes` を記録すると Phase 3.7 に進む。既存のアクティブタスクは無いため、移行対象のデータは存在しない（アーカイブ済みタスクは判定対象外）
- **配置先 2 件**: `knowledge-capture` / `steering` / `feature-pipeline` の契約が変わるため、再コピー時に配置先の挙動が変わる。ただし `capture_done` の意味は変えないため、**再コピーしない限り現状の動作は壊れない**（後方互換）
- **CI 追加によりリポジトリの外向き挙動が増える**: GitHub Actions は push のたびに実行される。課金実走は含めないため追加コストは Actions の無料枠内
- **リグレッション懸念**: `check_asset_consistency.py` に順序検査を足すと、既存の 10 検査が通っていた資産で新たに落ちる可能性がある（steering spec のドリフトは実際に落ちる想定 → 項目 3 で先に直す）
- `.claude/agents/` を新設すると、このリポジトリで作業する Claude 自身のエージェント一覧に 12 件が増える（`description` は subagent 選択時にのみ参照され、常時のスキル一覧とは別枠）
- **`design-premortem` と `impl-tournament` の採点が opus に固定されるため、これらの実行コストは上がる**（品質のための意図的な増加。どちらも低頻度スキルで、コストレポート §3-5 も「コスト意識の実装が優れている」と評価している箇所）
- `passthrough_check.py` のモデル可変化は、既存の測定ログ書式（`skill-test/references/passthrough-testing.md`）と `skill-test` の手順に波及する。課金実走は既定で回さないため、CI や日常フローの挙動は変わらない

## テスト方針

| 層 | 対象 | 方法 |
|---|---|---|
| 状態機械 | `resolve_phase()` | table-driven（到達可能性・優先順位・fail-closed・capture 2 段）。**修正前の表で FAIL することを先に確認**してから修正に入る（TDD Red 相当） |
| 資産契約 | 表↔関数、spec↔templates、hook 要約↔正本、SKILL.md↔agent 定義 | `check_asset_consistency.py` に検査を追加（既存 10 → 14） |
| agent 定義 | `.claude/agents/*.md` 11 本 | frontmatter の必須キー（`name` / `description` / `model` / `tools`）と、読み取り専用を意図した定義に書き込み系ツールが混ざっていないことを検査（`validate_skills.py` に agents モードを足すか、資産整合側に寄せるかは実装時に決める） |
| 構造 | SKILL.md 群 | 既存 `validate_skills.py`（500 行・必須見出し・アストラル面文字）。frontmatter に `model` / `effort` を足しても既存検査は通る（必須キーのみ検査する実装であることを確認済み） |
| 実行 | 停止契約 | `passthrough_check.py` は dry-run のみ CI に載せる。課金実走は任意（既定では回さない） |
| 移植性 | 配布可スキル | `validate:portability` を CI で strict 相当に扱い、警告 0 を維持 |

## 検討した代替案

- **C 案（レポート全項目を一括）** — 承認ゲート再編・sandbox・plugin 化・レビュー軸拡張を含める案。却下理由は、これら 4 項目が「判断材料が未収集」または「実環境検証が必要」で、今 design.md に書くと決定ではなく推測になるため。代わりに項目 11 で判断材料を取り、BACKLOG に節立てして追跡する
- **A 案（P0 のみ）** — 状態機械だけを直す最小案。却下理由は、CI と衛生改善が「同じセッション内で片付く無料の改善」であり、分割するとタスク管理コストの方が高くつくため
- **判定表をドキュメント修正だけで直す** — 却下理由は、レポートが指摘した本質が「キーワード共存検査は空文でも通る」という検査方式の限界であり、同型の欠陥が再発するため
- **`pipeline_state.py` を単一正本にして SKILL.md の表を生成物にする** — 正本二重化を原理的に消せるが、SKILL.md を手で直せなくなり生成スクリプトが新たな保守対象になる。同期検査で足りると判断
- **capture フラグを `pr_knowledge_captured` / `session_knowledge_captured` に全面置換**（評価レポートの提案） — 命名は対称になるが、consumer 5 箇所すべてと配置先 2 件の移行（旧フラグの後方互換読み）が必要になる。`capture_done` の意味を保つ追加 1 本の方が変更面積が小さい
- **`CLAUDE_CODE_SUBAGENT_MODEL` でサブエージェントの既定を haiku にする**（コストレポート §6） — 公式仕様上、この環境変数は**組み込みの Explore / Plan subagent には効かない**ため、レポートが主目的に挙げた `impl-from-design` の code-explorer には届かない。個別定義（`.claude/agents/`）で指定する方が確実なので採用しない

## 調査結果（レポート所見の独立検証）

| レポートの主張 | 判定 | 根拠 |
|---|---|---|
| Critical 1: Phase 3.7 到達不能 | **再現** | `feature-pipeline/SKILL.md:70-89` が「上から順・最初にマッチで確定」。デプロイ節は `PR作成 / CI / マージ` の 3 項目（`templates.md:141-146`）で、マージ前は必ず未チェックが残る |
| Critical 2: 単一 `capture_done` | **再現** | tasklist は 2 段（`templates.md:135-160`）だが `knowledge-capture/SKILL.md:253` は常に `capture_done` を作り、pipeline は `capture_done` あり → Phase 5 |
| High: steering spec のドリフト | **再現** | `spec.md:99-123` に「知見保存(PR分)」節が無く、順序も デプロイ → 福利化 → 知見保存 |
| 静的検査は全 PASS | **再現** | `validate` 34/34・`validate:assets` 10/10・`test:hooks` 35/35・portability 警告 2 件・`check_deploy_drift.py` exit 1（ドリフト 14 / 配置先 2） |
| `biome.json` の deprecated | **再現** | `biome check .` が `biome migrate` を案内する info を 1 件出力 |

### コスト構造の実測（2026-09-17・日本語 1 トークン ≈ 1.3 文字での概算）

| 測定対象 | 実測 | 概算トークン | 性質 |
|---|---|---|---|
| 29 スキルの `description` 合計 | 7,672 文字 | 約 5,900 | **常時ロードの固定費**（キャッシュ対象） |
| うちマスター専用 6 本 | 1,779 文字（23%） | 約 1,400 | `disable-model-invocation` / `skillOverrides` で削減しうる上限 |
| `docs/knowledge/` 全文 | 847 行 / 30,515 文字 | 約 23,000 | `compound` 実行時にメイン文脈へ載る（項目 6c で隔離） |
| review-security + review-performance の本文 | 6,279 文字 | 約 4,800 | 統合案の削減対象。ただし主成分は本文ではなく各エージェントの diff 読み |

この実測から導いた判断:

- SKILL.md 本文は**起動時のみ**ロードされ、常時費は `description` だけである（公式: "skill descriptions are loaded into context so Claude knows what's available, but full skill content only loads when invoked"）。コストレポート §2-③ の「毎回のロード時に払っている」は常時費ではなく起動時費の意。参照分離の推奨自体は有効なので結論は変えない
- 統合案（§2-①）の削減上限はフルモード 1 回あたり約 1/7。effort 差別化（security=high / performance=medium）と相殺するため、発動頻度の実測が必要（対象外の理由）
- `compound` の 23,000 トークンは実測で最大の単一項目であり、**隔離の効果はレポートの指摘どおり明確**（項目 6c で採用）

### サブエージェント起動箇所の棚卸し（grep で確認した実体）

| 箇所 | 現状の指定 | 本タスクでの扱い |
|---|---|---|
| `frontend-code-review` Phase 2A（7 軸並列） | なし | agent 定義 7 本（読み取り専用・軸ごとの effort） |
| `impl-from-design:66-77` Step 1.5 | `feature-dev:code-explorer` を起動（モデル指定なし） | `codebase-explorer`（haiku / low）を定義し、無ければ従来へフォールバック |
| `design-premortem:37` | 「フレッシュな subagent」とだけ記載 | `premortem-attacker`（opus / high） |
| `impl-tournament/references/commands.md:35-36` | 「Haiku 相当に指定」「Opus 相当に」と**散文のみ・機構なし** | `tournament-variant` / `tournament-scorer` の定義へ移す |
| `compound` Step 1 / Step 4 | 起動なし（メイン文脈で `docs/knowledge/` 全文読み） | `knowledge-scanner`（haiku / low / 読み取り専用）へ隔離 |
| `debug:19` | ビルトイン Explore / code-explorer への委譲案内 | 変更なし（委譲先の案内であり起動箇所ではない） |
| `empirical-prompt-tuning` の実行者 | なし | **意図的に指定しない**ことを本文に明記 |
| `scripts/passthrough_check.py:51` | `--model sonnet` をハードコード | CLI 引数化し、実走記録に使用モデルを残す |

### 公式仕様の裏取り（2026-09-17 時点）

| レポートの前提 | 公式の記述 | 設計への影響 |
|---|---|---|
| `disable-model-invocation` | 実在。`true` で説明文がコンテキストに載らなくなり、subagent へのプリロードと scheduled task での起動も止まる | 採用は実測後（対象外）。`skillOverrides` の `name-only`（名前だけ残す）/ `user-invocable-only` という設定側の中間手段もあるため、レポートの「自然文発動を完全に失う」は不正確 |
| `context: fork` | 実在。フォーク先は**会話履歴を見ない**。`agent` で subagent 種別、`model` でモデルを指定。`background: false` は v2.1.218+ | `compound` の一部ステップだけを fork する案は、新規スキル追加が前提になる（対象外の理由） |
| `model` / `effort`（skill frontmatter） | 実在。どちらも**現在のターンのセッション設定を上書き**する | 下げ方向の指定は副作用があるため対象を限定（未解決の論点 3） |
| `.claude/agents/*.md` の frontmatter | `tools` / `disallowedTools` / `model` / `effort` / `permissionMode` / `skills`（プリロード） 等が実在 | レビュー 7 軸の model・effort・読み取り専用化を**ここで**指定するのが実効経路。2 レポートの要求（軸ごとの effort / 最小権限）が同じ場所で同時に満たせる |
| `CLAUDE_CODE_SUBAGENT_MODEL` | 実在。ただし単体では組み込みの Explore / Plan subagent のモデルを変えない。v2.1.251 で優先順位が変更 | 既定 haiku 化は採用しない（代替案参照） |

出典: [Extend Claude with skills](https://code.claude.com/docs/en/skills) / [Create custom subagents](https://code.claude.com/docs/en/sub-agents) / [All settings](https://code.claude.com/docs/en/settings-reference)

### 既存パターン調査（20260920・code-explorer / Read・Grep・Glob のみで実施、スクリプトは未実行）

**設計と衝突する発見（原本を再確認済み）**
- `docs/decisions/20260706-no-custom-reviewer-agent.md`（Accepted）: レビュー用のカスタム agent 定義を導入しないと決定済み。再検討トリガーは「レビュー agent がコードを誤編集した事故を実際に観測したとき」で、本タスクは満たしていない。却下理由（隠れ依存・`subagent_type` 語彙の本文流入・haiku 化の精度低下）のうち、`sonnet` 固定・2 段フォールバック・非配布は回答済みだが、本文への語彙流入は未回答。design.md はこの ADR に言及していない。
- `docs/decisions/20260722-agentskills-non-adoption.md`: 全スキルの frontmatter を `name` / `description` / `compatibility` / `metadata` に揃える方針（可搬性）。項目 7（`effort` / `model` の frontmatter 追加）はこの揃いを崩す。

**規約（確認済み）**
- `check_asset_consistency.py`: 検査は数字でなく英小文字 `contract_a..l`（g・i は除去済みで再利用しない）。新規は `contract_m/n/o` を `contract_l` の後・`main` の前に追加。戻り値は `(PASS|FAIL, details[])`、正規表現が 0 件ヒットなら FAIL（フェイルクローズ）。README:222 の `(x) ` 箇条と `contract_k` が集合一致を検査するため、新検査は README:222・docstring と同一コミットで更新する。`package.json` の scripts を足す場合も README:221 が突合対象。`:53-55` の「順序は検査対象外」は契約 (l) についての記述で、(12) の節見出し順とは別対象。README:222 に同趣旨の記述あり。
- `validate_skills.py`: 引数は手書き分岐（`KNOWN_FLAGS` への追加が要る）。`--portability` は常に exit 0 のため CI の「警告 0 件」は終了コードで判定できない（strict フラグ新設か出力判定が要る）。既定走査の `total = len(dirs) + 5` は追加検査数のハードコード。frontmatter は `metadata:` 直後に `  version:` が続く形を維持する。キー共存検査は SKILL.md 本文だけを見る（`feature-pipeline` の `APPROVED 追認` / `Gate 1` / `必須警告`、`knowledge-capture` の三択語彙、`steering` の `知見なしでアーカイブ` 等）ため、`references/` へ分離する際は本文に残す。
- 「除外リスト」は `deploy_skills.py:47-53` の `GITIGNORE_LINES`（配置先 .gitignore への追記行）で、コピー除外ではない。**「4 行」は `deploy_skills.py:18,310` / `docs/user-guide.md:81` / `validate_skills.py:250`（`KNOWLEDGE_FRESHNESS_CHECKS`）に連動**。`pr_capture_done` を足すなら 5 行に直して同一コミットで揃える。
- `passthrough_check.py`: `AGENT_CMD:51`。引数は `sys.argv` 手処理で、`--model` は `--runs` と同じ位置（:221 の後・:223 の前）で `del` しないと位置引数扱いになる。測定ログはスクリプト内に無く標準出力のみ（「記録」を標準出力止まりにするかログ表への手書きにするかは未定）。
- テスト: `tests/hooks/run_fixtures.py` が規約（`CASES` の table-driven・`PASS/FAIL id: label`・`N/M passed`・exit 0/1・`ROOT=parents[2]`）。pytest は無く、`__pycache__` に cpython-39 があるため `from __future__ import annotations` を付け `match` 文等は避ける。
- 判定表: 2 列・行 ID なし・11 行。Phase 3.7 行（:85）は 3.5 行（:84）の後にあり到達不能（Critical 1 を表の構造から確認）。`capture_done` の consumer は 6 ファイル 17 箇所（design の「5 箇所」より多い。docs/README を含めると 8 ファイル）。
- tasklist テンプレ: 正本 `templates.md:114-162` は 6 節（実装 / レビュー / 知見保存(PR分) / デプロイ / 福利化 / クローズ）、`spec.md:90-124` は 5 節で順序も異なる（デプロイ → 福利化 → 知見保存・クローズ節なし）。`validate_skills.py` に既存の「tasklist 工程表同期」検査があり、(12) と概念が重なる（対象ファイルが違う）。
- `.claude/agents/` は存在しない。`.github/` も存在しない。プラグイン由来定義の書式は `tools` カンマ区切り・`model`・`effort`。`tools: Bash(git diff *)` の書式と `skills:` プリロードは環境内に実例が無く、**公式 docs での裏取りが未了**。
- `(13)` の agent 名照合: `review-security` 等は既存スキル名と同名で、スキル名の語一致方式では区別できない。`review-impl` / `review-test` は既存スキル `impl-review` / `test-review` と語順が逆。frontend-code-review 本文の agent 名は `test-agent` 形式で、定義名とのマッピングが要る。
- `.claude/hooks/validate-skill-edit.sh` の assets モードは `.claude/agents/*.md` や `scripts/pipeline_state.py` の編集では起動しない（手で `pnpm run validate:assets` を回す）。

## 決定の記録（Phase 1.5 の回答）

| 質問 | 回答 | 反映先 |
|---|---|---|
| スコープ | B+（P0 + 無料の確実な改善 + 可逆な衛生/ドリフト分類） | 「スコープ」節 |
| 状態機械の守り方 | A（純粋関数 + table-driven test + 表↔関数の同期検査） | 項目 4・主要コンポーネント |
| capture フラグ | B（`pr_capture_done` を 1 つ追加し `capture_done` の意味は据え置き） | 項目 2・主要コンポーネント |
| rule-audit 月次ナッジ | 「後で」（マーカー不変） | 本タスクでは実施しない |
