---
name: tdd
description: "テストファースト開発や既存コードへのテスト追加に使う — 「テストを先に書いて」「TDD で」「レッド・グリーン・リファクタリング」「既存コードにテストを追加して」「失敗するテストを書いて」などのフレーズが対象。スタック: Vitest + React Testing Library + MSW（ユニット・インテグレーション）、Playwright（E2E）。設計ドキュメントなしで既存コードにテストを追加する場合に単独で使う。既存テストのレビューのみの場合は起動しない（test-review を使う）。"
---

# TDD

Red → Green → Refactor サイクル。
単独での使用（既存コードへのテスト追加）と `impl-from-design` からの参照の両方に対応。

## When NOT to use

- 既存テストの品質をレビューしたい → `test-review`
- `impl-from-design` が TDD モードで動いている → そちらに任せる

---

## サイクル

### Red — 失敗するテストを書く

テストを書いてから実行。**正しい理由** で失敗することを確認する。

```bash
npx vitest run path/to/the.test.ts
```

コンパイルエラーや import エラーで失敗している場合は Red ではない。
型・import を修正してから改めて Red を確認する。

### Green — 最小実装でパスさせる

テストを通す最小限のコードを書く。過剰実装は Refactor フェーズでやる。

```bash
npx vitest run path/to/the.test.ts
```

### Refactor — テストが緑のまま整理する

重複・命名・構造を改善する。変更のたびに再実行して緑を維持。

---

## パターン: Unit テスト

### 通常の describe/it 形式

```typescript
import { describe, it, expect } from 'vitest'
import { calculateTotal } from './cart'

describe('calculateTotal', () => {
  it('割引コードが有効な場合に割引を適用する', () => {
    expect(calculateTotal({ subtotal: 100, discountCode: 'SAVE10' })).toBe(90)
  })

  it('割引コードがない場合は小計をそのまま返す', () => {
    expect(calculateTotal({ subtotal: 100 })).toBe(100)
  })
})
```

### In-source testing（ロジックが重いユーティリティファイル向け）

本番ビルドではツリーシェイクされる。AI がソースとテストを1ファイルで把握できる利点がある。

```typescript
// src/lib/cart.ts
export function calculateTotal(params: { subtotal: number; discountCode?: string }): number {
  if (params.discountCode === 'SAVE10') return params.subtotal * 0.9
  return params.subtotal
}

if (import.meta.vitest) {
  const { it, expect } = import.meta.vitest
  it('SAVE10 で 10% 割引', () => {
    expect(calculateTotal({ subtotal: 100, discountCode: 'SAVE10' })).toBe(90)
  })
}
```

`vitest.config.ts` に `includeSource: ['src/**/*.ts']` を追加すること。

---

## パターン: Component テスト（React Testing Library）

### クエリの優先順位（必ず守る）

1. `getByRole` — 常に最初に試す
2. `getByLabelText` — フォーム要素
3. `getByText` — 表示テキスト
4. `getByTestId` — 上記が使えない最終手段のみ

`querySelector`・`container.firstChild`・クラス名での取得は禁止。

### 基本パターン

```typescript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import { LoginForm } from './LoginForm'

describe('LoginForm', () => {
  it('正常なログインで Welcome を表示する', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)

    await user.type(screen.getByLabelText('Email'), 'user@example.com')
    await user.type(screen.getByLabelText('Password'), 'secret')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Welcome')).toBeInTheDocument()
  })
})
```

**テストしてはいけないもの**: コンポーネントの内部 state・CSS クラス・中間変数。
**テストするもの**: ユーザーが見る・操作できるもの（observable behavior）。

### 非同期アサーション

```typescript
// Good: findBy* は自動的に待つ
expect(await screen.findByText('Loading complete')).toBeInTheDocument()

// Good: waitFor でポーリング
await waitFor(() => expect(mockFn).toHaveBeenCalledWith({ id: '1' }))

// Bad: Promise を直接アサートしない
expect(screen.findByText('...')).toBeTruthy() // 常に truthy になる
```

---

## パターン: MSW（ネットワークモック）

**ルール**: ネットワーク呼び出しをするモジュールを `vi.mock` でモックしない。
MSW で HTTP 境界のみをモックする。

### セットアップ

```typescript
// src/test-utils/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('/api/user', () =>
    HttpResponse.json({ id: 1, name: 'Alice' })
  ),
  http.post('/api/login', async ({ request }) => {
    const body = await request.json() as { password: string }
    if (body.password === 'wrong') {
      return HttpResponse.json({ error: 'Invalid credentials' }, { status: 401 })
    }
    return HttpResponse.json({ token: 'abc123' })
  }),
]
```

```typescript
// vitest.setup.ts
import { setupServer } from 'msw/node'
import { handlers } from './src/test-utils/handlers'

export const server = setupServer(...handlers)
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

### テストごとのオーバーライド

```typescript
import { server } from '../test-utils/server'
import { http, HttpResponse } from 'msw'

it('500 エラーを正しくハンドルする', async () => {
  server.use(
    http.get('/api/user', () => HttpResponse.error())
  )
  // ... テスト
})
```

詳細パターンは `references/patterns.md` を参照。

---

## Related skills

- `impl-from-design` — TDD モードで実装を進める場合はこちらが主体
- `test-review` — 書いたテストの品質を確認
