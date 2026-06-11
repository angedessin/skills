# AI Skills — フロントエンド開発ワークフロー

個人用の Claude Code スキルセット。Next.js / TypeScript プロジェクトにおける設計から実装・レビュー・ナレッジ保存までを一貫したワークフローとして定義している。

**スタック**: Next.js / TypeScript / Vitest / React Testing Library / MSW / Playwright

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
[4] コードレビュー  frontend-code-review（フル: 5エージェント並列 / 軽量: 直列）
      ↓
[5] 指摘修正      修正 → 指摘があった軸のみ差分再レビュー
      ↓
[6] 福利化        compound（パターン → ルール・知識・スキル改善）
      ↓
[7] ナレッジ保存  knowledge-capture（パターン → docs/）
      ↓
[8] アーカイブ    steering archive
```

---

## スキル一覧

### 設計・コンテキスト管理

| スキル | 役割 |
|---|---|
| [`design-doc`](.claude/skills/design-doc/SKILL.md) | タスク開始時に design.md（Goal/Scope/Acceptance + 設計）と tasklist.md を作成。**design.md 作成後は人間の承認まで実装しない**。1セッションで終わるタスクには .steering を作らない |
| [`steering`](.claude/skills/steering/SKILL.md) | `.steering/` のライフサイクル管理（init / resume / status / archive）。ファイル仕様は [references/spec.md](.claude/skills/steering/references/spec.md) |

### 実装

| スキル | 役割 |
|---|---|
| [`impl-from-design`](.claude/skills/impl-from-design/SKILL.md) | APPROVED な design.md から実装。code-explorer による既存パターン調査 → TDD モード（推奨）/ Impl-first モードを選択。設計と乖離したら止まって報告 |
| [`tdd`](.claude/skills/tdd/SKILL.md) | Red → Green → Refactor サイクルの単独ユーティリティ。テストパターン集は [references/patterns.md](.claude/skills/tdd/references/patterns.md) |

### コードレビュー

| スキル | 役割 |
|---|---|
| [`frontend-code-review`](.claude/skills/frontend-code-review/SKILL.md) | オーケストレーター。コミット済み + 未コミットの diff をトリアージし、ロジック/コンポーネント変更はフルモード（5エージェント並列）、リファクタ/スタイルのみは軽量モード（直列）。結果を `review-result.md` に記録し、修正後は指摘があった軸のみ差分再レビュー |
| [`test-review`](.claude/skills/test-review/SKILL.md) | テストコード品質。実装エコー・アサーション品質・MSW 規律・RTL クエリ優先順位・カバレッジ意図の5軸 |
| [`impl-review`](.claude/skills/impl-review/SKILL.md) | 実装コード品質。設計整合性・プロジェクト規約・TypeScript・React/Next.js・基本 a11y の5軸 |
| [`review-security`](.claude/skills/review-security/SKILL.md) | XSS・型安全・env var・依存関係の4軸 |
| [`review-performance`](.claude/skills/review-performance/SKILL.md) | Bundle サイズ・再レンダリング・CWV の3軸 |
| [`review-a11y`](.claude/skills/review-a11y/SKILL.md) | セマンティクス・ARIA・フォーカス管理・キーボード操作の4軸 |

### ナレッジ管理・自己改善

| スキル | 役割 |
|---|---|
| [`compound`](.claude/skills/compound/SKILL.md) | 福利化。review-result.md / decisions.md / skill-issues.md からパターンを抽出し、ルール・知識・スキル改善に昇格。codify-log.md と突合して**昇格済みルールの効果検証**（再発検知）も行う。承認制 |
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

- セッション中にスキルの誤発動・曖昧な指示に気づいたら `.steering/[task]/skill-issues.md` に記録する（CLAUDE.md ルール）
- Stop hook が knowledge-capture 未実行タスクに `.capture-needed` フラグを作成し、次セッション開始時にリマインドされる
- frontend-code-review 完了時に `.codify-needed` フラグが作成され、compound への引き継ぎになる

---

## インフラ・設定

- **Stop Hook** (`.claude/hooks/session-stop.sh`): アクティブタスクに `capture_done` がなければ `.capture-needed` フラグを作成するだけの軽量フック（セッション記録は git が持つ）
- **settings.json**: パッケージインストール・`.env` 読み取り（Bash / Read 両方）・破壊的 git 操作・`rm -rf` を deny

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
                         （テスト）   （実装）    （sec/perf/a11y）
```

`empirical-prompt-tuning` は上記スキル自体の品質改善に横断的に使う。
