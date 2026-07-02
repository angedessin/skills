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
└── docs/
    ├── knowledge/                     # 経験・パターン集
    └── decisions/                     # ADR（設計判断）
```

---

## メインワークフロー

```
[1] 設計          design-doc（.steering/ は複数セッションタスクのみ作成）
      ↓
[2] レビュー      人間がレビュー・承認（design.md: DRAFT → APPROVED）
      ↓
[3] 実装          impl-from-design  ←→  tdd
      ↓
[4] コードレビュー  frontend-code-review（フル: 7エージェント並列 / 軽量: 直列）
      ↓
[5] 指摘修正      修正 → 指摘があった軸のみ差分再レビュー
      ↓
[6] 福利化        compound（パターン → ルール・知識・スキル改善）
      ↓
[7] ナレッジ保存  knowledge-capture（パターン → docs/）
      ↓
[8] アーカイブ    steering archive
```

フェーズ全体を一括で進めたい場合は `feature-pipeline` が上記スキルを順に編成する（各フェーズ境界に人間の承認ゲートあり・途中フェーズから再開可）。

入口の分岐: 新機能・タスク開始は `design-doc`、バグ・障害の原因調査は `debug`（小さい修正は即修正で完結、構造に触る修正は design-doc に接続して上記フローに合流）。

---

## スキル一覧

### オーケストレーション

| スキル | 役割 |
|---|---|
| [`feature-pipeline`](.claude/skills/feature-pipeline/SKILL.md) | メインワークフローを一気通貫で回すエンドツーエンドのオーケストレーター。既存スキル（design-doc → impl-from-design → frontend-code-review → knowledge-capture / compound）を順に呼び出し、各フェーズ境界で人間の承認ゲートを挟む。`.steering/[task]/` の成果物から現在地を検出して途中フェーズから再開できる |

### 設計・コンテキスト管理

| スキル | 役割 |
|---|---|
| [`design-doc`](.claude/skills/design-doc/SKILL.md) | タスク開始時に design.md（Goal/Scope/Acceptance + 設計）と tasklist.md を作成。**design.md 作成後は人間の承認まで実装しない**。1セッションで終わるタスクには .steering を作らない |
| [`debug`](.claude/skills/debug/SKILL.md) | 障害調査。再現 → 仮説 → 切り分け → 根本原因 → 修正方針。小さい修正（影響が閉じる・巻き戻し容易・テストで再発防止可）は承認を得て即修正、構造に触る修正は design-doc に接続 |
| [`steering`](.claude/skills/steering/SKILL.md) | `.steering/` のライフサイクル管理（init / resume / status / archive）。ファイル仕様は [references/spec.md](.claude/skills/steering/references/spec.md) |

### 実装

| スキル | 役割 |
|---|---|
| [`impl-from-design`](.claude/skills/impl-from-design/SKILL.md) | APPROVED な design.md から実装。code-explorer による既存パターン調査 → TDD モード（推奨）/ Impl-first モードを選択。設計と乖離したら止まって報告 |
| [`tdd`](.claude/skills/tdd/SKILL.md) | Red → Green → Refactor サイクルの単独ユーティリティ。テストパターン集は [references/patterns.md](.claude/skills/tdd/references/patterns.md) |

### コードレビュー

| スキル | 役割 |
|---|---|
| [`frontend-code-review`](.claude/skills/frontend-code-review/SKILL.md) | オーケストレーター。コミット済み + 未コミットの diff をトリアージし、ロジック/コンポーネント変更はフルモード（7エージェント並列）、リファクタ/スタイルのみは軽量モード（直列。CSS 変更を含む場合は review-ui も実行）。結果を `review-result.md` に記録し、修正後は指摘があった軸のみ差分再レビュー |
| [`test-review`](.claude/skills/test-review/SKILL.md) | テストコード品質。実装エコー・アサーション品質・ネットワークモック境界・クエリ優先順位・カバレッジ意図の5軸 |
| [`impl-review`](.claude/skills/impl-review/SKILL.md) | 実装コード品質。設計整合性・プロジェクト規約・TypeScript・React・基本 a11y の5軸 |
| [`review-security`](.claude/skills/review-security/SKILL.md) | XSS・型安全・env var・依存関係の4軸 |
| [`review-performance`](.claude/skills/review-performance/SKILL.md) | Bundle サイズ・再レンダリング・CWV の3軸 |
| [`review-a11y`](.claude/skills/review-a11y/SKILL.md) | セマンティクス・ARIA・フォーカス管理・キーボード操作の4軸 |
| [`review-correctness`](.claude/skills/review-correctness/SKILL.md) | ロジック正当性。境界条件・null/undefined・非同期レース/stale closure・状態遷移/エラー握りつぶしの4軸 |
| [`review-ui`](.claude/skills/review-ui/SKILL.md) | UI 品質。レイアウト・レスポンシブ / デザイン整合（トークンは references をカートリッジとして配置先で再生成） / UX 状態網羅（loading・error・empty・disabled）の3軸 |

### ナレッジ管理・自己改善

| スキル | 役割 |
|---|---|
| [`compound`](.claude/skills/compound/SKILL.md) | 福利化。review-result.md / decisions.md / skill-issues.md からパターンを抽出し、ルール・知識・スキル改善に昇格。codify-log.md と突合して**昇格済みルールの効果検証**（再発検知）も行う。昇格の適用は承認制（昇格ゼロ時のフラグ整理のみ承認不要） |
| [`rule-audit`](.claude/skills/rule-audit/SKILL.md) | 剪定。CLAUDE.md・ルール・スキル frontmatter を定期監査し、削除テスト・症状診断で**保持/削除/統合/移動/明確化**を判定。compound（追加）と対をなす。適用は承認制 |
| [`knowledge-capture`](.claude/skills/knowledge-capture/SKILL.md) | セッションの知見を docs/knowledge/（パターン）・docs/decisions/（ADR）・CLAUDE.md（行動ルール）・glossary に振り分けて保存。承認制 |
| [`empirical-prompt-tuning`](.claude/skills/empirical-prompt-tuning/SKILL.md) | スキル・プロンプト自体の品質改善。フレッシュな subagent に実行させて両面評価し、改善が頭打ちになるまで反復 |

---

## 自己改善ループ

```
コードの問題:  frontend-code-review → review-result.md ─┐
実装中の判断:  decisions.md ────────────────────────────┼→ compound → CLAUDE.md ルール / docs/knowledge / ADR
スキルの問題:  skill-issues.md ─────────────────────────┘       │
                                                                ├→ codify-log.md（昇格履歴）
過去の昇格:    codify-log.md × review-result.md 突合 ←──────────┘
               （ルールが効いていなければルール自体を改善）
スキル不具合 → 該当 SKILL.md 修正 + empirical-prompt-tuning で検証
```

- セッション中にスキルの誤発動・曖昧な指示に気づいたら `.steering/[task]/skill-issues.md` に記録する（CLAUDE.md ルール。decisions.md / skill-issues.md / blockers.md への追記は承認不要 — 内容の取捨選択は compound / knowledge-capture 時に行う）
- compound がルールを増やし、`rule-audit` が定期監査（削除テスト）で刈る — 追加と剪定の両輪で CLAUDE.md の肥大化を構造的に抑える
- Stop hook が knowledge-capture 未実行タスクに `.capture-needed` フラグを作成し、次セッション開始時にリマインドされる
- frontend-code-review 完了時に `.codify-needed` フラグが作成され、compound への引き継ぎになる

---

## インフラ・設定

- **Stop Hook** (`.claude/hooks/session-stop.sh`): アクティブタスクに `capture_done` がなければ `.capture-needed` フラグを作成するだけの軽量フック（セッション記録は git が持つ）
- **settings.json**: パッケージインストール・`.env` 読み取り（Bash / Read 両方）・破壊的 git 操作・`rm -rf` を deny

---

## 横展開（他プロジェクトでの利用）

このリポジトリがマスター。スキルは人が選んで配置先プロジェクトの `.claude/skills/` に手動コピーする（`~/.claude/` への配置・symlink・プラグイン化はしない）。

- 配置の取捨選択自体がガードレール（無関係なスキルの誤発動を防ぐ）
- 改善は必ずマスターに還元し、再コピーで配る。配置先で直接編集しない
- 配置時にマスターのコミットハッシュを配置先に記録する（ドリフト追跡）
- スキルは CLAUDE.md・docs/・`.steering/` が無くても動く自己完結設計（[skill-design-patterns.md](docs/knowledge/skill-design-patterns.md)）

経緯: [ADR 20260612-manual-copy-skill-distribution](docs/decisions/20260612-manual-copy-skill-distribution.md)

---

## スキル間の関係図

```
design-doc ──→ impl-from-design ──→ frontend-code-review
    │                │                      │
    ↓                ↓                      ↓
steering ←──── tdd              compound + knowledge-capture
                                           │
                              ┌────────────┼────────────┐
                         test-review  impl-review  review-*
                         （テスト）   （実装）    （sec/perf/a11y/correctness/ui）
```

`empirical-prompt-tuning` は上記スキル自体の品質改善に横断的に使う。
