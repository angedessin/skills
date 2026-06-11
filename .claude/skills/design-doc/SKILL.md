---
name: design-doc
description: "新機能・タスク開始・障害調査に使う — 「Xを作ろう」「Zの設計をして」「新しいタスク」などのフレーズが対象。複数セッションにまたがる見込みのタスクには .steering/[YYYYMMDD]-[task-name]/ に design.md・tasklist.md を作成し、design.md 作成後は必ず停止して人間のレビューを待つ（実装に入らない）。1セッションで終わる見込みのタスクは .steering を作らず会話内で設計確認する。「design doc」と言われなくてもタスク開始のシグナルがあれば起動する。現在タスクの .steering/ が既に存在する場合は steering（resume モード）を使う。テスト追加のみや小さなバグ修正では起動しない。"
---

# Design Doc

新しいタスクの `.steering/` コンテキストをブートストラップし、設計ドキュメントを作成する。
**design.md 作成後は必ず止まって人間のレビューを待つ。実装には入らない。**

## When NOT to use

- 現在のタスクの `.steering/` ディレクトリがすでに存在する → `steering`（resume モード）を使う
- **1セッションで完了する見込みのタスク** → `.steering/` を作らない。会話内で設計方針（Goal / Approach / 完了条件）を提示して承認を得てから実装する。`.steering/` は複数セッションにまたがる見込みのタスク専用（次セッションの自分が読まないファイルは作らない）
- 設計フェーズが不要な 30 分以内のバグ修正 → そのまま実装
- テスト追加のみ → `tdd` スキルを直接使う

作業の途中で複数セッションにまたがると判明した場合は、その時点で Phase 2 を実行し、会話内の設計内容を design.md に転記する。

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
   - ユーザーが **Yes** → Phase 2 に進み新しいタスクを初期化する
   - ユーザーが **No** → `steering` スキルの resume モードで既存タスクを再開するよう案内して終了する

---

## Phase 2 — .steering/ を初期化する

`.steering/[YYYYMMDD]-[task-name]/` ディレクトリと以下の2ファイルを作成する。
テンプレートの全文は `references/templates.md` を参照。ファイルが存在しない場合は、以下の各ファイルの説明に従って合理的に生成してよい（参照不要）。

### 作成するファイル

**`design.md`** — 要求の整理 + 実装アプローチ（Status: DRAFT）
- Goal: 何を達成するか・なぜ必要か（1段落）
- Scope: In / Out of scope
- Constraints: スタック・制約事項
- Acceptance criteria: 完了条件（チェックボックス）
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
1. `design.md`・`tasklist.md` を読む（旧構造のタスクに `requirements.md` があればそれも読む）
2. 現状をユーザーに要約して伝える
3. 「何から続けますか？」と確認

---

## 方針転換が起きた場合

実装中にスコープや技術選択が大きく変わったとき（採用ライブラリの変更・別スキルへの置き換え・scope の追加・削除など）は `design.md` を実態に合わせて更新する:

1. `design.md` の Approach / Key components / Alternatives considered を修正
2. `design.md` の Scope / Acceptance criteria を修正
3. `tasklist.md` の未完了タスクを実態に合わせて追記・削除

**更新しないと `.steering/` と実際の作業が乖離し、セッションをまたいだ再開時に混乱する。**

---

## Related skills

- `steering` — `.steering/` のライフサイクル全体（resume / archive / status）
- `impl-from-design` — 設計承認後の実装フェーズ
- `knowledge-capture` — セッション終了時の知見保存
