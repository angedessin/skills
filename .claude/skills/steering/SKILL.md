---
name: steering
description: ".steering/ クロスセッションコンテキスト管理のメタスキル。「new task」「start steering」「[task] を再開」「[task] をアーカイブ」「steering status」「進行中タスクは？」と明示的に言われた場合のみ起動。通常のセッション開始で .steering/ を読むだけの場合や design-doc がコンテキスト設定を担っている場合は自動起動しない。"
metadata:
  version: "1.4"
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
│   ├── design.md           (必須 — 契約コアに目的/スコープ/完了条件等。DRAFT のみ実装禁止。SPIKE/APPROVED は実装可（SPIKE は外向き不可）。付録は境界マーカー以降)
│   ├── tasklist.md         (必須 — セッションごとに更新)
│   ├── decisions.md        (任意 — タスク固有の決定事項)
│   ├── blockers.md         (任意 — 未解決の問題)
│   ├── skill-issues.md     (任意 — スキル自体の不具合記録。compound が読む)
│   ├── investigation.md    (任意 — debug が生成: 障害調査ログ)
│   ├── review-result.md    (frontend-code-review が生成)
│   ├── codify-log.md       (compound が生成 — 昇格履歴)
│   ├── .capture-needed     (フラグ — knowledge-capture 未実行)
│   ├── .codify-needed      (フラグ — compound 未実行)
│   ├── pr_capture_done     (フラグ — PR 差分に属する知見の保存済み。アーカイブ条件ではない)
│   └── capture_done        (フラグ — 最終 knowledge-capture 完了済み。アーカイブのハードストップはこちら)
└── archived/
    └── [YYYYMMDD]-[task-name]/   (完了タスク)
```

旧構造のタスク（`requirements.md`・`session-log.md` がある）は読み取り時のみ対応する: あれば読む、新規には作らない。

**Status 読み取り規則**: `Status:` 行の最初の語彙トークン（`**` を除く）∈ {DRAFT,SPIKE,APPROVED}。以外・欠落は停止。
**実装可否の正本**: DRAFT のみ実装禁止。SPIKE/APPROVED は実装可（SPIKE は外向き不可）。詳細は `references/spec.md`。

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

**`.steering/` ディレクトリ自体が無い場合**（このプロジェクトでまだ一度も使っていない）→ その旨を伝えて終了する。再開する対象が存在しないため、**勝手に `.steering/` を作らない**（新規タスクの開始は init モード、または `design-doc` の担当）。アクティブタスクが 0 件の場合も同じ。

1. `.steering/` のアクティブタスク一覧（`archived/` 除外）を確認
2. 対象タスクの以下を読む:
   - `design.md`（**契約コアまで**を既定。`<!-- design-doc-boundary: appendix -->` より前の
     目的・設計と Status。マーカーが無い旧ファイルは全文。旧構造で `requirements.md` があればそれも読む。
     **操作定義**: ツールがファイル全文を返しても必須入力は境界より前に限定する。可能なら `Read` の
     `limit` で境界行まで取得する。付録を要約・推論に使ってはならない）
   - `tasklist.md`（進捗確認）
   - `blockers.md`（なければ「なし」として扱う）
   - `decisions.md`（なければ「記録なし」として扱う）
3. セッションサマリーを表示:

```
## セッション再開: [task-name]

**目的**: [design.md の目的から一行]
**設計**: DRAFT / SPIKE / APPROVED
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

**`.steering/` ディレクトリ自体が無い場合** → 「このプロジェクトでは `.steering/` を使っていません」と伝えて終了する（エラーにしない・**作らない**）。ディレクトリはあるがアクティブタスクが 0 件の場合は、アーカイブ済みの直近 3 件だけを表示する。

アクティブタスクの一覧テーブルを表示:

```
## ステアリング状況

### アクティブタスク
| タスク | 作成日 | Design | 進捗 |
|--------|--------|--------|------|
| [name] | [date] | APPROVED | 3/7 |
| [name] | [date] | SPIKE | 1/5 |
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
- [ ] knowledge-capture **ハードストップ**（下記充足判定）

**knowledge-capture 充足判定（ハードストップ）**:
- **充足**: `capture_done` が存在する、またはユーザーが「知見なしでアーカイブ」と明示した
- **非充足**: 上記どちらも無い → **ここで止まる**。アーカイブ手順に進まない。knowledge-capture を**最終 capture として**（呼び出し時に「アーカイブ前の最終」と指定して）実行するか、「知見なしでアーカイブ」と明示するかを聞く。マージ前にアーカイブするタスク（デプロイ項目が未チェックのまま）でも、最終と指定すれば `capture_done` が立つ
- **非充足のままでは通さないもの**: 汎用「省略してアーカイブ」、`tasklist.md` の knowledge-capture `[x]` 単独、`pr_capture_done` 単独（PR 前の分だけで、最終 capture が済んでいない）

チェックを満たしている場合:
1. `.steering/[date]-[task]` を `.steering/archived/[date]-[task]` に移動
2. `tasklist.md` の末尾に `Archived: [YYYYMMDD]` を追記
3. 「アーカイブ完了。`.steering/archived/[task]` に保存されました。」と報告

knowledge-capture 以外のチェックが不足している場合は、不足項目をリストして確認を求める。
ユーザーが「省略してアーカイブ」と明示した場合は、**knowledge-capture ゲート以外**の未チェック項目をスキップしてアーカイブを実行する（knowledge-capture 未充足なら依然としてここで止まる）。

---

## ファイル命名規則

- タスク名: kebab-case、≤5 words、具体的（NG: `task-1` / OK: `user-auth-refresh`）
- 日付: タスク作成時の YYYYMMDD（アーカイブ時も変えない）

## Related skills

- `design-doc` — 新機能タスクの主要な入口（.steering/ の詳細なフロー付き）
- `knowledge-capture` — アーカイブ前ハードストップ（`capture_done` または「知見なしでアーカイブ」）
- `impl-from-design` — 実装フェーズで tasklist.md を更新
