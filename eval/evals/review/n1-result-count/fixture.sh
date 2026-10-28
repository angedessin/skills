#!/bin/bash
set -euo pipefail
cp -cR /Users/kentaro/Desktop/_lab/ai/skills-eval-app/. .
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
mkdir -p "$(dirname 'src/features/products/ProductSearch.tsx')"
cat > 'src/features/products/ProductSearch.tsx' <<'EOF_FIXTURE'
import { type FormEvent, useState } from "react";
import { type Product, searchProducts } from "../../api/products";

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
        <>
        <p>{state.products.length} 件見つかりました</p>
        <ul aria-label="検索結果">
          {state.products.map((p) => (
            <li key={p.id}>
              {p.name}（{p.category}）¥{p.price.toLocaleString()}
            </li>
          ))}
        </ul>
        </>
      )}
    </section>
  );
}
EOF_FIXTURE
mkdir -p "$(dirname 'src/features/products/ProductSearch.test.tsx')"
cat > 'src/features/products/ProductSearch.test.tsx' <<'EOF_FIXTURE'
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { server } from "../../mocks/server";
import { ProductSearch } from "./ProductSearch";

describe("ProductSearch", () => {
  it("キーワードに一致する商品を表示する", async () => {
    const user = userEvent.setup();
    render(<ProductSearch />);

    await user.type(screen.getByLabelText("キーワード"), "モニター");
    await user.click(screen.getByRole("button", { name: "検索" }));

    const list = await screen.findByRole("list", { name: "検索結果" });
    expect(list).toHaveTextContent("27インチモニター");
    expect(list).toHaveTextContent("モニターアーム");
    expect(list).not.toHaveTextContent("ワイヤレスマウス");
    expect(screen.getByText("2 件見つかりました")).toBeInTheDocument();
  });

  it("該当がないときはその旨を表示する", async () => {
    const user = userEvent.setup();
    render(<ProductSearch />);

    await user.type(screen.getByLabelText("キーワード"), "冷蔵庫");
    await user.click(screen.getByRole("button", { name: "検索" }));

    expect(await screen.findByText("該当する商品はありません")).toBeInTheDocument();
  });

  it("API が失敗したらエラーを表示する", async () => {
    server.use(http.get("/api/products", () => new HttpResponse(null, { status: 500 })));
    const user = userEvent.setup();
    render(<ProductSearch />);

    await user.click(screen.getByRole("button", { name: "検索" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("検索に失敗しました");
  });
});
EOF_FIXTURE
