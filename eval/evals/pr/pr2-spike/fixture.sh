#!/bin/bash
set -euo pipefail
cp -cR /Users/kentaro/Desktop/_lab/ai/skills-eval-app/. .
git remote remove origin 2>/dev/null || true
git init -q --bare .remote.git
echo '.remote.git/' >> .git/info/exclude
git remote add origin "$PWD/.remote.git"
mkdir -p "$(dirname '.steering/20261030-category-filter/design.md')"
cat > '.steering/20261030-category-filter/design.md' <<'EOF_FIXTURE'
# カテゴリの絞り込み（探索）

Status: SPIKE

## 目的

カテゴリで絞り込む関数の形を試す。結果を見て設計を決め、この実装は捨てる前提。
EOF_FIXTURE
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
