---
name: test-review
description: "Next.js/TypeScript/Vitest/React Testing Library プロジェクトのテストコード品質レビューに使う — 「テストをレビューして」「テストの品質を確認して」「このテストは良い？」「実装エコー」「アサーションが悪い」などのフレーズが対象。確認内容: 実装結合・アサーション品質・MSW 規律・RTL クエリ優先順位・カバレッジ意図。単独または frontend-code-review の Step 1 として動作。テストインフラの監査（vitest 設定・カバレッジツール設定）には起動しない。"
---

# Test Review

テストコードの品質審査。テストの行数やカバレッジ率ではなく、**テストが正しく機能しているか**を確認する。

## When NOT to use

- テストインフラ（vitest 設定・カバレッジ統合・Playwright 設定）の監査 → `.tmp/skills` の `frontend-review-testing`
- 新しいテストを書く → `tdd`

---

## スコープの決定

デフォルト: `git diff --name-only HEAD` で変更された `*.test.ts`・`*.spec.ts`・`*.test.tsx` ファイル。
ユーザーが特定のファイルやディレクトリを指定した場合はそちらを優先。

```bash
git diff --name-only HEAD | grep -E '\.(test|spec)\.(ts|tsx)$'
```

スコープが空の場合（変更されたテストファイルが 0 件）は「テストレビューの対象ファイルがありません」と出力して終了する。5つのレビュー軸のチェックは行わない。

---

## 5つのレビュー軸

### Axis 1 — 実装エコー（最重要）

実装エコーとは「内部の実装方法をアサートするテスト」。リファクタリングしても壊れず、実装が間違っていても通ってしまう。

**レッドフラグ**:

```typescript
// ❌ Bad: 内部 state をアサートしている
expect(component.state.isLoading).toBe(true)

// ❌ Bad: dispatch の引数をアサートしている（ユーザーには見えない）
expect(mockDispatch).toHaveBeenCalledWith({ type: 'SET_USER', payload: user })

// ❌ Bad: クラス名でアサートしている
expect(button).toHaveClass('btn-primary')
```

```typescript
// ✅ Good: ユーザーが見る動作をアサート
expect(screen.getByRole('progressbar')).toBeInTheDocument()
expect(await screen.findByText('Alice')).toBeInTheDocument()
expect(screen.getByRole('button')).toBeDisabled()
```

---

### Axis 2 — アサーション品質

**具体性のないアサーション**:

```typescript
// ❌ Bad: 何でも true
expect(result).toBeTruthy()
expect(mockFn).toHaveBeenCalled()

// ✅ Good: 具体的な値
expect(result).toEqual({ id: 1, status: 'active' })
expect(mockFn).toHaveBeenCalledWith({ userId: '42' })
```

**非同期アサーション**:

```typescript
// ❌ Bad: Promise を直接アサート（常に truthy）
expect(screen.findByText('Done')).toBeTruthy()

// ✅ Good: await で待つ
expect(await screen.findByText('Done')).toBeInTheDocument()
await waitFor(() => expect(mockFn).toHaveBeenCalled())
```

---

### Axis 3 — MSW 規律

ネットワーク呼び出しをするモジュールを `vi.mock` でモックしていないか確認する。

```typescript
// ❌ Bad: vi.mock でネットワーク層をモック（統合契約が壊れても気づかない）
vi.mock('../api/user', () => ({
  getUser: vi.fn().mockResolvedValue({ id: 1 })
}))

// ✅ Good: MSW で HTTP 境界のみモック
server.use(
  http.get('/api/user', () => HttpResponse.json({ id: 1 }))
)
```

`vi.mock` が許容される場合:
- DB・ファイルシステム・外部 SDK（HTTP を使わない）
- 日時・乱数など環境依存の値

**違反判定の基準**: `vi.mock` の対象が `fetch`・`axios` を呼ぶモジュール、または `api/`・`service/` 等の HTTP 通信を担うレイヤーの場合が違反対象。ファイル名だけで判断できない場合はモジュール内に `fetch`/`axios` 呼び出しがあるかを確認する。

---

### Axis 4 — RTL クエリ優先順位

優先順位: `getByRole` > `getByLabelText` > `getByText` > `getByTestId`

```typescript
// ❌ Bad: セマンティクスを無視したクエリ
container.querySelector('.submit-button')
screen.getByTestId('submit-btn')
screen.getByClassName('btn')

// ✅ Good: セマンティクスを活かしたクエリ
screen.getByRole('button', { name: /submit/i })
screen.getByLabelText('Email')
```

---

### Axis 5 — カバレッジの意図

テストが存在する意味を持っているか確認する。

**低価値なテストパターン**:

```typescript
// ❌ Bad: レンダリングするだけ（何も検証しない）
it('renders without error', () => {
  render(<MyComponent />)
  // アサーションなし
})

// ❌ Bad: 実装のコピー
it('returns the sum', () => {
  expect(add(1, 2)).toBe(1 + 2) // 実装と同じ計算をしている
})
```

**良いテストの基準**:
- 仕様をエンコードしている（意図した動作を表現している）
- 壊れたら本当のバグを教えてくれる

---

## トリアージ分類

問題のあるテストを以下に分類する:

| 分類 | 意味 | 対処 |
|------|------|------|
| spec changed | 実装は正しい、テストが古い | テストを更新 |
| implementation bug | テストは正しい、実装が間違っている | 実装を修正 |
| test was wrong | テストが最初から仕様と合っていない | テストを書き直す |
| low-value | 存在価値が低い | 削除または拡充 |

---

## 出力形式

```
## Test Review: [スコープ（ファイルまたはディレクトリ）]

### Axis 1 — 実装エコー
- [file.test.ts:L42] mockDispatch の引数をアサート → `screen.findByText` で結果を確認すべき **[implementation bug]**

### Axis 2 — アサーション品質
- [file.test.ts:L18] `toBeTruthy()` → `toEqual({ id: 1 })` に変更 **[spec changed]**

### Axis 3 — MSW 規律
（問題なし）

### Axis 4 — RTL クエリ
- [file.test.tsx:L33] `getByTestId('btn')` → `getByRole('button', { name: /submit/i })` **[test was wrong]**

### Axis 5 — カバレッジの意図
- [file.test.tsx:L5] renders without error のみ → 主要インタラクションのアサーションを追加 **[low-value]**

### サマリー
- 確認したテストファイル: N件
- 重要な問題: X件
- 推奨修正: [修正内容の要点]
```

**提案のみ。自動修正しない。** ユーザーの承認後に修正を実施する。

---

## Related skills

- `tdd` — 問題のあるテストを書き直す
- `impl-review` — テストコードではなく実装コードをレビューする
- `frontend-code-review` — test-review と impl-review を順番に実行するオーケストレーター
