# .steering/ ファイルテンプレート集

`design-doc` スキルが `.steering/[YYYYMMDD]-[task]/` を初期化する際に使うテンプレート。

---

## requirements.md テンプレート

```markdown
# Requirements: [task-name]

Created: [YYYYMMDD]

## Goal

[一段落: このタスクが達成することと、なぜ必要か]

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

---

## design.md テンプレート

```markdown
# Design: [task-name]

Status: **DRAFT — awaiting review**

## Approach

[2〜4文: 核となる技術的な判断と理由]

## Key components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| [name] | `src/...` | [役割] |

## Data flow

[テキストまたは ASCII ダイアグラムでデータ・イベントの流れを説明]

## Test strategy

- Unit: [何をユニットテストするか、vitest]
- Integration: [必要な MSW ハンドラー]
- E2E: [Playwright シナリオ（あれば）]

## Open questions

- [ ] [人間のレビューが必要な質問や不明点]

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| [代替案] | [却下理由] |

## Research

[インシデントや未知の技術を調査した場合、その結果をここに記載]
```

---

## tasklist.md テンプレート

```markdown
# Tasklist: [task-name]

Last updated: [YYYYMMDD]

## Implementation

- [ ] [design.md の Key components から導出したタスク]
- [ ] [タスク2]
- [ ] テスト作成（TDD Red フェーズ）
- [ ] 実装（TDD Green フェーズ）
- [ ] リファクタリング（TDD Refactor フェーズ）

## Review

- [ ] frontend-code-review の実行
- [ ] レビュー指摘の修正（review-result.md を参照）
- [ ] 修正後の再確認

## Deploy
<!-- git push してブランチを PR にするフェーズ。CI がないリポジトリはスキップ可。 -->
<!-- GitHub Actions 等があれば CI グリーンを確認してからマージする。 -->

- [ ] PR 作成（`pr-create` スキルまたは `gh pr create`）
- [ ] CI グリーン確認
- [ ] マージ

## Compound
<!-- レビュー・実装で発見したパターンをルール・知識・スキルに昇格するフェーズ。 -->
<!-- frontend-code-review 完了後に .codify-needed フラグが作成される。 -->

- [ ] compound スキルの実行（パターンをルール・知識に昇格）

## Knowledge
<!-- セッションの知見を docs/ に永続保存するフェーズ。 -->
<!-- .capture-needed フラグが次セッション開始時のリマインダーになる。 -->

- [ ] knowledge-capture スキルの実行
- [ ] steering archive モードでアーカイブ
```

---

## decisions.md テンプレート（任意ファイル）

タスク固有の決定事項を記録する。

```markdown
# Decisions: [task-name]

## [YYYYMMDD] — [短いラベル]

**Decision**: [決定内容]
**Reason**: [なぜこの決定をしたか]
**Impact**: [今後に影響すること]
```

---

## review-result.md テンプレート（frontend-code-review が生成）

レビュー指摘とその修正状況を追跡する。

```markdown
# Review Result: [task-name]

Date: [YYYYMMDD]
Status: PENDING | IN_PROGRESS | RESOLVED

## Test

| Axis | 指摘 | ファイル | 分類 | 修正状況 |
|------|------|----------|------|----------|
| 実装エコー | [内容] | [file:line] | implementation bug | [ ] |
| MSW 規律 | [内容] | [file:line] | test was wrong | [ ] |

## Implementation

| Axis | 指摘 | ファイル | 修正状況 |
|------|------|----------|----------|
| 設計整合性 | [内容] | [file] | [ ] |
| TypeScript | [内容] | [file:line] | [ ] |

## Security

| 指摘 | ファイル | 修正状況 |
|------|----------|----------|
| [内容] | [file:line] | [ ] |

## Performance

| 指摘 | ファイル | 修正状況 |
|------|----------|----------|
| [内容] | [file:line] | [ ] |

## Accessibility

| 指摘 | ファイル | 修正状況 |
|------|----------|----------|
| [内容] | [file:line] | [ ] |

## サマリー

- 重要な問題: N件
- 修正完了: 0/N件
```

---

## blockers.md テンプレート（任意ファイル）

未解決の問題・依存待ちを記録する。

```markdown
# Blockers: [task-name]

## [YYYYMMDD] — [ブロッカーの内容]

**Status**: OPEN
**Waiting for**: [誰・何を待っているか]
**Resolution**: [解決したら記入]
```
