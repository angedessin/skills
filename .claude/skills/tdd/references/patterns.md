# TDD パターン集

`tdd` スキルおよび `impl-from-design` スキル（TDD モード）から参照される詳細パターン集。

---

## vitest.config.mts テンプレート

> **重要**: ファイル名は `vitest.config.mts`（`.ts` ではなく）。
> `.ts` のままだと CJS として読み込まれ、ESM の `@vitejs/plugin-react` で
> `ExperimentalWarning` が出る。

> **必須**: `environment: 'jsdom'` を使う場合は `jsdom` を別途インストールすること。
> ```bash
> pnpm add -D jsdom
> ```

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
    // In-source testing を使う場合
    includeSource: ['src/**/*.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/**/*.test.{ts,tsx}',
        'src/**/*.spec.{ts,tsx}',
      ],
    },
  },
  // In-source testing の本番ビルドでのツリーシェイク
  define: {
    'import.meta.vitest': 'undefined',
  },
})
```

---

## vitest.setup.ts テンプレート（MSW 込み）

```typescript
import '@testing-library/jest-dom'
import { setupServer } from 'msw/node'
import { handlers } from './src/test-utils/handlers'

export const server = setupServer(...handlers)

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

---

## Hook テスト（renderHook）

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

## 状態管理のテスト（Jotai の例）

コンポーネントを介さず、Store を直接テストする。

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

## Server Action / API Route テスト（Next.js）

```typescript
// Server Action のテスト
import { createUser } from './actions'

// 依存する DB 呼び出しは vi.mock（外部 I/O なので OK）
vi.mock('./db', () => ({
  insertUser: vi.fn().mockResolvedValue({ id: '1' }),
}))

it('正常なユーザー作成', async () => {
  const result = await createUser({ name: 'Alice', email: 'a@example.com' })
  expect(result).toEqual({ success: true, id: '1' })
})
```

**注意**: ネットワーク経由の外部 API は vi.mock ではなく MSW を使う。
DB・ファイルシステムへのアクセスは vi.mock で OK。

---

## E2E（Playwright）— TDD での使い方

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

**禁止パターン**:
- `page.waitForTimeout(1000)` → `expect(locator).toBeVisible()` を使う
- CSS セレクター（`.submit-btn`）→ `getByRole` / `getByLabel` を使う
- `page.locator('#id')` → セマンティクスを優先

---

## カバレッジのガイドライン

| 対象 | 目標カバレッジ | 備考 |
|------|----------------|------|
| `src/lib/` `src/utils/` | 80%+ | 純粋関数・ロジック |
| UI コンポーネント | 60%+ | 主要なユーザーインタラクション |
| 生成 UI（shadcn/ui 等） | 対象外 | 生成コードはカバレッジ免除 |

**目標**: カバレッジ % を上げるためだけのテストは書かない。
実際の仕様をエンコードするテストを優先する。
