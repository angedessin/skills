# tdd カートリッジ — React / Vitest / React Testing Library / MSW

> **これはスタック固有の「機構」層**。SKILL.md 本文（判断エンジン）が役割名（§unit 等）で参照する具体例を集約する。
> 別スタック（Vue / Svelte / Jest / node:test 等）に横展開するときは、**このファイルを自分のスタック用に再生成して差し替える**。本文（SKILL.md）は触らない。
> example スタック: React 18+ / Vitest / @testing-library/react / MSW v2 / Playwright
> `tdd` および `impl-from-design`（TDD モード）から参照される。

---

## §run — テストの実行

```bash
npx vitest run path/to/the.test.ts      # 単一ファイルを1回実行
npx vitest run                          # 全テスト
```

Red 確認時: コンパイル/import エラーでの失敗は Red ではない。型・import を直してから「正しい理由での失敗」を確認する。

---

## §config — vitest.config.mts テンプレート

> **重要**: ファイル名は `vitest.config.mts`（`.ts` ではなく）。`.ts` のままだと CJS として読み込まれ、ESM の `@vitejs/plugin-react` で `ExperimentalWarning` が出る。
> **必須**: `environment: 'jsdom'` を使う場合は `jsdom` を別途インストール（`pnpm add -D jsdom`）。

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',        // または 'happy-dom'（高速）
    setupFiles: ['./vitest.setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    includeSource: ['src/**/*.ts'],   // In-source testing を使う場合
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/**/*.test.{ts,tsx}', 'src/**/*.spec.{ts,tsx}'],
    },
  },
  define: { 'import.meta.vitest': 'undefined' },  // 本番ビルドでツリーシェイク
})
```

---

## §setup — vitest.setup.ts テンプレート（MSW 込み）

```typescript
import '@testing-library/jest-dom'
import { setupServer } from 'msw/node'
import { handlers } from './src/test-utils/handlers'

export const server = setupServer(...handlers)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

---

## §unit — Unit テスト（describe/it と In-source）

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

### In-source testing（ロジックが重いユーティリティ向け）

「ロジックが重い」の目安: 分岐・計算が多い（if/switch が複数、計算式が複雑）。単純なラッパー・1行委譲は対象外 → describe/it を使う。本番ビルドではツリーシェイクされる。

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

`vitest.config.mts` に `includeSource: ['src/**/*.ts']` が必要（§config）。

---

## §component — Component テスト（React Testing Library）

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

**「存在しない」ことの確認**: `getByText` ではなく `queryByText` を使い `.not.toBeInTheDocument()`。

### 非同期アサーション

```typescript
// Good: findBy* は自動的に待つ
expect(await screen.findByText('Loading complete')).toBeInTheDocument()
// Good: waitFor でポーリング
await waitFor(() => expect(mockFn).toHaveBeenCalledWith({ id: '1' }))
// Bad: Promise を直接アサートしない（常に truthy）
expect(screen.findByText('...')).toBeTruthy()
```

---

## §query-ladder — クエリ優先順位（必ず守る）

1. `getByRole` — 常に最初に試す
2. `getByLabelText` — フォーム要素
3. `getByText` — 表示テキスト
4. `getByTestId` — 上記が使えない最終手段のみ

`querySelector`・`container.firstChild`・クラス名での取得は禁止。

---

## §network — MSW（ネットワークモック）

ハンドラ定義:

```typescript
// src/test-utils/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('/api/user', () => HttpResponse.json({ id: 1, name: 'Alice' })),
  http.post('/api/login', async ({ request }) => {
    const body = await request.json() as { password: string }
    if (body.password === 'wrong') {
      return HttpResponse.json({ error: 'Invalid credentials' }, { status: 401 })
    }
    return HttpResponse.json({ token: 'abc123' })
  }),
]
```

テストごとのオーバーライド:

```typescript
import { server } from '../test-utils/server'
import { http, HttpResponse } from 'msw'

it('500 エラーを正しくハンドルする', async () => {
  server.use(http.get('/api/user', () => HttpResponse.error()))
  // ... テスト
})
```

---

## §hook — Hook テスト（renderHook）

```typescript
import { renderHook, act } from '@testing-library/react'
import { useCounter } from './useCounter'

describe('useCounter', () => {
  it('初期値を返す', () => {
    const { result } = renderHook(() => useCounter(0))
    expect(result.current.count).toBe(0)
  })

  it('increment で 1 増える', () => {
    const { result } = renderHook(() => useCounter(0))
    act(() => result.current.increment())
    expect(result.current.count).toBe(1)
  })
})
```

---

## §state — 状態管理のテスト（Jotai の例）

コンポーネントを介さず Store を直接テストする。

```typescript
import { createStore } from 'jotai'
import { countAtom, incrementAtom } from './store'

describe('countAtom', () => {
  it('初期値は 0', () => {
    const store = createStore()
    expect(store.get(countAtom)).toBe(0)
  })

  it('increment で 1 増える', () => {
    const store = createStore()
    store.set(incrementAtom)
    expect(store.get(countAtom)).toBe(1)
  })
})
```

---

## §api-layer — API クライアント / fetch 層テスト

サーバー側ロジック（API クライアント・データアクセス関数・サーバーアクション等、呼び名はフレームワーク次第）も同じ原則でテストする。

```typescript
import { createUser } from './users'

// DB・ファイルシステムなど非ネットワークの外部 I/O は vi.mock で OK
vi.mock('./db', () => ({
  insertUser: vi.fn().mockResolvedValue({ id: '1' }),
}))

it('正常なユーザー作成', async () => {
  const result = await createUser({ name: 'Alice', email: 'a@example.com' })
  expect(result).toEqual({ success: true, id: '1' })
})
```

**注意**: ネットワーク経由の外部 API は vi.mock ではなく MSW を使う（HTTP 境界でモック）。DB・ファイルシステムは vi.mock で OK。

---

## §e2e — E2E（Playwright）— TDD での使い方

> **E2E テストの作成・レビューは `e2e` スキルが担当**（対象選定・粒度・安定性の判断軸はそちらを参照）。この節は Red を E2E シナリオから始める場合の記法例としてのみ残す。

シナリオを先に書いてから実装する。

```typescript
// tests/e2e/checkout.spec.ts
import { test, expect } from '@playwright/test'

test('ユーザーがチェックアウトを完了できる', async ({ page }) => {
  await page.goto('/checkout')
  await page.getByLabel('カード番号').fill('4111111111111111')
  await page.getByLabel('有効期限').fill('12/28')
  await page.getByLabel('CVV').fill('123')
  await page.getByRole('button', { name: /支払う/i }).click()

  await expect(page.getByText('注文が確定しました')).toBeVisible()
})
```

**禁止パターン**: `page.waitForTimeout(1000)` → `expect(locator).toBeVisible()` / CSS セレクタ → `getByRole`/`getByLabel` / `page.locator('#id')` → セマンティクス優先。

---

## §coverage — カバレッジのガイドライン

| 対象 | 目標カバレッジ | 備考 |
|------|----------------|------|
| `src/lib/` `src/utils/` | 80%+ | 純粋関数・ロジック |
| UI コンポーネント | 60%+ | 主要なユーザーインタラクション |
| 生成 UI（shadcn/ui 等） | 対象外 | 生成コードはカバレッジ免除 |

**目標**: カバレッジ % を上げるためだけのテストは書かない。実際の仕様をエンコードするテストを優先する。
