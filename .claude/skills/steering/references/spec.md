# .steering/ 仕様詳細

## ディレクトリ構造

```
.steering/
├── [YYYYMMDD]-[task-name]/    ← 進行中タスク
│   ├── requirements.md        ← 必須: 要求・目標・スコープ
│   ├── design.md              ← 必須: 実装アプローチ（DRAFT → APPROVED）
│   ├── tasklist.md            ← 必須: チェックボックス形式のタスクリスト
│   ├── session-log.md         ← 自動生成: Stop hook が追記するセッション記録
│   ├── decisions.md           ← 任意: タスク固有の決定事項ログ
│   ├── blockers.md            ← 任意: 未解決の問題・依存待ち
│   ├── .capture-needed        ← フラグ: knowledge-capture 未実行を示す
│   └── capture_done           ← フラグ: knowledge-capture 完了済みを示す
└── archived/
    └── [YYYYMMDD]-[task-name]/  ← 完了タスク（git で永続管理）
```

## 各ファイルの役割

### requirements.md（必須）

何をするか・なぜするかを記述。セッションをまたいでも目的がブレないようにする。

```markdown
# Requirements: [task-name]

Created: [YYYYMMDD]

## Goal
[一段落: このタスクが達成することと理由]

## Scope
### In scope
- [項目]

### Out of scope
- [項目]

## Constraints
- Stack: Next.js / TypeScript / Vitest / React Testing Library / MSW / Playwright
- [その他の制約]

## Acceptance criteria
- [ ] [基準1]
- [ ] [基準2]
```

### design.md（必須）

**Status が DRAFT の間は実装に入らない。** 人間の承認後に APPROVED に変更する。

```markdown
# Design: [task-name]

Status: **DRAFT — awaiting review**

## Approach
[2〜4文: 核となる技術的な判断]

## Key components
| Component | Location | Responsibility |
|-----------|----------|----------------|
| [name] | `src/...` | [役割] |

## Data flow
[テキストまたは ASCII ダイアグラム]

## Test strategy
- Unit: [何をユニットテストするか]
- Integration: [必要な MSW ハンドラー]
- E2E: [Playwright シナリオ（あれば）]

## Open questions
- [ ] [人間のレビューが必要な質問]

## Alternatives considered
| Alternative | Why rejected |
|-------------|--------------|
| [代替案] | [却下理由] |
```

承認後:
```markdown
Status: **APPROVED**
Approved: [YYYYMMDD]
```

### tasklist.md（必須）

セッションのたびに更新する。チェックボックスが Claude の「現在地」を示す。

```markdown
# Tasklist: [task-name]

Last updated: [YYYYMMDD]

## Implementation
- [ ] [設計から導出したタスク]
- [ ] テスト作成（TDD: Red フェーズ）
- [ ] 実装（Green フェーズ）
- [ ] リファクタリング（Refactor フェーズ）

## Review
- [ ] frontend-code-review スキルの実行
- [ ] knowledge-capture スキルの実行
```

### session-log.md（自動生成）

Stop hook（`.claude/hooks/session-stop.sh`）が自動追記。Claude が次回セッション開始時に読む。

```markdown
---
## 2026-05-27 14:32 (task: user-auth-refresh)
 src/components/Login.tsx | 45 ++++++
 src/api/auth.ts          | 23 +++
 M src/components/Login.tsx
?? src/api/auth.ts
```

### decisions.md（任意）

タスク固有の決定事項。ADR（`docs/decisions/`）にする前の中間記録。

```markdown
## [YYYYMMDD] — [短いラベル]

**Decision**: [決定内容]
**Reason**: [なぜ]
**Impact**: [今後に影響すること]
```

### blockers.md（任意）

解決待ちの問題。次のセッションで見逃さないように記録する。

```markdown
## [YYYYMMDD] — [ブロッカーの内容]

**Status**: OPEN / RESOLVED
**Waiting for**: [誰・何を待っているか]
**Resolution**: [解決したら記入]
```

## セッション開始コントラクト

CLAUDE.md に記述済み。毎セッション:
1. `find .steering -name '.capture-needed' 2>/dev/null` を実行
2. `.capture-needed` があれば knowledge-capture を促す
3. アクティブタスクの context を読む
4. 複数タスクがあれば優先度を確認

## アーカイブポリシー

**完了後も削除しない。git で永続管理を推奨。**

理由:
- 意思決定ログとして残る
- 類似タスクのたたき台になる
- 障害時に当時の設計意図を遡れる

`tasklist.md` が全チェック済みになったら `archived/` へ移動。
直近3件は `steering status` で表示される。
