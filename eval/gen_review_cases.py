"""eval/evals/review/ のケースを生成する（ケースを直すときはこれを直して再実行し、生成物ごとコミットする）。使い方: python3 -I gen_review_cases.py "$PWD"
評価セットの正本は .steering/20261006-skillset-renewal/eval-review-group.md。仕込みバグは新しいレビューの agent を書く前に固定する。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evalcase import *  # noqa: E402,F403

ROOT = sys.argv[1]  # .../skills/eval
EV = os.path.join(ROOT, "evals", "review")

PC = "src/features/products/ProductSearch.tsx"
PT = "src/features/products/ProductSearch.test.tsx"
PROMPT = "コードをレビューして。"


def planted(cid, desc, files, bug):
    """サンプルアプリをコミットした後に files（パス → 中身）を未コミットの変更として重ね、レビューを頼む。
    bug は仕込んだバグを指摘したかの採点基準（英語）。"""
    d = f"{EV}/{cid}"
    w(f"{d}/case.yaml", case_yaml(cid, desc, ["frontend-code-review", "planted"], 60, 1800, group="review"))
    w(f"{d}/prompt.md", PROMPT + "\n")
    overlay = "".join(heredoc(p, c) for p, c in files.items())
    w(f"{d}/fixture.sh", fixture() + overlay)  # fixture() の最後でコミットし、その後に重ねる
    stop_graders(d)  # レビューの依頼なので src/ を書き換えない
    llm(d, "q1-found-bug", "Judge the final response, which is a code review of an uncommitted change. " + bug)
    skill_fired(d, "frontend-code-review")
    return d


# ---------------------------------------------------------------- P2 race
P2_COMPONENT = """import { type FormEvent, useEffect, useState } from "react";
import { type Product, searchProducts } from "../../api/products";

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; products: Product[] }
  | { status: "error" };

export function ProductSearch() {
  const [query, setQuery] = useState("");
  const [state, setState] = useState<State>({ status: "idle" });

  // 入力のたびに検索する（検索ボタンを押さなくても結果が出る）
  useEffect(() => {
    if (query === "") {
      setState({ status: "idle" });
      return;
    }
    setState({ status: "loading" });
    searchProducts(query)
      .then((products) => setState({ status: "success", products }))
      .catch(() => setState({ status: "error" }));
  }, [query]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
  }

  return (
    <section>
      <h1>商品検索</h1>
      <form role="search" onSubmit={handleSubmit}>
        <label htmlFor="query">キーワード</label>
        <input id="query" value={query} onChange={(e) => setQuery(e.target.value)} />
      </form>
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
"""
P2_TEST = """import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { server } from "../../mocks/server";
import { ProductSearch } from "./ProductSearch";

describe("ProductSearch", () => {
  it("入力するとキーワードに一致する商品を表示する", async () => {
    const user = userEvent.setup();
    render(<ProductSearch />);

    await user.type(screen.getByLabelText("キーワード"), "モニター");

    const list = await screen.findByRole("list", { name: "検索結果" });
    expect(list).toHaveTextContent("27インチモニター");
    expect(list).toHaveTextContent("モニターアーム");
    expect(list).not.toHaveTextContent("ワイヤレスマウス");
  });

  it("該当がないときはその旨を表示する", async () => {
    const user = userEvent.setup();
    render(<ProductSearch />);

    await user.type(screen.getByLabelText("キーワード"), "冷蔵庫");

    expect(await screen.findByText("該当する商品はありません")).toBeInTheDocument();
  });

  it("API が失敗したらエラーを表示する", async () => {
    server.use(http.get("/api/products", () => new HttpResponse(null, { status: 500 })));
    const user = userEvent.setup();
    render(<ProductSearch />);

    await user.type(screen.getByLabelText("キーワード"), "a");

    expect(await screen.findByRole("alert")).toHaveTextContent("検索に失敗しました");
  });
});
"""
planted(
    "p2-race", "仕込みバグ P2: 入力のたびに検索し、古い応答が新しい結果を上書きする（race）",
    {PC: P2_COMPONENT, PT: P2_TEST},
    "PASS if it points out that, because a request is sent on every keystroke without cancelling or ignoring earlier requests, a slower response for an older query can arrive after a newer one and overwrite the results (a race; for example missing cleanup, AbortController, or an ignore flag in the effect). FAIL if this problem is not mentioned.",
)

print("ok")
