#!/bin/bash
set -euo pipefail
cp -cR /Users/kentaro/Desktop/_lab/ai/skills-eval-app/. .
mkdir -p "$(dirname '.steering/20261010-category-filter/design.md')"
cat > '.steering/20261010-category-filter/design.md' <<'EOF_FIXTURE'
# 設計: category-filter

Created: 20261010
Status: **APPROVED**（20261010）

## 目的

商品検索の結果をカテゴリで絞り込めるようにする。

## スコープ

- 対象: 検索フォームの下にカテゴリの select を置き、検索結果をクライアント側で絞り込む
- 対象外: API の変更・URL への状態の保存

## 設計

- カテゴリの選択肢は固定の 3 件（周辺機器・ディスプレイ・オーディオ）と「すべて」
- 初期値は「すべて」。選択を変えたら、取得済みの結果をその場で絞り込む（再検索しない）
- 絞り込みの結果が 0 件なら「該当する商品はありません」を出す

## 完了条件

- [ ] カテゴリを選ぶと、そのカテゴリの商品だけが表示される
- [ ] 「すべて」に戻すと、検索結果の全件が表示される
- [ ] 既存のテスト 3 件が通る
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261010-category-filter/tasklist.md')"
cat > '.steering/20261010-category-filter/tasklist.md' <<'EOF_FIXTURE'
# タスクリスト: category-filter

Last updated: 20261012

- [x] 絞り込みの関数 `filterByCategory` を `src/features/products/filter.ts` に作り、テストを書く
- [x] ProductSearch に選択中のカテゴリの state を足す
- [ ] カテゴリの select を追加する（固定の 3 件と「すべて」）
- [ ] 絞り込みの結果をテストで確かめる（MSW）
- [ ] 0 件のときの表示を確かめる
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261010-category-filter/decisions.md')"
cat > '.steering/20261010-category-filter/decisions.md' <<'EOF_FIXTURE'
# 決定事項: category-filter

## 20261011 — 絞り込みはクライアント側で行う

**決定**: API は変えず、取得済みの結果をクライアント側で絞り込む
**理由**: 商品数が少なく、API の変更は対象外にしたため

## 20261012 — カテゴリの選択肢は固定値をやめ、検索結果から作る

**決定**: select の選択肢は、固定の 3 件ではなく、その時点の検索結果に含まれるカテゴリから作る（重複を除き、「すべて」を先頭に置く）
**理由**: カテゴリが増えるたびに固定の一覧を直すことになり、結果に無いカテゴリを選ぶと必ず 0 件になるため
**影響**: design.md の「設計」と tasklist の 3 番目は、まだ固定の 3 件のまま（次の作業のときに直す）
EOF_FIXTURE
mkdir -p "$(dirname 'src/features/products/filter.ts')"
cat > 'src/features/products/filter.ts' <<'EOF_FIXTURE'
import type { Product } from "../../api/products";

export const ALL = "すべて";

export function filterByCategory(products: Product[], category: string): Product[] {
  if (category === ALL) return products;
  return products.filter((p) => p.category === category);
}
EOF_FIXTURE
mkdir -p "$(dirname 'src/features/products/filter.test.ts')"
cat > 'src/features/products/filter.test.ts' <<'EOF_FIXTURE'
import { filterByCategory, ALL } from "./filter";

const products = [
  { id: "1", name: "a", category: "周辺機器", price: 1 },
  { id: "2", name: "b", category: "ディスプレイ", price: 2 },
];

describe("filterByCategory", () => {
  it("「すべて」なら全件を返す", () => {
    expect(filterByCategory(products, ALL)).toHaveLength(2);
  });

  it("カテゴリが一致する商品だけを返す", () => {
    expect(filterByCategory(products, "ディスプレイ").map((p) => p.id)).toEqual(["2"]);
  });
});
EOF_FIXTURE
python3 - <<'EOF_PY'
import re
p = 'src/features/products/ProductSearch.tsx'
s = open(p, encoding='utf-8').read()
s = s.replace('import { type Product, searchProducts } from "../../api/products";',
              'import { type Product, searchProducts } from "../../api/products";\nimport { ALL } from "./filter";')
s = s.replace('  const [query, setQuery] = useState("");',
              '  const [query, setQuery] = useState("");\n  const [category, setCategory] = useState(ALL);')
open(p, 'w', encoding='utf-8').write(s)
EOF_PY
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
