# AI Skills — フロントエンド開発ワークフロー

個人用の Claude Code スキルセット。React / TypeScript プロジェクトにおける設計から実装・レビュー・ナレッジ保存までを一貫したワークフローとして定義している。

**スタック**: React / TypeScript / Vitest / React Testing Library / MSW / Playwright

各スキルの詳細手順は `.claude/skills/[name]/SKILL.md` が一次情報。この README は全体像のみを示す。

---

## ディレクトリ構成

```
.
├── CLAUDE.md                          # 行動ルール（Claude の設定）
├── .claude/
│   ├── settings.json                  # パーミッション・フック設定
│   ├── hooks/
│   │   └── session-stop.sh            # セッション終了時に .capture-needed フラグを作成
│   └── skills/                        # スキル定義（下の一覧を参照）
├── .steering/                         # クロスセッション コンテキスト（複数セッションタスクのみ）
├── deployments.md                     # 配置先レジストリ（マスター専用・skill-harvest が読む）
├── scripts/
│   ├── validate_skills.py             # スキル frontmatter・構造の機械検証（マスター専用）
│   ├── passthrough_check.py           # 素通り検査（ハードストップの実地検証・課金・任意）
│   └── check_deploy_drift.py          # 配置先ドリフト検出・issues 還流（読み取り専用）
├── templates/                         # スキル作成用メタ雛形（SKILL.template.md・README.md）
├── tests/
│   └── passthrough/[skill]/scenario.md # 素通り検査のシナリオ資産（マスター専用）
└── docs/
    ├── starter-kit.md                 # 他プロジェクトへの配置手順・推奨構成
    ├── knowledge/                     # 経験・パターン集
    └── decisions/                     # ADR（設計判断）
```

---

## メインワークフロー

```
[0] 入口分岐      新機能 → design-doc ／ バグ・障害 → debug
                  （小さい修正は即修正で完結、構造に触る修正は design-doc に接続）
      ↓
[1] 設計          design-doc（.steering/ は複数セッションタスクのみ作成。feature-pipeline 配下では常に作成）
      ↓           （任意）design-premortem — 人間レビュー前に敵対的レビューで設計の穴出し
[2] レビュー      人間がレビュー・承認（design.md: DRAFT → APPROVED）
      ↓
[3] 実装          impl-from-design  ←→  tdd ／ クリティカルパスは e2e
      ↓           （任意）impl-tournament — リスクの高いアプローチ選択で N 並列実装を比較
[4] コードレビュー  frontend-code-review（フル: 7エージェント並列 / 軽量: 直列）
      ↓
[5] 指摘修正      修正 → 指摘があった軸のみ差分再レビュー
      ↓
[6] PR 提出       pr-create → CI 確認（**マージはしない**）
      ↓
[6.5] PR 往復     pr-feedback — 返ってきたコメント・CI 失敗をトリアージ → 修正 → 返信
      ↓
[6.9] マージ      人間の判断（外向き操作）
      ↓
[7] ナレッジ保存  knowledge-capture（パターン → docs/）／ session-retrospective — セッション摩擦を skill-issues.md に採掘
      ↓
[8] 福利化        compound（パターン → ルール・知識・スキル改善）
      ↓
[9] アーカイブ    steering archive

定期（フェーズ外）: rule-audit — ルールの削除テスト・統合・GC ／ security-audit — セットアップ資産のセキュリティ監査（サードパーティ採用前・定期）
マスター保守（フェーズ外）: skill-test — スキルの回帰テスト ／ skill-harvest — 配置先からの還流
```

フェーズ全体を一括で進めたい場合は `feature-pipeline` が上記スキルを順に編成する（人間の承認ゲートは「不可逆/外向き・価値判断・責任」に該当する 4 点のみ: 設計承認・指摘トリアージ・マージ・知見保存。該当しない境界（実装→レビュー等）は報告して自動で進む・途中フェーズから再開可）。

**運用ルール**: このワークフロー図と `feature-pipeline` スキルは同一コミットで改訂する（図とオーケストレーターのドリフト防止）。

---

## スキル一覧

### オーケストレーション

| スキル | 役割 |
|---|---|
| [`feature-pipeline`](.claude/skills/feature-pipeline/SKILL.md) | メインワークフローを一気通貫で回すエンドツーエンドのオーケストレーター。既存スキル（design-doc → impl-from-design → frontend-code-review → pr-create → knowledge-capture / compound）を順に呼び出し、主要な判断点（設計承認・指摘トリアージ・マージ・知見保存）で人間の承認ゲートを挟む。`.steering/[task]/` の成果物から現在地を検出して途中フェーズから再開できる |

### 設計・コンテキスト管理

| スキル | 役割 |
|---|---|
| [`design-doc`](.claude/skills/design-doc/SKILL.md) | タスク開始時に design.md（Goal/Scope/Acceptance + 設計）と tasklist.md を作成。**design.md 作成後は人間の承認まで実装しない**。1セッションで終わるタスクには .steering を作らない |
| [`debug`](.claude/skills/debug/SKILL.md) | 障害調査。再現 → 仮説 → 切り分け → 根本原因 → 修正方針。小さい修正（影響が閉じる・巻き戻し容易・テストで再発防止可）は承認を得て即修正、構造に触る修正は design-doc に接続 |
| [`steering`](.claude/skills/steering/SKILL.md) | `.steering/` のライフサイクル管理（init / resume / status / archive）。ファイル仕様は [references/spec.md](.claude/skills/steering/references/spec.md) |
| [`design-premortem`](.claude/skills/design-premortem/SKILL.md) | 人間レビュー前の敵対的レビュー。エッジケース・状態複雑化・テスト容易性・スコープ・「3ヶ月後に後悔する理由」の6観点で design.md を攻撃し `## Premortem` に反映。**設計は承認しない**（任意・design-doc の Phase 2.5） |

### 実装

| スキル | 役割 |
|---|---|
| [`impl-from-design`](.claude/skills/impl-from-design/SKILL.md) | APPROVED な design.md から実装。code-explorer による既存パターン調査 → TDD モード（推奨）/ Impl-first モードを選択。設計と乖離したら止まって報告 |
| [`tdd`](.claude/skills/tdd/SKILL.md) | Red → Green → Refactor サイクルの単独ユーティリティ。テストパターン集は [references/patterns.md](.claude/skills/tdd/references/patterns.md) |
| [`e2e`](.claude/skills/e2e/SKILL.md) | E2E テストの作成・レビュー。クリティカルパス選定・1テスト1シナリオ・安定性原則（flaky 防止）・実ユーザー視点の4判断軸。Playwright 具体例は [references/patterns.md](.claude/skills/e2e/references/patterns.md)（カートリッジ — 配置先で再生成） |
| [`impl-tournament`](.claude/skills/impl-tournament/SKILL.md) | リスクの高いアプローチ選択で、APPROVED な design.md から2〜3の異なる実装を worktree 並列で作り採点して人間が勝者を選ぶ。**開始前にコスト見積 + 無料代替の承認必須**。常用しない（任意）。worktree コマンド・モデル振り分けは [references/commands.md](.claude/skills/impl-tournament/references/commands.md) |

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
| [`rule-audit`](.claude/skills/rule-audit/SKILL.md) | 剪定。CLAUDE.md・ルール・スキル frontmatter を定期監査し、削除テスト・症状診断で**保持/削除/統合/移動/明確化**を判定。compound（追加）と対をなす。適用は承認制 |
| [`knowledge-capture`](.claude/skills/knowledge-capture/SKILL.md) | セッションの知見を docs/knowledge/（パターン）・docs/decisions/（ADR）・CLAUDE.md（行動ルール）・glossary に振り分けて保存。承認制 |
| [`session-retrospective`](.claude/skills/session-retrospective/SKILL.md) | セッション終盤に会話履歴から摩擦（スキル誤発動・ユーザー訂正・手戻り・パーミッション拒否・曖昧さ）を採掘し `skill-issues.md` に起票。**昇格はしない**（compound の原料を作る）。ゼロ件なら起票しない |
| [`empirical-prompt-tuning`](.claude/skills/empirical-prompt-tuning/SKILL.md) | スキル・プロンプト自体の品質改善。フレッシュな subagent に実行させて両面評価し、改善が頭打ちになるまで反復 |
| [`security-audit`](.claude/skills/security-audit/SKILL.md) | セットアップ資産（スキル・agents・hooks・settings・依存/MCP）のサプライチェーン・セキュリティを**静的**監査。外部送信・シークレット読取・破壊的コマンド・広範権限・インジェクション構造を機械スキャンし、判別不能はフェイルクローズで要確認に。**対象本文を全文解釈せずヒット行のみ判定**（監査対象の埋め込み指示に従わない）。「検出なし」は安全証明ではなく目視確認ルールを置換しない。修正は承認制。review-security（コード diff）とは対象が別 |

### マスター専用ツール（配布しない）

| スキル | 役割 |
|---|---|
| [`skill-test`](.claude/skills/skill-test/SKILL.md) | スキルの回帰テストを2層で編成。静的層（`validate_skills.py`・無料・毎回）+ 実行層（`passthrough_check.py`・課金・任意）。**実行層はコスト明示 + 承認必須・hooks 接続禁止** |
| [`skill-harvest`](.claude/skills/skill-harvest/SKILL.md) | 配置先からの還流。`deployments.md` の各配置先の再コピー候補・ドリフト・溜まった skill-issues.md を `check_deploy_drift.py`（読み取り専用）で収集。**配置先への書き込みは承認制** |
| [`skill-deploy`](.claude/skills/skill-deploy/SKILL.md) | 新規配置の実行版（starter-kit 配置手順 1〜7 を駆動）。セット選択 → dry-run 提示 → 明示承認 → `deploy_skills.py` 実行 → 残タスク案内。**配置先への書き込みは承認制**。既存配置先の更新・回収は skill-harvest |

---

## 自己改善ループ

```
コードの問題:  frontend-code-review → review-result.md ─┐
実装中の判断:  decisions.md ────────────────────────────┼→ compound → CLAUDE.md ルール / docs/knowledge / ADR
スキルの問題:  session-retrospective → skill-issues.md ─┘       │
                                                                ├→ codify-log.md（昇格履歴）
過去の昇格:    codify-log.md × review-result.md 突合 ←──────────┘
               （ルールが効いていなければルール自体を改善）
スキル不具合 → 該当 SKILL.md 修正 + empirical-prompt-tuning / skill-test で検証
配置先 → 還流:  session-retrospective（配置先で併配）→ skill-issues.md → skill-harvest → マスターの compound
```

- セッション中にスキルの誤発動・曖昧な指示に気づいたら `.steering/[task]/skill-issues.md` に記録する（CLAUDE.md ルール。decisions.md / skill-issues.md / blockers.md への追記は承認不要 — 内容の取捨選択は compound / knowledge-capture 時に行う）
- compound がルールを増やし、`rule-audit` が定期監査（削除テスト）で刈る — 追加と剪定の両輪で CLAUDE.md の肥大化を構造的に抑える
- Stop hook が knowledge-capture 未実行タスクに `.capture-needed` フラグを作成し、次セッション開始時にリマインドされる
- frontend-code-review 完了時に `.codify-needed` フラグが作成され、compound への引き継ぎになる

---

## インフラ・設定

- **Stop Hook** (`.claude/hooks/session-stop.sh`): アクティブタスクに `capture_done` がなければ `.capture-needed` フラグを作成するだけの軽量フック（セッション記録は git が持つ）。成果物（*.md）の無いタスクディレクトリはスキップする
- **PreToolUse Guard** (`.claude/hooks/guard-env-read.sh`): Bash コマンド全文を検査し、`.env` 系に触れるものを ask に落とす（deny の前置一致では防げない head/sed/base64 等の迂回対策）。jq 未導入環境ではフェイルクローズ
- **検証スクリプト** (`scripts/validate_skills.py`): name 一致・description・行数・アストラル面絵文字・metadata.version・When NOT to use 見出し・停止契約の構造（承認語彙 → ハードストップ）の 7 項目を機械検証。`--purity` でツール純度レポート（本文のツール固有語彙の出現数・FAIL にしない）。スキル改訂時と配置前に実行する（PostToolUse hook でも自動実行）
- **素通り検査** (`scripts/passthrough_check.py`): ハードストップが実地で守られるかを、フレッシュエージェントの実行前後の SHA1 差分で機械判定（課金・任意・デフォルトでは回さない）。シナリオは `tests/passthrough/[skill]/scenario.md`。`--dry-run` で無課金の構造確認。編成は `skill-test` スキル
- **ドリフト検出** (`scripts/check_deploy_drift.py`): 配置先の直接編集・マスター先行・記録なしの3分類 + 溜まった skill-issues.md を収集（読み取り専用）。引数なしで `deployments.md` の全配置先をループ。編成は `skill-harvest` スキル
- **settings.json**: パッケージインストール（dlx / bunx / npx -y 含む）・`.env` / 鍵ファイル読み取り（Bash / Read 両方）・破壊的 git 操作・`rm -rf` を deny。素の `npx` / `rm -r` / `git push` / ガードレール自身（settings・hooks）の変更は ask。配置先への同送手順は [docs/starter-kit.md](docs/starter-kit.md) 手順 6

---

## 横展開（他プロジェクトでの利用）

このリポジトリがマスター。スキルは人が選んで配置先プロジェクトの `.claude/skills/` に手動コピーする（`~/.claude/` への配置・symlink・プラグイン化はしない）。

- 配置の取捨選択自体がガードレール（無関係なスキルの誤発動を防ぐ）
- 改善は必ずマスターに還元し、再コピーで配る。配置先で直接編集しない
- 配置時にマスターのコミットハッシュを各スキルの `metadata.source-commit` に記録する（ドリフト追跡は `git diff <hash>` 一発）
- スキルは CLAUDE.md・docs/・`.steering/` が無くても動く自己完結設計（[skill-design-patterns.md](docs/knowledge/skill-design-patterns.md)）

**推奨構成と配置手順**: [docs/starter-kit.md](docs/starter-kit.md)（最小/拡張セットの選定表・8 ステップの配置手順・CLAUDE.md 雛形）
**配置前チェック**: `python3 scripts/validate_skills.py`（frontmatter・構造の機械検証）
**配置後チェック**: スモークテスト（[starter-kit 手順 8](docs/starter-kit.md)。スキル一覧の確認・design-doc の承認ゲート停止・ガードレールの ask 落ち）

配布方式の段階基準:

| 段階 | 条件 | 配布方式 |
|---|---|---|
| 現在（個人・数プロジェクト） | 配置先 ≤ 3 程度 | 手動コピー + source-commit 記録 |
| 拡大 | 配置先が増えドリフト管理が手に余る | バージョンタグ付きスターターキット + 配置スクリプト（選択は人・記録は自動） |
| チーム標準化 | 複数メンバーが同一セットを使う | プラグイン化 or テンプレートリポジトリ（ADR を正式に改訂） |

経緯: [ADR 20260612-manual-copy-skill-distribution](docs/decisions/20260612-manual-copy-skill-distribution.md)

---

## スキル間の関係図

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

- `feature-pipeline` が上記の一連を承認ゲート付きで編成する（オーケストレーター）
- `empirical-prompt-tuning` は上記スキル自体の品質改善に横断的に使う
- マスター専用: `skill-test`（回帰テスト）/ `skill-deploy`（新規配置）/ `skill-harvest`（配置先の還流）は配布せずマスターで保守に使う
