#!/bin/bash
set -euo pipefail
cp -cR /Users/kentaro/Desktop/_lab/ai/skills-eval-app/. .
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
mkdir -p "$(dirname 'src/features/products/ProductSearch.tsx')"
cat > 'src/features/products/ProductSearch.tsx' <<'EOF_FIXTURE'
import { type FormEvent, useEffect, useState } from "react";
import { type Product, searchProducts } from "../../api/products";

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; products: Product[] }
  | { status: "error" };

export function ProductSearch() {
  const [query, setQuery] = useState("");
  const [state, setState] = useState<State>({ status: "idle" });
  const [categories, setCategories] = useState<string[]>([]);

  // 入力中のキーワードに合う商品のカテゴリを候補として出す
  useEffect(() => {
    searchProducts(query)
      .then((products) => setCategories([...new Set(products.map((p) => p.category))]))
      .catch(() => setCategories([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      {categories.length > 0 && <p>カテゴリの候補: {categories.join("・")}</p>}
      {state.status === "loading" && <p>読み込み中…</p>}
      {state.status === "error" && <p role="alert">検索に失敗しました</p>}
      {state.status === "success" && state.products.length === 0 && <p>該当する商品はありません</p>}
      {state.status === "success" && state.products.length > 0 && (
        <ul aria-label="検索結果">
          {state.products.map((p) => (
            <li key={p.id}>
              {p.name}（{p.category}）¥{p.price.toLocaleString()}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
EOF_FIXTURE
