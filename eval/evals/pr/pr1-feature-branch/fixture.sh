#!/bin/bash
set -euo pipefail
cp -cR /Users/kentaro/Desktop/_lab/ai/skills-eval-app/. .
git remote remove origin 2>/dev/null || true
git init -q --bare .remote.git
echo '.remote.git/' >> .git/info/exclude
git remote add origin "$PWD/.remote.git"
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
git push -q origin HEAD:refs/heads/main
git branch -M main
git branch -u origin/main >/dev/null 2>&1 || true
git checkout -q -b feature/category-filter
mkdir -p "$(dirname 'src/features/products/filterByCategory.ts')"
cat > 'src/features/products/filterByCategory.ts' <<'EOF_FIXTURE'
import type { Product } from "../../api/products";

export function filterByCategory(products: Product[], category: string): Product[] {
  if (category === "") return products;
  return products.filter((p) => p.category === category);
}
EOF_FIXTURE
mkdir -p "$(dirname 'src/features/products/filterByCategory.test.ts')"
cat > 'src/features/products/filterByCategory.test.ts' <<'EOF_FIXTURE'
import { describe, expect, it } from "vitest";
import { filterByCategory } from "./filterByCategory";

const products = [
  { id: "1", name: "A", category: "ディスプレイ", price: 1000 },
  { id: "2", name: "B", category: "周辺機器", price: 2000 },
];

describe("filterByCategory", () => {
  it("空のカテゴリなら全件を返す", () => {
    expect(filterByCategory(products, "")).toHaveLength(2);
  });
  it("一致するカテゴリだけを返す", () => {
    expect(filterByCategory(products, "周辺機器").map((p) => p.id)).toEqual(["2"]);
  });
});
EOF_FIXTURE
