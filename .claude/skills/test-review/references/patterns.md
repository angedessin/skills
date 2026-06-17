# test-review カートリッジ — React / Vitest / React Testing Library / MSW

> **これはスタック固有の「機構」層**。SKILL.md 本文（判断エンジン）が役割名（§echo 等）で参照する具体例を集約する。
> 別スタック（Vue / Svelte / Jest / Playwright Component Testing 等）に横展開するときは、**このファイルを自分のスタック用に再生成して差し替える**。本文（SKILL.md）は触らない。
> example スタック: React 18+ / Vitest / @testing-library/react / MSW v2

---

## §echo — 実装エコー（Axis 1）

```typescript
// ❌ Bad: 内部 state をアサートしている
expect(component.state.isLoading).toBe(true)

// ❌ Bad: dispatch の引数をアサート（ユーザーには見えない）
expect(mockDispatch).toHaveBeenCalledWith({ type: 'SET_USER', payload: user })

// ❌ Bad: クラス名でアサート
expect(button).toHaveClass('btn-primary')
```

```typescript
// ✅ Good: ユーザーが見る動作をアサート
expect(screen.getByRole('progressbar')).toBeInTheDocument()
expect(await screen.findByText('Alice')).toBeInTheDocument()
expect(screen.getByRole('button')).toBeDisabled()
```

---

## §assertions — アサーション品質（Axis 2）

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

## §network-mocking — ネットワークモック境界（Axis 3）

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

**モジュールレベルのモック（`vi.mock`）が許容される対象**:
- DB・ファイルシステム・外部 SDK（HTTP を使わない）
- 日時・乱数など環境依存の値

**違反判定の基準**: `vi.mock` の対象が `fetch`・`axios` を呼ぶモジュール、または `api/`・`service/` 等の HTTP 通信を担うレイヤーの場合が違反対象。ファイル名だけで判断できない場合はモジュール内に `fetch`/`axios` 呼び出しがあるかを確認する。

---

## §queries — クエリ優先順位（Axis 4）

優先順位: `getByRole` > `getByLabelText` > `getByText` > `getByTestId`

```typescript
// ❌ Bad: セマンティクスを無視したクエリ
container.querySelector('.submit-button')
screen.getByTestId('submit-btn')

// ✅ Good: セマンティクスを活かしたクエリ
screen.getByRole('button', { name: /submit/i })
screen.getByLabelText('Email')
```

---

## §coverage-intent — カバレッジの意図（Axis 5）

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

---

## §scope — 対象ファイルの抽出（このスタックの規約）

```bash
git diff --name-only HEAD | grep -E '\.(test|spec)\.(ts|tsx)$'
```

別スタックではテストファイル命名規約を自分のものに置き換える（例: `*_test.go` / `*.spec.js` / `test_*.py`）。
