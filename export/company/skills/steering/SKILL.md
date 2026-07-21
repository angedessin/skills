---
name: steering
description: ".steering/ クロスセッションコンテキスト管理のメタスキル。「new task」「start steering」「[task] を再開」「[task] をアーカイブ」「steering status」「進行中タスクは？」と明示的に言われた場合のみ起動。通常のセッション開始で .steering/ を読むだけの場合や design-doc がコンテキスト設定を担っている場合は自動起動しない。"
metadata:
  version: "1.0"
  source-commit: df027219393941e5a3e80cd2a9e8a4baa26f0b19
---

# Steering

`.steering/` ディレクトリのライフサイクルを管理するインフラスキル。
設計・実装ワークフローから独立した独立ツール。
<!-- validator: no-stop-needed — 本文の「APPROVED」は design.md の Status 値の引用（例示・表示）であり、このスキル自身は承認ゲートを持たない。承認を伴う停止は design-doc / impl-from-design の担当。 -->

## When NOT to use

- `design-doc` スキルが新機能タスクを開始しているとき（そちらが `.steering/` の初期化を担当）
- 通常のセッション開始で `.steering/` を読むだけのとき（読む → 普通に作業）
- 別のスキルがすでに `.steering/` を管理しているとき

## ディレクトリ構造

```
.steering/
├── [YYYYMMDD]-[task-name]/
│   ├── design.md           (必須 — 目的/スコープ/完了条件を含む。APPROVED になるまで実装禁止)
│   ├── tasklist.md         (必須 — セッションごとに更新)
│   ├── decisions.md        (任意 — タスク固有の決定事項)
│   ├── blockers.md         (任意 — 未解決の問題)
│   ├── skill-issues.md     (任意 — スキル自体の不具合記録。compound が読む)
│   ├── investigation.md    (任意 — 障害調査ログ: 仮説・検証・棄却理由)
│   ├── review-result.md    (frontend-code-review が生成)
│   ├── codify-log.md       (compound が生成 — 昇格履歴)
│   ├── .capture-needed     (フラグ — knowledge-capture 未実行)
│   ├── .codify-needed      (フラグ — compound 未実行)
│   └── capture_done        (フラグ — knowledge-capture 完了済み)
└── archived/
    └── [YYYYMMDD]-[task-name]/   (完了タスク)
```

旧構造のタスク（`requirements.md`・`session-log.md` がある）は読み取り時のみ対応する: あれば読む、新規には作らない。

詳細仕様: `references/spec.md`

---

## モード: init

**トリガー**: "新しいタスク"、"steering を始める"、直接呼び出し

1. ユーザーと確認してタスク名を決定（kebab-case、≤5 words）
2. 日付は今日（YYYYMMDD 形式）
3. `.steering/[YYYYMMDD]-[task-name]/` を作成
4. 以下のファイルをテンプレートから生成:
   - `design.md`（Status: DRAFT — 目的 / スコープ / 完了条件を含む）
   - `tasklist.md`
5. 作成したパスを報告

**注**: 新機能タスクには `design-doc` スキルを使うこと（こちらの方が詳細なフロー）。
`steering init` は軽量なコンテキスト設定用。

---

## モード: resume

**トリガー**: "再開"、"[task] の続き"、新セッションで `.steering/` あり

1. `.steering/` のアクティブタスク一覧（`archived/` 除外）を確認
2. 対象タスクの以下を読む:
   - `design.md`（目的・設計と Status。旧構造で `requirements.md` があればそれも読む）
   - `tasklist.md`（進捗確認）
   - `blockers.md`（なければ「なし」として扱う）
   - `decisions.md`（なければ「記録なし」として扱う）
3. セッションサマリーを表示:

```
## セッション再開: [task-name]

**目的**: [design.md の目的から一行]
**設計**: DRAFT / APPROVED
**進捗**: X/Y tasks チェック済み

### 残タスク
- [ ] [未チェックの項目]

### ブロッカー
[blockers.md の内容、なければ "なし"]

### 最新の決定事項
[decisions.md の最後のエントリ、なければ "記録なし"]
```

4. 「何から始めますか？」と確認

---

## モード: status

**トリガー**: "steering status"、"進行中のタスクは？"

アクティブタスクの一覧テーブルを表示:

```
## ステアリング状況

### アクティブタスク
| タスク | 作成日 | Design | 進捗 |
|--------|--------|--------|------|
| [name] | [date] | APPROVED | 3/7 |
| [name] | [date] | DRAFT | 0/5 |

### アーカイブ済み（直近3件）
- [name] — archived [date]
```

進捗は `tasklist.md` のチェック済み / 全チェックボックス数から計算。

---

## モード: archive

**トリガー**: "[task] を完了"、"アーカイブして"、knowledge-capture 実行後

**アーカイブ前チェック**:
- [ ] `tasklist.md` の全項目がチェック済み
- [ ] `knowledge-capture` スキルが実行済み（または明示的に省略を確認）

チェックを満たしている場合:
1. `.steering/[date]-[task]` を `.steering/archived/[date]-[task]` に移動
2. `tasklist.md` の末尾に `Archived: [YYYYMMDD]` を追記
3. 「アーカイブ完了。`.steering/archived/[task]` に保存されました。」と報告

チェックが不足している場合は、不足している項目をリストして確認を求める。
ユーザーが「省略してアーカイブ」と明示した場合は未チェック項目をスキップしてアーカイブを実行する。

**knowledge-capture 実行済みの判定**: `capture_done` フラグが存在するか、または `tasklist.md` の knowledge-capture チェックボックスがチェック済みであれば OK（どちらか一方で十分）。

---

## ファイル命名規則

- タスク名: kebab-case、≤5 words、具体的（NG: `task-1` / OK: `user-auth-refresh`）
- 日付: タスク作成時の YYYYMMDD（アーカイブ時も変えない）

## Related skills

- `design-doc` — 新機能タスクの主要な入口（.steering/ の詳細なフロー付き）
- `knowledge-capture` — アーカイブ前に実行が推奨
- `impl-from-design` — 実装フェーズで tasklist.md を更新
