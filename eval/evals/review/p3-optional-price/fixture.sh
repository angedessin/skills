#!/bin/bash
set -euo pipefail
cp -cR /Users/kentaro/Desktop/_lab/ai/skills-eval-app/. .
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
mkdir -p "$(dirname 'src/api/products.ts')"
cat > 'src/api/products.ts' <<'EOF_FIXTURE'
export type Product = {
  id: string;
  name: string;
  category: string;
  /** 価格未定の商品は undefined */
  price?: number;
};

export async function searchProducts(query: string): Promise<Product[]> {
  const params = new URLSearchParams({ q: query });
  const res = await fetch(`/api/products?${params}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch products: ${res.status}`);
  }
  return res.json();
}
EOF_FIXTURE
mkdir -p "$(dirname 'src/mocks/data.ts')"
cat > 'src/mocks/data.ts' <<'EOF_FIXTURE'
import type { Product } from "../api/products";

export const products: Product[] = [
  { id: "1", name: "ワイヤレスマウス", category: "周辺機器", price: 3980 },
  { id: "2", name: "メカニカルキーボード", category: "周辺機器", price: 12800 },
  { id: "3", name: "USB-C ハブ", category: "周辺機器", price: 4500 },
  { id: "4", name: "27インチモニター", category: "ディスプレイ", price: 32800 },
  { id: "5", name: "モニターアーム", category: "ディスプレイ", price: 8900 },
  { id: "6", name: "ノイズキャンセリングヘッドホン", category: "オーディオ", price: 29800 },
  { id: "7", name: "ギフトカード", category: "その他" },
];
EOF_FIXTURE
mkdir -p "$(dirname 'src/features/products/formatPrice.ts')"
cat > 'src/features/products/formatPrice.ts' <<'EOF_FIXTURE'
export function formatPrice(price?: number): string {
  return `¥${(price as number).toLocaleString()}`;
}
EOF_FIXTURE
mkdir -p "$(dirname 'src/features/products/ProductSearch.tsx')"
cat > 'src/features/products/ProductSearch.tsx' <<'EOF_FIXTURE'
import { type FormEvent, useState } from "react";
import { type Product, searchProducts } from "../../api/products";
import { formatPrice } from "./formatPrice";

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; products: Product[] }
  | { status: "error" };

export function ProductSearch() {
  const [query, setQuery] = useState("");
  const [state, setState] = useState<State>({ status: "idle" });

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState({ status: "loading" });
    try {
      const products = await searchProducts(query);
      setState({ status: "success", products });
    } catch {
      setState({ status: "error" });
    }
  }

  return (
    <section>
      <h1>商品検索</h1>
      <form role="search" onSubmit={handleSubmit}>
        <label htmlFor="query">キーワード</label>
        <input id="query" value={query} onChange={(e) => setQuery(e.target.value)} />
        <button type="submit">検索</button>
      </form>
      {state.status === "loading" && <p>読み込み中…</p>}
      {state.status === "error" && <p role="alert">検索に失敗しました</p>}
      {state.status === "success" && state.products.length === 0 && <p>該当する商品はありません</p>}
      {state.status === "success" && state.products.length > 0 && (
        <ul aria-label="検索結果">
          {state.products.map((p) => (
            <li key={p.id}>
              {p.name}（{p.category}）{formatPrice(p.price)}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
EOF_FIXTURE
