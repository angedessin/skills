# E2E Patterns — Playwright (example)

> **これはマスター同梱の example**。配置先プロジェクトの E2E スタックに合わせて**再生成すること**。
> E2E を書かないプロジェクトではこのファイルを削除してよい — `e2e` 本文は判断軸のみで縮退動作する。

## §scope — E2E テストファイルの識別

```bash
# playwright.config.ts の testDir 設定が正。一般的な配置:
git diff --name-only HEAD | grep -E '^(e2e|tests?)/.*\.spec\.ts$'
```

## §run — 実行と flaky 検出

```bash
# 第一候補: package.json スクリプト経由（fetch セマンティクスなし。例: "e2e": "playwright test"）
npm run e2e -- [file]
npm run e2e -- --repeat-each=3 [file]    # 同一テストを繰り返して flaky 検出
npm run e2e -- --trace=on [file]         # 失敗調査用トレース

# スクリプト未定義で Playwright がローカル導入済みのときのみ npx を使う
# （未導入だとレジストリ取得 → 即実行が走る。導入済みバイナリの実行にのみ使う）
npx playwright test [file]
```

## §locators — ロケータ優先順位ラダー

```typescript
// 1. 役割 + アクセシブルネーム（最優先 — ユーザーが認識する意味）
await page.getByRole('button', { name: '購入する' }).click()

// 2. ラベル・可視テキスト
await page.getByLabel('メールアドレス').fill('a@example.com')
await expect(page.getByText('注文が完了しました')).toBeVisible()

// 3. テスト専用属性（可視の意味で取れない場合のみ）
page.getByTestId('cart-total')

// 4. CSS セレクタ（最後の手段 — 実装結合のレッドフラグ）
page.locator('.price')  // Bad: クラス名変更で壊れる
```

## §waiting — 明示的待機

```typescript
// Bad: 固定時間の sleep（遅い環境で落ち、速い環境で時間を無駄にする）
await page.waitForTimeout(3000)

// Good: 条件で待つ（ロケータの auto-wait を活かす）
await expect(page.getByText('注文完了')).toBeVisible()
await page.waitForURL('**/checkout/complete')
await page.waitForResponse(res => res.url().includes('/api/order') && res.ok())
```

## §auth — 認証状態の再利用（テスト間独立を保ったまま高速化）

```typescript
// auth.setup.ts — ログインを 1 回だけ実行して状態を保存
import { test as setup } from '@playwright/test'

setup('authenticate', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('メールアドレス').fill(process.env.E2E_USER!)
  await page.getByLabel('パスワード').fill(process.env.E2E_PASS!)
  await page.getByRole('button', { name: 'ログイン' }).click()
  await page.waitForURL('**/dashboard')
  await page.context().storageState({ path: 'playwright/.auth/user.json' })
})
```

```typescript
// playwright.config.ts — setup プロジェクト + storageState の再利用
projects: [
  { name: 'setup', testMatch: /auth\.setup\.ts/ },
  {
    name: 'chromium',
    dependencies: ['setup'],
    use: { storageState: 'playwright/.auth/user.json' },
  },
]
```

## §fixtures — テスト間独立と一意なテストデータ

```typescript
// Bad: 前のテストが作ったデータに依存（順序依存 — 単独実行で落ちる）
test('編集できる', async ({ page }) => {
  await page.goto('/items/1')  // 「作成テスト」が item 1 を作った前提
})

// Good: 各テストが自分で前提を整え、一意なデータを使う
test('編集できる', async ({ page }) => {
  const name = `item-${Date.now()}`
  await createItemViaAPI(name)          // セットアップは API 経由で高速に
  await page.goto('/items')
  await page.getByRole('link', { name }).click()
})
```
