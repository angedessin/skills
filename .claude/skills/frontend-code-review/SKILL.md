---
name: frontend-code-review
description: "Use when reviewing code after implementation — phrases like 'review the code', 'let's review', 'code review', 'check the implementation'. Orchestrates test-review (test code quality) then impl-review (implementation quality + design alignment) in sequence, producing a combined summary. Use this as the default review entry point. Use test-review or impl-review directly only when you need a focused single-axis review."
---

# Frontend Code Review

`test-review` と `impl-review` を順番に実行するオーケストレーター。
`.tmp/skills` の `frontend-review-weekly` に相当する役割。

## When to use sub-skills directly

- テストコードのみを確認したい → `test-review` を直接使う
- 実装コードのみを確認したい → `impl-review` を直接使う
- このスキルはデフォルトの「レビューして」への対応

---

## Step 1 — スコープを確認する

レビュー対象を把握する:

```bash
# 変更されたファイルの一覧
git diff --name-only HEAD
```

ユーザーが特定のファイル・PR・ディレクトリを指定していれば、そちらを優先。

---

## Step 2 — test-review を実行する

以下の手順で `test-review` スキルの審査を行う。

**スコープ**: `git diff --name-only HEAD` の `*.test.ts`・`*.spec.ts`・`*.test.tsx`

5つの軸で確認する（詳細は `test-review` スキルを参照）:

1. **実装エコー**: 内部 state・クラス名・dispatch をアサートしていないか
2. **アサーション品質**: `toBeTruthy()` より具体的か、async は `findBy*`/`waitFor` を使っているか
3. **MSW 規律**: `vi.mock` でネットワーク系をモックしていないか
4. **RTL クエリ優先順位**: `querySelector`・`container.firstChild` を使っていないか
5. **カバレッジの意図**: render-only テストや実装コピーテストがないか

各問題をトリアージ分類（spec changed / implementation bug / test was wrong / low-value）する。

**この結果をバッファに保持して Step 3 に進む。**

---

## Step 3 — impl-review を実行する

以下の手順で `impl-review` スキルの審査を行う。

**スコープ**: `git diff --name-only HEAD` の `.ts`・`.tsx`（テストファイルを除く）

5つの軸で確認する（詳細は `impl-review` スキルを参照）:

1. **設計整合性**: `.steering/[task]/design.md` が存在すれば照合。Key components・Approach・Open questions
2. **プロジェクト規約**: `docs/knowledge/antipatterns.md` があれば照合。CLAUDE.md の制約も確認
3. **TypeScript 品質**: `as any`・非 null アサーション・`Record<string, any>` の不適切な使用
4. **React / Next.js パターン**: useEffect deps・Server/Client 境界・過剰な state
5. **アクセシビリティ（基本）**: `<div onClick>`・aria-label 欠落・`alt` 欠落

**この結果をバッファに保持して Step 4 に進む。**

---

## Step 4 — サマリーを出力する

両レビューの結果をまとめて出力:

```
## Code Review Summary

### Test Review
重要な問題: N件

| 軸 | 問題 | ファイル | 分類 |
|----|------|----------|------|
| 実装エコー | [内容] | [file:line] | implementation bug |
| MSW 規律 | [内容] | [file:line] | test was wrong |

### Implementation Review
重要な問題: M件

| 軸 | 問題 | ファイル |
|----|------|----------|
| 設計整合性 | [内容] | [file] |
| TypeScript | [内容] | [file:line] |

### 全体サマリー
- テスト問題: N件（重要: X件）
- 実装問題: M件（重要: Y件）

### 次のアクション
- [ ] [最優先で修正すべき問題]
- [ ] [次に修正すべき問題]
- knowledge-capture を実行して発見したパターンを `docs/knowledge/` に保存することを推奨
```

---

## 承認後の修正フロー

サマリーをユーザーが確認後:
- 修正が必要な項目を確認してから実施（自動修正しない）
- 修正後は該当のテストを再実行して確認
- `tasklist.md` のレビューチェックボックスを更新

深いレビューが必要な場合: `/code-review high` または `/code-review ultra` を追加で実行することを提案。

---

## Related skills

- `test-review` — テストコードのみを審査（単独利用可）
- `impl-review` — 実装コードのみを審査（単独利用可）
- `knowledge-capture` — レビューで発見したパターンを docs/ に保存
