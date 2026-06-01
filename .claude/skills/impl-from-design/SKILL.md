---
name: impl-from-design
description: "承認済みデザインドキュメントに基づく実装に使う — 「実装を開始して」「設計から実装して」「設計が承認された、作ろう」などのフレーズが対象。.steering/[task]/design.md の Status が APPROVED である必要がある。design.md がない・DRAFT の場合は design-doc にリダイレクト。.steering/ コンテキストなしの汎用「実装して」リクエストには起動しない。"
---

# Impl from Design

承認済みの `design.md` を元に実装を進める。
TDD（デフォルト・推奨）と Impl-first モードの両方に対応。

## When NOT to use

- `.steering/` が存在しない → `design-doc` スキルから始める
- `design.md` の Status が `DRAFT` → 設計レビューを先に完了させる
- テストのみを追加したい → `tdd` スキルを直接使う

---

## Step 1 — 前提チェック

```bash
# アクティブタスクの確認
find .steering -maxdepth 1 -mindepth 1 -type d ! -name "archived" 2>/dev/null
```

対象タスクの `design.md` を読み、Status を確認する:
- `APPROVED` → 続行
- `DRAFT` → 止まる: "design.md がまだ DRAFT です。`design-doc` スキルで設計レビューを完了してください。"

`tasklist.md` も読んで実装スコープを把握する。

---

## Step 1.5 — 既存コードベースの調査（code-explorer）

新規コンポーネント作成 or 既存の複雑なファイルへの変更を含む場合に実行する。
単純な定数追加・typo 修正の場合はスキップしてよい（ユーザーに確認して省略可）。

`feature-dev:code-explorer` を起動して以下を調査する:
- 実装対象に近い既存コードのパターン・規約
- `design.md` の Key components が既存コードとどう繋がるか
- プロジェクト固有の書き方（fetch のラッパー・エラーハンドリング・状態管理など）

**探索結果の記録**: 調査結果を `design.md` の `## Research` セクションに追記する。
セッションをまたいでも参照できるように揮発させない。

```
## Research

### 既存パターン調査（[YYYYMMDD]）
- [パターン名]: [観察した規約・実装場所]
- 注意点: [実装時に合わせるべき点]
```

調査結果をユーザーに提示してから実装モードの選択に進む。

---

## Step 2 — モード選択

実装開始前にユーザーに確認する:

```
実装モードを選んでください:

1. TDD モード（推奨）— テストを先に書いてから実装
   Red（失敗テスト）→ Green（最小実装）→ Refactor

2. Impl-first モード — 実装してからテストを追加
   実装 → テスト追加 → レビュー

どちらで進めますか？（デフォルト: 1）
```

---

## TDD モード（モード1）

`tasklist.md` の実装タスクを1つずつ処理する。

### 各タスクのサイクル

**Red — 失敗するテストを書く**

TDD のパターンは `.claude/skills/tdd/references/patterns.md` を参照。
- テストファイルに失敗するテストを記述
- 実行して「正しい理由」で失敗することを確認:
  ```bash
  npx vitest run [テストファイルパス]
  ```
- コンパイルエラーで失敗している場合は Red ではない（型・import を先に修正）

**Green — 最小実装でパスさせる**

- テストを通す最小限のコードを書く（過剰実装しない）
- 実行してグリーンを確認:
  ```bash
  npx vitest run [テストファイルパス]
  ```

**Refactor — テストが緑のまま整理する**

- 重複・命名・構造を改善
- 変更のたびに再実行して緑を維持

**サイクル完了後**: `tasklist.md` の該当項目をチェック済みにする

---

## Impl-first モード（モード2）

`design.md` の Key components テーブルを見て実装を進める。

1. Key components のコンポーネントを上から順に実装
2. 各コンポーネント完了後:
   - 「このコンポーネントのテストを書きますか？」と確認
   - Yes → `tdd` スキルのパターン（`.claude/skills/tdd/references/patterns.md`）を参照してテストを追加
3. `tasklist.md` を更新

---

## 実装中の判断ルール

### design.md との乖離が生じた場合

実装中に設計通りに進められないことが判明したら:
1. 止まってユーザーに報告
2. `design.md` の Open questions に追記
3. ユーザーの判断を待つ（勝手に設計変更しない）

### decisions.md への記録

実装中に重要な技術的判断をした場合は `.steering/[task]/decisions.md` に追記:
```markdown
## [YYYYMMDD] — [判断の内容]
**Decision**: [何を決めたか]
**Reason**: [なぜ]
**Impact**: [影響範囲]
```

---

## 完了後

すべての実装タスクが完了したら:

1. `tasklist.md` の実装セクションをすべてチェック済みにする
2. 次のステップを案内:
   ```
   実装が完了しました。

   次: `frontend-code-review` スキルでレビューを実行してください。
   （test-review + impl-review を順番に実行します）
   ```

---

## Related skills

- `design-doc` — この前に実行する設計フェーズ
- `tdd` — TDD パターンの単独ユーティリティ（既存コードへのテスト追加など）
- `frontend-code-review` — 実装完了後のレビュー（オーケストレーター）
- `steering` — tasklist.md の更新・セッション管理
