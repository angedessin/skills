# AI Skills — フロントエンド開発ワークフロー

個人用の Claude Code スキルセット。React / TypeScript プロジェクトにおける設計から実装・レビュー・ナレッジ保存までを一貫したワークフローとして定義している。

**スタック**: React / TypeScript / Vitest / React Testing Library / MSW / Playwright

各スキルの詳細手順は `.claude/skills/[name]/SKILL.md` が一次情報。この README は全体像のみを示す。

---

## ドキュメントの読み分け

| あなたは | 読むもの |
|---|---|
| スキルを**使う**人（このリポジトリ・配置先どちらでも） | [docs/user-guide.md](docs/user-guide.md) — チートシート（言うフレーズ全表）・FAQ・使うときのコツ |
| スキルを他プロジェクトへ**配置する**人 | [docs/starter-kit.md](docs/starter-kit.md) — 推奨構成・配置手順 8 ステップ・CLAUDE.md 雛形 |
| マスターを**保守する**人・全体像を知りたい人 | この README（ワークフロー図・スキル一覧・自己改善ループ・インフラ） |

最低限の抜粋（一次情報は user-guide のチートシート）: 新機能は「X を作りたい」（仕様書があれば貼る）、バグは「調べて」、タスク再開は「[タスク名] を再開」、完了は「[タスク名] をアーカイブして」。残りのスキルは自動発動かメンテ用で、覚えなくてよい。

---

## ディレクトリ構成

```
.
├── CLAUDE.md                          # 行動ルール（Claude の設定）
├── .claude/
│   ├── settings.json                  # パーミッション・フック設定
│   ├── hooks/
│   │   ├── session-start-check.sh     # 開始時に未処理フラグ・rule-audit 月次ナッジ・アクティブタスクを context へ注入
│   │   ├── session-stop.sh            # セッション終了時に .capture-needed フラグを作成
│   │   ├── guard-env-read.sh          # .env 系に触れる Bash を ask に落とす（全文検査）
│   │   ├── guard-gated-write.sh       # 承認制パスへの Bash 経由の書き込みを ask に落とす
│   │   ├── guard-gated-delete.sh      # 承認制パスへの素の rm/mv を deny する
│   │   ├── post-edit-lint.sh          # 編集ごとの lint 差し戻し（フェイルオープン）
│   │   ├── stop-typecheck.sh          # 終了宣言時の tsc（フェイルオープン）
│   │   ├── remind-config-docs.sh      # 設定/スキル編集時に該当知識の要点を注入（master-only）
│   │   └── validate-skill-edit.sh     # SKILL.md 等の編集時に検証を自動実行（master-only）
│   └── skills/                        # スキル定義（下の一覧を参照）
├── .steering/                         # クロスセッション コンテキスト（複数セッションタスクのみ）
├── deployments.example.md             # 配置先レジストリの雛形（追跡。実体 deployments.md は .gitignore＝ローカル限定）
├── scripts/
│   ├── validate_skills.py             # スキル frontmatter・構造の機械検証（マスター専用）
│   ├── passthrough_check.py           # 素通り検査（ハードストップの実地検証・課金・任意）
│   ├── deploy_skills.py               # 配置先へのスキル・ガードレール同送（skill-deploy が使う）
│   ├── check_deploy_drift.py          # 配置先ドリフト検出・issues 還流（読み取り専用）
│   └── check_asset_consistency.py     # 資産どうしの契約突合（片側修正の検出・違反で exit 1）
├── prompts/                           # 人が貼って使うマスター専用プロンプト（非配布）
│   └── adversarial-skill-review.md    # スキル本文の敵対的レビュー（横断／個別の二層）
├── templates/                         # スキル作成用メタ雛形（SKILL.template.md・README.md）
├── tests/
│   └── passthrough/[skill]/scenario.md # 素通り検査のシナリオ資産（マスター専用）
└── docs/
    ├── user-guide.md                  # スキルを使う人向けガイド（チートシート・FAQ。配布可）
    ├── starter-kit.md                 # 他プロジェクトへの配置手順・推奨構成
    ├── knowledge/                     # 経験・パターン集
    └── decisions/                     # ADR（設計判断・adr スキルが起票）
```

---

## メインワークフロー

```
[0] 入口分岐      新機能 → design-doc ／ バグ・障害 → debug
                  （小さい修正は即修正で完結、構造に触る修正は design-doc に接続）
      ↓
[1] 設計          design-doc（.steering/ は複数セッションタスクのみ作成。feature-pipeline 配下では常に作成）
      ↓           （任意）design-premortem — 人間レビュー前に敵対的レビューで設計の穴出し
      │           （任意）SPIKE — 破棄前提の短い探索実装（ローカルのみ・PR 不可）。学びは decisions。本実装は DRAFT に戻してから承認
[2] レビュー      人間がレビュー・承認（design.md: DRAFT → APPROVED）
      ↓
[3] 実装          impl-from-design（APPROVED または SPIKE）  ←→  tdd ／ クリティカルパスは e2e
      ↓           （任意）impl-tournament — リスクの高いアプローチ選択で N 並列実装を比較
[4] コードレビュー  frontend-code-review（フル: 7エージェント並列 / 軽量: 直列）
      ↓
[5] 指摘修正      修正 → 指摘があった軸のみ差分再レビュー
      ↓
[5.5] 知見（PR分） knowledge-capture — **この変更の説明・落とし穴は同じブランチへ**（後続 PR に混ぜない）
      ↓
[6] PR 提出       pr-create → CI 確認（**マージはしない**）
      ↓
[6.5] PR 往復     pr-feedback — 返ってきたコメント・CI 失敗をトリアージ → 修正 → 返信
      ↓
[6.9] マージ      人間の判断（外向き操作）
      ↓
[7] 知見（残り）  knowledge-capture（会話由来・横断の残り）／ session-retrospective — セッション摩擦を skill-issues.md に採掘
      ↓
[8] 福利化        compound（パターン → ルール・知識・スキル改善）
      ↓
[9] アーカイブ    steering archive

定期（フェーズ外）: rule-audit — ルールの削除テスト・統合・GC ／ security-audit — セットアップ資産のセキュリティ監査（サードパーティ採用前・定期）
マスター保守（フェーズ外）: skill-test — スキルの回帰テスト ／ skill-harvest — 配置先からの還流
```

フェーズ全体を一括で進めたい場合は `feature-pipeline` が上記スキルを順に編成する（人間の承認ゲートは「不可逆/外向き・価値判断・責任」に該当する 4 点のみ: 設計承認・指摘トリアージ・マージ・知見保存。該当しない境界（実装→レビュー等）は報告して自動で進む・途中フェーズから再開可）。

**運用ルール**: このワークフロー図と `feature-pipeline` スキルは同一コミットで改訂する（図とオーケストレーターのドリフト防止）。

### スキル間の関係図

```
debug（障害調査。小さい修正は即完結）─┐
                                      ↓
design-doc ──→ impl-from-design ──→ frontend-code-review ──→ pr-create ──→ pr-feedback ──→ compound ＋ knowledge-capture
    │  ↑           │  ↑                     │                              (PR 往復)              ↕
    ↓  │(任意)     ├─←→ tdd                 ↓                                                rule-audit
steering │         └─── e2e     test-review / impl-review / review-*                       （剪定の対・定期）
（ライフ）│         │(任意)      （テスト / 実装 / sec・perf・a11y・correctness・ui）
design-premortem   impl-tournament                          session-retrospective → skill-issues.md → compound
（設計の穴出し）    （N 並列実装の比較）                     （セッション摩擦の採掘）
```

- `empirical-prompt-tuning` は上記スキル自体の品質改善に横断的に使う
- マスター専用: `skill-test`（回帰テスト）/ `skill-deploy`（新規・追加配置）/ `skill-harvest`（配置先の還流）は配布せずマスターで保守に使う

---

## スキル一覧

### オーケストレーション

| スキル | 役割 |
|---|---|
| [`feature-pipeline`](.claude/skills/feature-pipeline/SKILL.md) | メインワークフローを一気通貫で回すエンドツーエンドのオーケストレーター。既存スキル（design-doc → impl-from-design → frontend-code-review → pr-create → knowledge-capture / compound）を順に呼び出し、主要な判断点（設計承認・指摘トリアージ・マージ・知見保存）で人間の承認ゲートを挟む。`.steering/[task]/` の成果物から現在地を検出して途中フェーズから再開できる |

### 設計・コンテキスト管理

| スキル | 役割 |
|---|---|
| [`design-doc`](.claude/skills/design-doc/SKILL.md) | タスク開始時に design.md（目的/スコープ/完了条件 + 設計）と tasklist.md を作成。**DRAFT は人間の承認まで実装しない**。SPIKE はローカル探索可（外向き不可）。1セッションで終わるタスクには .steering を作らない |
| [`debug`](.claude/skills/debug/SKILL.md) | 障害調査。再現 → 仮説 → 切り分け → 根本原因 → 修正方針。小さい修正（影響が閉じる・巻き戻し容易・テストで再発防止可）は承認を得て即修正、構造に触る修正は design-doc に接続 |
| [`steering`](.claude/skills/steering/SKILL.md) | `.steering/` のライフサイクル管理（init / resume / status / archive）。ファイル仕様は [references/spec.md](.claude/skills/steering/references/spec.md) |
| [`design-premortem`](.claude/skills/design-premortem/SKILL.md) | 人間レビュー前の敵対的レビュー。エッジケース・状態複雑化・テスト容易性・スコープ・「3ヶ月後に後悔する理由」の6観点で design.md を攻撃し `## プレモータム所見` に反映。**設計は承認しない**（任意・design-doc の Phase 2.5） |

### 実装

| スキル | 役割 |
|---|---|
| [`impl-from-design`](.claude/skills/impl-from-design/SKILL.md) | APPROVED または SPIKE な design.md から実装（SPIKE はローカルのみ・外向き禁止）。code-explorer による既存パターン調査 → TDD モード（推奨）/ Impl-first モードを選択。設計と乖離したら止まって報告 |
| [`tdd`](.claude/skills/tdd/SKILL.md) | Red → Green → Refactor サイクルの単独ユーティリティ。テストパターン集は [references/patterns.md](.claude/skills/tdd/references/patterns.md) |
| [`e2e`](.claude/skills/e2e/SKILL.md) | E2E テストの作成・レビュー。クリティカルパス選定・1テスト1シナリオ・安定性原則（flaky 防止）・実ユーザー視点の4判断軸。Playwright 具体例は [references/patterns.md](.claude/skills/e2e/references/patterns.md)（カートリッジ — 配置先で再生成） |
| [`impl-tournament`](.claude/skills/impl-tournament/SKILL.md) | リスクの高いアプローチ選択で、APPROVED な design.md から2〜3の異なる実装を worktree 並列で作り採点して人間が勝者を選ぶ（SPIKE 不可）。**開始前にコスト見積 + 無料代替の承認必須**。常用しない（任意）。worktree コマンド・モデル振り分けは [references/commands.md](.claude/skills/impl-tournament/references/commands.md) |

### コードレビュー

| スキル | 役割 |
|---|---|
| [`frontend-code-review`](.claude/skills/frontend-code-review/SKILL.md) | オーケストレーター。コミット済み + 未コミットの diff をトリアージし、ロジック/コンポーネント変更はフルモード（7エージェント並列）、リファクタ/スタイルのみは軽量モード（直列。CSS 変更を含む場合は review-ui も実行）。結果を `review-result.md` に記録し、修正後は指摘があった軸のみ差分再レビュー |
| [`test-review`](.claude/skills/test-review/SKILL.md) | テストコード品質。実装エコー・アサーション品質・ネットワークモック境界・クエリ優先順位・カバレッジ意図の5軸 |
| [`impl-review`](.claude/skills/impl-review/SKILL.md) | 実装コード品質。設計整合性・プロジェクト規約・TypeScript・React の4軸（a11y は review-a11y の単独担当） |
| [`review-security`](.claude/skills/review-security/SKILL.md) | XSS・型安全・env var・依存関係の4軸 |
| [`review-performance`](.claude/skills/review-performance/SKILL.md) | Bundle サイズ・再レンダリング・CWV の3軸 |
| [`review-a11y`](.claude/skills/review-a11y/SKILL.md) | セマンティクス・ARIA・フォーカス管理・キーボード操作の4軸 |
| [`review-correctness`](.claude/skills/review-correctness/SKILL.md) | ロジック正当性。境界条件・null/undefined・非同期レース/stale closure・状態遷移/エラー握りつぶしの4軸 |
| [`review-ui`](.claude/skills/review-ui/SKILL.md) | UI 品質。レイアウト・レスポンシブ / デザイン整合（トークンは references をカートリッジとして配置先で再生成） / UX 状態網羅（loading・error・empty・disabled）の3軸 |

### 統合

| スキル | 役割 |
|---|---|
| [`pr-create`](.claude/skills/pr-create/SKILL.md) | 変更を PR として提出。コミット状態の確認 → デフォルトブランチ直を避けるブランチ作成 → 差分からタイトル/本文作成 → **プッシュ/PR 作成前に明示承認**（外向き操作）→ CI 追跡。**マージはしない**（人間の判断）。具体コマンドは [references/commands.md](.claude/skills/pr-create/references/commands.md)（カートリッジ — 別ホストは差し替え）。リモート/PR ホストが無ければ案内して停止 |
| [`pr-feedback`](.claude/skills/pr-feedback/SKILL.md) | 提出済み PR の往復。レビューコメント・CI 失敗を収集 → must-fix/要議論/nit にトリアージ → **対応計画の承認** → 修正 → 指摘軸のみ差分再レビュー → **返信/プッシュ前の承認**（外向き操作）。具体コマンドは [references/commands.md](.claude/skills/pr-feedback/references/commands.md)（カートリッジ — 別ホストは差し替え） |

### ナレッジ管理・自己改善

| スキル | 役割 |
|---|---|
| [`compound`](.claude/skills/compound/SKILL.md) | 福利化。review-result.md / decisions.md / skill-issues.md からパターンを抽出し、ルール・知識・スキル改善に昇格。codify-log.md と突合して**昇格済みルールの効果検証**（再発検知）も行う。昇格の適用は承認制（昇格ゼロ時のフラグ整理のみ承認不要） |
| [`rule-audit`](.claude/skills/rule-audit/SKILL.md) | 剪定。CLAUDE.md・ルール・docs/knowledge/・スキル frontmatter を定期監査し、削除テスト・症状診断・鮮度シグナル（最終更新日・被参照数）で**保持/削除/統合/移動/明確化**を判定。compound（追加）と対をなす。適用は承認制 |
| [`knowledge-capture`](.claude/skills/knowledge-capture/SKILL.md) | セッションの知見を docs/knowledge/（パターン）・`.steering/[task]/decisions.md`（決定）・CLAUDE.md（行動ルール）に振り分けて保存。決定は「決定・理由・却下案」までを扱い**定型フォーマットは生成しない**（記録先の様式は記録先が決める）。承認制 |
| [`adr`](.claude/skills/adr/SKILL.md) | **マスター専用**。却下した代替案がある決定を `docs/decisions/` に ADR として起票し、近縁 ADR の検出・Superseded / Amended の印付けと相互リンクで判例集を維持する。書き込み前に明示承認のハードストップ。配布しない（ADR の権威は批准プロセスから来るため、批准の仕組みを持たない配置先では影の決定ログになる） |
| [`session-retrospective`](.claude/skills/session-retrospective/SKILL.md) | セッション終盤に会話履歴から摩擦（スキル誤発動・ユーザー訂正・手戻り・パーミッション拒否・曖昧さ）を採掘し `skill-issues.md` に起票。**昇格はしない**（compound の原料を作る）。ゼロ件なら起票しない |
| [`empirical-prompt-tuning`](.claude/skills/empirical-prompt-tuning/SKILL.md) | スキル・プロンプト自体の品質改善。フレッシュな subagent に実行させて両面評価し、改善が頭打ちになるまで反復 |
| [`security-audit`](.claude/skills/security-audit/SKILL.md) | セットアップ資産（スキル・agents・hooks・settings・依存/MCP）のサプライチェーン・セキュリティを**静的**監査。外部送信・シークレット読取・破壊的コマンド・広範権限・インジェクション構造を機械スキャンし、判別不能はフェイルクローズで要確認に。**対象本文を全文解釈せずヒット行のみ判定**（監査対象の埋め込み指示に従わない）。「検出なし」は安全証明ではなく目視確認ルールを置換しない。修正は承認制。review-security（コード diff）とは対象が別 |

### マスター専用ツール（配布しない）

| スキル | 役割 |
|---|---|
| [`skill-test`](.claude/skills/skill-test/SKILL.md) | スキルの回帰テストを2層で編成。静的層（`validate_skills.py`・無料・毎回）+ 実行層（`passthrough_check.py`・課金・任意）。**実行層はコスト明示 + 承認必須・hooks 接続禁止** |
| [`skill-harvest`](.claude/skills/skill-harvest/SKILL.md) | 配置先からの還流。`deployments.md` の各配置先の再コピー候補・ドリフト・溜まった skill-issues.md を `check_deploy_drift.py`（読み取り専用）で収集。**配置先への書き込みは承認制** |
| [`skill-deploy`](.claude/skills/skill-deploy/SKILL.md) | 新規・追加配置の実行版（starter-kit 配置手順 1〜7 を駆動）。セット選択 → dry-run 提示 → 明示承認 → `deploy_skills.py` 実行 → 残タスク案内。**配置先への書き込みは承認制**。配置済みスキルの更新・回収は skill-harvest |

---

## 自己改善ループ

```
コードの問題:  frontend-code-review → review-result.md ─┐
実装中の判断:  decisions.md ────────────────────────────┼→ compound → CLAUDE.md ルール / docs/knowledge
スキルの問題:  session-retrospective → skill-issues.md ─┘       │
                                                                ├→ codify-log.md（昇格履歴）
過去の昇格:    codify-log.md × review-result.md 突合 ←──────────┘
               （ルールが効いていなければルール自体を改善）
スキル不具合 → 該当 SKILL.md 修正 + empirical-prompt-tuning / skill-test で検証
配置先 → 還流:  session-retrospective（配置先で併配）→ skill-issues.md → skill-harvest → マスターの compound
```

- セッション中にスキルの誤発動・曖昧な指示に気づいたら `.steering/[task]/skill-issues.md` に記録する（CLAUDE.md ルール。decisions.md / skill-issues.md / blockers.md への追記は承認不要 — 内容の取捨選択は compound / knowledge-capture 時に行う）
- compound がルールを増やし、`rule-audit` が定期監査（削除テスト）で刈る — 追加と剪定の両輪で CLAUDE.md の肥大化を構造的に抑える。SessionStart は `.claude/skills/rule-audit/SKILL.md` があるとき、最終実施から 30 日以上（または未実施）なら【rule-audit 月次】ナッジを注入する（操作定義は hook 注入文。スキップは `.steering/.last-rule-audit` 更新による 30 日再ナッジ）
- Stop hook が knowledge-capture 未実行タスクに `.capture-needed` フラグを作成し、次セッション開始時に「今 / 後で / スキップ」でリマインドされる（スキップは次の Stop までの催促解除。アーカイブ前は `capture_done` または「知見なしでアーカイブ」が要る）
- frontend-code-review 完了時、および knowledge-capture 完了時（`codify-log.md` が無ければ）に `.codify-needed` フラグが作成され、compound への引き継ぎになる（producer 二重化）

---

## インフラ・設定

- **SessionStart Hook** (`.claude/hooks/session-start-check.sh`): `.steering/` を走査し、未処理フラグ（`.capture-needed` / `.codify-needed`）とアクティブタスク一覧を context に注入する。`.capture-needed` 時は対象タスクごとの「今 / 後で / スキップ」確認を促す（**操作定義はこの注入文**。CLAUDE.md 再掲は任意。スキップ効果は次の Stop まで）。`.claude/skills/rule-audit/SKILL.md` があるとき、最終実施から 30 日以上（または未実施）なら【rule-audit 月次】の「今 / 後で / スキップ」も注入する（操作定義はこの注入文。スキップは `.steering/.last-rule-audit` 更新による 30 日再ナッジ。capture の次 Stop 寿命とは別）。フラグの**読む側** — これが無いと Stop hook が立てたフラグは誰にも拾われない。加えて **`.steering/BACKLOG.md`（固定パスの着手前バックログ）の存在と節数を 1 行注入する** — バックログをアーカイブ済みタスクの `decisions.md` に書くと走査が `archived/` を除外するため次セッションから見えず、アクティブタスクとして置くと毎セッションの固定費になる。その中間として「存在と規模だけ」を知らせる（中身は必要になってから読む）。`.steering/` が無い環境ではフェイルオープン（jq 非依存）
- **Stop Hook** (`.claude/hooks/session-stop.sh`): アクティブタスクに `capture_done` がなければ `.capture-needed` フラグを作成するだけの軽量フック（セッション記録は git が持つ）。成果物（*.md）の無いタスク・作りたて（design/tasklist のみかつ未チェック）はスキップする。スキップでフラグを消しても `capture_done` が無ければ次の Stop で再立てする
- **PreToolUse Guard** (`.claude/hooks/guard-env-read.sh`): Bash コマンド全文を検査し、`.env` 系に触れるものを ask に落とす（deny の前置一致では防げない head/sed/base64 等の迂回対策）。jq 非依存
- **承認ゲートの Bash 側（書き込み）** (`.claude/hooks/guard-gated-write.sh`): `CLAUDE.md` / `docs/knowledge/` / `docs/decisions/` への **Bash 経由**の書き込み（`>` / `>>` / `tee`）を ask に落とす。permissions の ask は **Edit ツールにしか掛からず**、`Bash(git show*)` のような前置一致 allow があると `git show HEAD:x > CLAUDE.md` で迂回できるため、その穴を塞ぐ
- **承認ゲートの Bash 側（削除・移動）** (`.claude/hooks/guard-gated-delete.sh`): 同パスへの **素の `rm` / `mv`** を **deny** する（`tool_input.command` を python3 で構造抽出。失敗・複合シェル・`git rm` / `/bin/rm` は沈黙＝完全封鎖ではない）。permissions の粗い `rm -rf *` 等は別層として維持。検証: `mise exec -- pnpm run test:hooks`
- **知識の要点注入** (`.claude/hooks/remind-config-docs.sh`, **master-only**): `.claude/settings.json` / `.claude/hooks/` / `SKILL.md` を編集したとき、対応する `docs/knowledge/` の要点を**本文ごと** context に注入する（セッション 1 回だけ）。「読め」というポインタを増やしても読まれなかった実測があるため、要点そのものを渡す方式にしている。注入する本文がマスターの `docs/knowledge/` に依存するため配置先には同送しない
- **検証スクリプト** (`scripts/validate_skills.py`): name 一致・description・行数・アストラル面絵文字・metadata.version・When NOT to use 見出し・停止契約の構造（承認語彙 → ハードストップ）の 7 項目を機械検証。`--purity` でツール純度レポート（本文のツール固有語彙の出現数・FAIL にしない）。スキル改訂時と配置前に実行する（PostToolUse hook でも自動実行）
- **素通り検査** (`scripts/passthrough_check.py`): ハードストップが実地で守られるかを、フレッシュエージェントの実行前後の SHA1 差分で機械判定（課金・任意・デフォルトでは回さない）。シナリオは `tests/passthrough/[skill]/scenario.md`。`--dry-run` で無課金の構造確認。編成は `skill-test` スキル
- **npm script** (`package.json`): `validate`（静的検査）/ `validate:portability`（配布可スキルの内部前提混入）/ `validate:assets`（下記の契約突合）/ `lint`（Biome）。検証コマンドを散文から探さずに済むようにしている
- **資産どうしの契約突合** (`scripts/check_asset_consistency.py`): 「同じ情報が複数箇所にある」箇所を機械で突合し、**片側修正を検出する**。検査する 7 契約 — (a) 同送 hook が `HOOK_REGISTRATIONS` に登録済みか（死んだ登録も検出）/ (b) `.claude/hooks/` の全ファイルが「同送」か「master-only」に分類済みか / (c) README の hook 記述が実体と一致するか / (d) 同送 hook が配置手順に載っているか / (e) permissions が配布用とマスター専用に分類済みか（未分類・ドリフト・死んだ分類・重複の 4 方向）/ (f) **`settings.json` の hooks 登録が実体と一致するか**（置いたのに登録を忘れて一度も発火しない、を検出）/ (h) `MASTER_ONLY`（配布分類）が `deploy_skills.py` と `validate_skills.py` で一致するか。**違反で exit 1**。この検査は「`expected_hooks()` に足したが `HOOK_REGISTRATIONS` に登録し忘れて配置が全滅する」型が 2 度起きたことから作られている（うち 1 度は、まさに同じ漏れをルール化したコミット自身が再発させた）。会社向け持ち出しセット用の契約 (g)(i) と `check_export_stopcontract.py` は 20260730 に Frozen handoff として除去済み
- **敵対的スキルレビュー** (`prompts/adversarial-skill-review.md`): スキル**本文の中身**を敵対的に精読するプロンプト（人が貼って使う・フレッシュな subagent 推奨）。境界の重複と空白・オーケストレーターとの契約ズレ・片側修正・死んだ参照・迂回経路・配布分類違反を、静的検査と素通り検査の**間**の層として拾う。ファイルは一切変更せず、証拠つきの指摘と方向性1行だけを提示して止まる
- **品質ゲート hooks** (`.claude/hooks/post-edit-lint.sh` / `stop-typecheck.sh` / `validate-skill-edit.sh`): 編集ごとの lint 差し戻し・終了宣言時の tsc・SKILL.md 編集時の `validate_skills.py` 自動実行。前 2 本はフェイルオープン（設定が無ければ素通し）なのでスタックを問わず配れる
- **配置スクリプト** (`scripts/deploy_skills.py`): 配置先へのスキル本体とガードレール（hooks・permissions・.gitignore）の同送。`--dry-run` / `--overwrite`。master-only スキルと master-only hook は配置対象から除外される。**permissions はマスターの settings.json をそのまま配らず、`DEPLOY_PERMISSIONS` に明示列挙した配布用サブセットを配る** — マスターの deny には「このリポジトリは依存を増やさない」というマスター固有の方針（`npm install` 等の deny）が混ざっており、そのまま配ると配置先の開発フローを止めるため。**配布サブセットはベースラインであって最終形ではない**（最終的なセキュリティルールは配布先に依存するので、dry-run 提示で調整する）。編成は `skill-deploy` スキル
- **ドリフト検出** (`scripts/check_deploy_drift.py`, argparse・`--help` あり): 配置先スキルの直接編集・マスター先行・記録なしの3分類 + **hooks の未配置 / 内容差分**（同送すべき hook が配置先に無い・内容がずれている）+ 溜まった skill-issues.md を収集（読み取り専用）。同送すべき hook の判定は `deploy_skills.py` の `expected_hooks()` を import して単一情報源にしている。引数なしで `deployments.md` の全配置先をループ。編成は `skill-harvest` スキル
- **settings.json**: パッケージインストール（dlx / bunx / npx -y 含む）・`.env` / 鍵ファイル読み取り（Bash / Read 両方）・破壊的 git 操作・`rm -rf` を deny。素の `npx` / `rm -r` / `git push` / ガードレール自身（settings・hooks）の変更は ask。加えて **`CLAUDE.md` / `docs/knowledge/` / `docs/decisions/` への書き込みも ask**（ディレクトリ配下は `*` / `**` / `**/*` の**3形式を列挙**する — 単一形式では直下のファイルを取りこぼしうる。根拠は docs/knowledge/claude-code-config.md の「glob はプレフィックス形とサフィックス形の両方を列挙する」） — CLAUDE.md が宣言している「CLAUDE.md・docs/ への書き込みは承認制」に機械的な裏づけを与えるもの（本文のハードストップだけでは knowledge-capture が承認前に書き込む破れが 1/4 の頻度で再現したため、`skill-design-patterns.md` の「摩擦が実証されてから機械の別防御を足す」に従って追加）。配置先への同送手順は [docs/starter-kit.md](docs/starter-kit.md) 手順 6

---

## 横展開（他プロジェクトでの利用）

このリポジトリがマスター。スキルは人が選んで配置先プロジェクトの `.claude/skills/` に手動コピーし、改善は配置先で直接編集せずマスターに還元して再コピーで配る。

推奨構成・配置手順（8 ステップ）・配布方式の段階基準・CLAUDE.md 雛形の一次情報: [docs/starter-kit.md](docs/starter-kit.md)
