#!/bin/bash
set -euo pipefail
cp -cR /Users/kentaro/Desktop/_lab/ai/skills-eval-app/. .
mkdir -p "$(dirname 'e2e/search.spec.ts')"
cat > 'e2e/search.spec.ts' <<'EOF_FIXTURE'
import { expect, test, type Page } from "@playwright/test";

let page: Page;
test.describe.configure({ mode: "serial" });

test("検索できる", async ({ browser }) => {
  page = await browser.newPage();
  await page.goto("/");

  await page.fill("#query", "モニター");
  await page.click("button[type=submit]");
  await page.waitForTimeout(2000);
  await expect(page.locator("ul > li:nth-child(2)")).toHaveText(/モニターアーム/);

  await page.fill("#query", "冷蔵庫");
  await page.click("button[type=submit]");
  await page.waitForTimeout(2000);
  await expect(page.locator("p")).toHaveText("該当する商品はありません");

  await page.route("**/api/products**", (route) => route.fulfill({ status: 500 }));
  await page.click("button[type=submit]");
  await page.waitForTimeout(2000);
  await expect(page.locator("[role=alert]")).toBeVisible();
});

test("入力したキーワードが残っている", async () => {
  const state = await page.evaluate(() => (window as unknown as { __searchState: { query: string } }).__searchState);
  expect(state.query).toBe("冷蔵庫");
});
EOF_FIXTURE
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
