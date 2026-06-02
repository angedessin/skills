# AI Skills — フロントエンド開発ワークフロー

個人用の Claude Code スキルセット。Next.js / TypeScript プロジェクトにおける設計から実装・レビュー・ナレッジ保存までを一貫したワークフローとして定義している。

**スタック**: Next.js / TypeScript / Vitest / React Testing Library / MSW / Playwright

---

## ディレクトリ構成

```
.
├── CLAUDE.md                          # 行動ルール（Claude の設定）
├── .claude/
│   ├── settings.json                  # パーミッション・フック設定
│   ├── hooks/
│   │   └── session-stop.sh            # セッション終了時の自動ログ記録
│   └── skills/                        # スキル定義
│       ├── design-doc/                # 設計ドキュメント作成
│       ├── steering/                  # クロスセッション管理
│       ├── impl-from-design/          # 設計から実装
│       ├── tdd/                       # TDD サイクル
│       ├── frontend-code-review/      # レビュー オーケストレーター
│       ├── test-review/               # テストコードレビュー
│       ├── impl-review/               # 実装コードレビュー
│       ├── review-security/           # セキュリティレビュー
│       ├── review-performance/        # パフォーマンスレビュー
│       ├── review-a11y/               # アクセシビリティレビュー
│       ├── compound/                  # パターン昇格（福利化）
│       ├── knowledge-capture/         # ナレッジ保存
│       └── empirical-prompt-tuning/   # プロンプト品質改善
├── .steering/                         # クロスセッション コンテキスト（タスク毎）
└── docs/
    ├── knowledge/                     # 経験・パターン集
    │   └── testing-patterns.md
    └── decisions/                     # ADR（設計判断）
```

---

## メインワークフロー

タスクは以下の順序で進む。各フェーズにスキルが対応している。

```
[1] 設計          design-doc
      ↓
[2] レビュー      人間がレビュー・承認
      ↓
[3] 実装          impl-from-design  ←→  tdd
      ↓
[4] コードレビュー  frontend-code-review（5エージェント並列）
      ↓
[5] 指摘修正      手作業
      ↓
[6] 福利化        compound（パターン → CLAUDE.md / スキル）
      ↓
[7] ナレッジ保存  knowledge-capture（パターン → docs/）
      ↓
[8] アーカイブ    steering archive
```

---

## スキル一覧

### 設計・コンテキスト管理

#### `design-doc` — 設計ドキュメント作成

**起動タイミング**: 「〜を作ろう」「設計して」「新しいタスク」など、新しい機能・タスク開始のシグナル

`.steering/[YYYYMMDD]-[task-name]/` を作成し、以下の3ファイルを生成する:

| ファイル | 内容 |
|---|---|
| `requirements.md` | Goal / Scope / Constraints / Acceptance criteria |
| `design.md` | Approach / Key components / Data flow / Test strategy / Open questions |
| `tasklist.md` | 実装・レビュー・Deploy・Compound・Knowledgeのチェックリスト |

**重要**: `design.md` 作成後は必ず止まって人間のレビューを待つ。承認前に実装に入らない。

承認を受けたら `design.md` の Status を `DRAFT → APPROVED` に更新し、`impl-from-design` スキルを案内する。

**起動しない場面**: `.steering/` が既存のタスクで存在する（→ `steering` resume を使う）/ 30分以内のバグ修正 / テスト追加のみ

---

#### `steering` — クロスセッションコンテキスト管理

**起動タイミング**: 「タスクを再開」「steering status」「アーカイブして」と明示的に言われた場合

`.steering/` ディレクトリのライフサイクルを管理するインフラスキル。4つのモードを持つ:

| モード | トリガー | 動作 |
|---|---|---|
| **init** | "新しいタスク"、直接呼び出し | タスクディレクトリを作成 |
| **resume** | "再開"、"[task] の続き" | requirements/design/tasklist を読んでサマリーを提示 |
| **status** | "進行中のタスクは？" | アクティブタスクの一覧テーブルを表示 |
| **archive** | "完了"、"アーカイブして" | `tasklist.md` 全チェック済み確認後に `archived/` へ移動 |

`.steering/` 構造:
```
.steering/
├── [YYYYMMDD]-[task-name]/
│   ├── requirements.md      必須
│   ├── design.md            必須（APPROVED まで実装禁止）
│   ├── tasklist.md          必須（毎セッション更新）
│   ├── session-log.md       Stop hook が自動追記
│   ├── decisions.md         任意
│   ├── blockers.md          任意
│   ├── review-result.md     frontend-code-review が生成
│   ├── .capture-needed      フラグ: knowledge-capture 未実行
│   ├── .codify-needed       フラグ: compound 未実行
│   └── capture_done         フラグ: knowledge-capture 完了
└── archived/
```

---

### 実装

#### `impl-from-design` — 設計から実装

**起動タイミング**: 「実装を開始して」「設計が承認された」

前提: `.steering/[task]/design.md` の Status が `APPROVED` であること。

**実行フロー**:

1. **前提チェック** — `design.md` の Status を確認。`DRAFT` なら止まる
2. **コードベース調査** — `feature-dev:code-explorer` で既存パターンを調査し `design.md` の `## Research` に記録
3. **モード選択** — ユーザーに確認

```
1. TDD モード（推奨）: Red → Green → Refactor
2. Impl-first モード: 実装 → テスト追加
```

**TDD モード**: `tasklist.md` のタスクを1つずつ、Red（失敗テスト）→ Green（最小実装）→ Refactor サイクルで処理。

**設計との乖離が生じた場合**: 実装を止めてユーザーに報告。勝手に設計変更しない。

完了後は `frontend-code-review` スキルを案内する。

---

#### `tdd` — TDD サイクル（単独ユーティリティ）

**起動タイミング**: 「テストを先に書いて」「既存コードにテストを追加して」「TDD で」

`impl-from-design` から参照される他、既存コードへのテスト追加に単独で使う。

**Red → Green → Refactor サイクル**:

```bash
# Red: 失敗することを確認
npx vitest run path/to/the.test.ts

# Green: 最小実装でパス
npx vitest run path/to/the.test.ts

# Refactor: テストが緑のまま整理
```

「正しい理由」で失敗することが Red の条件。コンパイルエラーは Red ではない。

**対応パターン**:
- Unit テスト（describe/it 形式・In-source testing）
- Component テスト（React Testing Library）
- MSW によるネットワークモック
- Hook テスト（renderHook）
- 状態管理テスト（Jotai 等）
- Server Action / API Route テスト
- E2E（Playwright）

**テストパターンの詳細**: `.claude/skills/tdd/references/patterns.md`

---

### コードレビュー

#### `frontend-code-review` — レビュー オーケストレーター

**起動タイミング**: 「コードをレビューして」「実装を確認して」

diff のトリアージでモードを自動判定し、適切なサブスキルを実行するオーケストレーター。

**Phase 1 — トリアージ**:

| ファイルパターン | 種別 |
|---|---|
| `src/lib/` `src/hooks/` `src/api/` `src/utils/` | ロジック変更 |
| `src/components/` `src/app/` `src/pages/` | コンポーネント変更 |
| リネーム・移動・型定義のみ | リファクタリング |
| `*.css` `*.json` `config.*` | スタイル/設定のみ |

**Phase 2A — フルモード**（ロジック/コンポーネント変更を含む場合）:
5エージェントを**単一メッセージで並列**ディスパッチ:

```
test-agent    → test-review スキルを実行
impl-agent    → impl-review スキルを実行
security-agent → review-security スキルを実行
perf-agent    → review-performance スキルを実行
a11y-agent    → review-a11y スキルを実行
```

**Phase 2B — 軽量モード**（リファクタリング/スタイルのみ）:
`test-review` → `impl-review` を直列で実行。

**Phase 3 — 統合サマリー**:
全エージェントの結果を集約して `.steering/[task]/review-result.md` に書き込む。
完了後に `.codify-needed` フラグを作成（compound スキルへの引き継ぎ）。

---

#### `test-review` — テストコードレビュー

**起動タイミング**: `frontend-code-review` から（または「テストをレビューして」で単独利用可）

スコープ: `*.test.ts` / `*.spec.ts` / `*.test.tsx`

**5つのレビュー軸**:

| Axis | 確認内容 |
|---|---|
| 実装エコー（最重要） | 内部 state・dispatch 引数・CSS クラスをアサートしていないか |
| アサーション品質 | `toBeTruthy()` など曖昧なアサーション / 非同期アサーションの正しさ |
| MSW 規律 | ネットワーク呼び出しを `vi.mock` でモックしていないか |
| RTL クエリ優先順位 | `getByRole > getByLabelText > getByText > getByTestId` を守っているか |
| カバレッジの意図 | アサーションなしテスト・実装コピーなどの低価値テストがないか |

問題を `spec changed / implementation bug / test was wrong / low-value` に分類して提示。

---

#### `impl-review` — 実装コードレビュー

**起動タイミング**: `frontend-code-review` から（または「実装をレビューして」で単独利用可）

スコープ: `.ts` / `.tsx`（テストファイルを除く）

**5つのレビュー軸**:

| Axis | 確認内容 |
|---|---|
| 設計整合性（最重要） | `design.md` の Key components・Approach・Open questions との乖離 |
| プロジェクト規約 | `docs/knowledge/` antipatterns / CLAUDE.md スタック制約 |
| TypeScript 品質 | `as any` / `as unknown` / 非 null アサーション過剰 / `@ts-ignore` |
| React/Next.js パターン | useEffect deps / Server-Client 境界 / 過剰な state |
| アクセシビリティ（基本） | `<div onClick>` → `<button>` / aria-label / `<img alt>` |

---

#### `review-security` — セキュリティレビュー

**4つのチェック軸**: XSS リスク / 型安全とインジェクション / env var・シークレット管理 / 依存関係の脆弱性

```typescript
// ❌ dangerouslySetInnerHTML に外部入力を直接渡す
// ❌ NEXT_PUBLIC_ なしの env var をクライアントで参照
// ❌ as any 経由で外部入力が型検証なしに使われる
```

---

#### `review-performance` — パフォーマンスレビュー

**3つのチェック軸**: Bundle サイズ / 不要な再レンダリング / Core Web Vitals（Next.js 固有）

```typescript
// ❌ import _ from 'lodash' （全量インポート）
// ❌ <Child config={{ key: 'value' }} /> （毎レンダリングで新しい参照）
// ❌ <Image src="/hero.jpg" /> （above the fold に priority なし）
```

---

#### `review-a11y` — アクセシビリティレビュー

**4つのチェック軸**: セマンティクスとインタラクティブ要素 / ARIA ラベル / フォーカス管理 / キーボード操作

```tsx
// ❌ <div onClick={handleSubmit}> → ✅ <button type="button" onClick={handleSubmit}>
// ❌ アイコンのみのボタンに aria-label なし
// ❌ モーダル開閉時にフォーカスが移動しない
// ❌ onMouseEnter のみ（onFocus がない）
```

---

### ナレッジ管理

#### `compound` — パターン昇格（福利化）

**起動タイミング**: 「福利化して」「codify して」「ルール化して」/ `.codify-needed` フラグがある場合

`frontend-code-review` の結果（`review-result.md`・`session-log.md`・`decisions.md`）から「再利用可能な学び」を抽出し、次のサイクルで自動的に防止できる形に変換する。

**昇格候補の優先順位**:

| 優先度 | 元データ | 昇格先 |
|---|---|---|
| 1 | 複数ファイルで繰り返す指摘 | CLAUDE.md ルール or lint ルール |
| 2 | 知らなかった仕様・落とし穴 | `docs/knowledge/[topic].md` |
| 3 | 技術的判断とその理由 | `docs/decisions/[date]-[slug].md`（ADR） |
| 4 | 再利用可能な実装パターン | `docs/knowledge/` or 新スキルの骨組み |

ドラフトを提示してユーザーの承認を得てから適用する（自動適用しない）。
完了後に `.codify-needed` フラグを削除。

---

#### `knowledge-capture` — ナレッジ保存

**起動タイミング**: 「ナレッジを保存して」「セッション終了」/ `.capture-needed` フラグがある場合

セッションで得た知見を適切なメモリ層に振り分けて保存するメタスキル。

**保存先の決定木**:

```
一回限りの設計判断（なぜこの設計にしたか）
  → docs/decisions/[YYYYMMDD]-[slug].md（ADR形式）

現在タスク固有の決定（再利用性が低い）
  → .steering/[task]/decisions.md（追記）

複数回再利用できるパターン・アンチパターン
  → docs/knowledge/[topic].md
  → CLAUDE.md に @参照を追記

Claude Code の短い常時ルール（1行の命令形）
  → CLAUDE.md（≤200行 厳守）

語彙・用語
  → docs/glossary.md
```

ドラフトをユーザーに確認してから書き込む（自動書き込みしない）。
保存完了後に `.capture-needed` を削除し `capture_done` を作成。

---

#### `empirical-prompt-tuning` — プロンプト品質改善

**起動タイミング**: スキル / プロンプトを新規作成・大幅改訂した直後 / エージェントの挙動が期待通りにならないとき

書き手バイアスを排除するため、**新規のサブエージェントに実際に動かしてもらい両面（実行者の自己申告 + 指示側メトリクス）で評価**する手法。改善が頭打ちになるまで反復する。

**ワークフロー**:

```
0. description と body の整合チェック（静的）
1. シナリオ設計（典型ケース × 1 + エッジケース × 1〜2）
2. 新規 subagent へ dispatch（同一 agent の再利用禁止）
3. レポート収集（自己申告の不明瞭点・裁量補完・再試行）
4. 両面評価（質的を主、量的を補助）
5. 最小修正を適用（1 イテレーション 1 テーマ）
6. 新規 subagent で再評価 → 2 に戻る
7. 連続 2 回で新規不明瞭点ゼロかつメトリクス飽和 → 停止
```

**評価軸**: 成功/失敗 / 精度 / ステップ数 / 所要時間 / 再試行回数 / 不明瞭点（自己申告）/ 裁量補完箇所（自己申告）

---

## インフラ・設定

### Stop Hook（セッション終了時の自動ログ）

`.claude/hooks/session-stop.sh` がセッション終了時に自動実行される。

**動作**:
1. `.steering/` のアクティブタスク全てに対して `git diff HEAD --stat` + `git status --short` を取得
2. 前回と同じ内容なら記録しない（重複抑制）
3. `.steering/[task]/session-log.md` に追記（タイムスタンプ付き）
4. `capture_done` がなく `.capture-needed` もない場合は `.capture-needed` フラグを作成してリマインドを出力

### settings.json（パーミッション設定）

以下の操作を自動 deny に設定してある:

**パッケージインストール系**: `pnpm add/remove/install`, `npm install/ci`, `yarn add/install`, `bun add/install`

**機密情報漏洩防止**: `cat .env*`, `grep * .env*`

**破壊的 git 操作**: `git push --force`, `git reset --hard`, `git clean -f`

**その他**: `rm -rf *`

---

## CLAUDE.md のルール（抜粋）

### セッション開始時

1. `find .steering -name '.capture-needed' 2>/dev/null` を実行
2. `.capture-needed` があれば「前回セッションのナレッジが未保存です。knowledge-capture を実行しますか？」と確認
3. `.steering/` のアクティブタスクをすべて読んでから作業開始
4. 複数のアクティブタスクがある場合はどれを再開するか確認

### スタック制約

- `vi.mock` でネットワーク系のモックは禁止（MSW の `http.*` を使う）
- RTL クエリ: `role > label > text > testId` の優先順位を守る
- Playwright: `waitForTimeout` 禁止
- `as any` / `as unknown` の不用意な使用禁止
- `<div onClick>` → `<button>` に置き換える

### ナレッジ保存先

| 種類 | 保存先 |
|---|---|
| 行動ルール（短い命令形） | CLAUDE.md |
| 経験・パターン・アンチパターン | `docs/knowledge/[topic].md` |
| 設計判断（ADR） | `docs/decisions/[date]-[slug].md` |
| タスク固有の決定 | `.steering/[task]/decisions.md` |

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
