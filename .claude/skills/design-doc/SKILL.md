---
name: design-doc
description: "Use when starting a new feature, task, or incident investigation — phrases like 'let's build X', 'design a solution for Z', 'investigate incident N', 'start a new task', 'new feature'. Creates .steering/[YYYYMMDD]-[task-name]/ with requirements.md, design.md, and tasklist.md, then STOPS for mandatory human review of design.md before any implementation. Trigger on task-start signals even if the user does not say 'design doc'. Do NOT trigger when .steering/ context already exists for the current task — use steering (resume mode) instead. Do NOT trigger on 'add a test' or 'fix a small bug' when no design is needed."
---

# Design Doc

新しいタスクの `.steering/` コンテキストをブートストラップし、設計ドキュメントを作成する。
**design.md 作成後は必ず止まって人間のレビューを待つ。実装には入らない。**

## When NOT to use

- 現在のタスクの `.steering/` ディレクトリがすでに存在する → `steering`（resume モード）を使う
- 設計フェーズが不要な 30 分以内のバグ修正 → そのまま実装
- テスト追加のみ → `tdd` スキルを直接使う

---

## Phase 1 — コンテキストを確認する

1. ユーザーのリクエストから以下を判断:
   - **種別**: 新機能 / インシデント調査 / リファクタリング / その他
   - **タスク名**: kebab-case、≤5 words（例: `user-auth-refresh-flow`）
   - **日付**: 今日（YYYYMMDD 形式）

2. `.steering/` の既存アクティブタスクを確認:
   ```bash
   find .steering -maxdepth 1 -mindepth 1 -type d ! -name "archived" 2>/dev/null
   ```
   アクティブタスクがあれば「既存タスク [name] があります。新しいタスクとして続けますか？」と確認。

---

## Phase 2 — .steering/ を初期化する

`.steering/[YYYYMMDD]-[task-name]/` ディレクトリと以下の3ファイルを作成する。
テンプレートの全文は `references/templates.md` を参照。

### 作成するファイル

**`requirements.md`** — ユーザーのリクエストから要求を整理
- Goal: 何を達成するか（1段落）
- Scope: In / Out of scope
- Constraints: スタック・制約事項
- Acceptance criteria: 完了条件（チェックボックス）

**`design.md`** — 実装アプローチを設計（Status: DRAFT）
- Approach: 核となる技術判断（2〜4文）
- Key components: コンポーネント・ファイル一覧テーブル
- Data flow: データ・イベントの流れ
- Test strategy: Unit / Integration / E2E の方針
- Open questions: 人間のレビューが必要な質問（重要）
- Alternatives considered: 却下した代替案

**`tasklist.md`** — design.md から導出したタスクのチェックリスト
- 実装タスク（チェックボックス）
- TDD / test-review / knowledge-capture の実行チェック

### インシデント・未知領域の場合

インシデントや不明な技術が含まれる場合は Phase 2 の前に調査を行う:
- 「実装前に調査しますか？関連するファイルや情報を教えてください」と確認
- 調査結果は `design.md` の `## Research` セクションに記載

---

## Phase 3 — STOP（必須）

`design.md` を作成したら必ず以下のメッセージを表示して止まる:

```
設計ドキュメントを作成しました。

📄 .steering/[date]-[task]/design.md

**実装に入る前に design.md をレビューしてください。**
特に「Open questions」セクションの確認をお願いします。

承認する場合は「承認」または「approved」と入力してください。
修正がある場合はその内容を教えてください。
```

**このメッセージの後は何も実装しない。ユーザーの応答を待つ。**

---

## Phase 4 — 承認後の処理

ユーザーが承認したら:

1. `design.md` の Status を更新:
   ```
   Status: **APPROVED**
   Approved: [YYYYMMDD]
   ```

2. 次のステップを案内:
   ```
   設計が承認されました。

   次は `impl-from-design` スキルで実装を開始できます。
   TDD モード（推奨）と Impl-first モードを選べます。
   ```

---

## セッション継続の場合

`.steering/` がすでに存在するタスクを再開するとき:
1. `requirements.md`・`design.md`・`tasklist.md` を読む
2. 現状をユーザーに要約して伝える
3. 「何から続けますか？」と確認

---

## Related skills

- `steering` — `.steering/` のライフサイクル全体（resume / archive / status）
- `impl-from-design` — 設計承認後の実装フェーズ
- `knowledge-capture` — セッション終了時の知見保存
