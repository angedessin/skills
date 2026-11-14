"""eval/evals/review/ のケースを生成する（ケースを直すときはこれを直して prepare.sh を流す。生成物はコミットしない）。使い方: python3 -I gen_review_cases.py "$PWD"
このファイルが評価セットの正本。決めた経緯は、閉じたタスク 20261006-skillset-renewal の eval-review-group.md（git の履歴。探し方は .steering/history.md）。仕込みバグは新しいレビューの agent を書く前に固定する。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evalcase import *  # noqa: E402,F403

ROOT = sys.argv[1]  # .../skills/eval
EV = os.path.join(ROOT, "evals", "review")

PC = "src/features/products/ProductSearch.tsx"
PT = "src/features/products/ProductSearch.test.tsx"
PROMPT = "コードをレビューして。"
LARGE_OK = "コードをレビューして。大きい差分だけど、範囲と費用は了承しているので全部見て。"


REPO = os.path.dirname(os.path.abspath(ROOT))  # マスター（このリポジトリ）。過去の差分の取り出し元
JUDGE = "Judge the final response, which is a code review of an uncommitted change. "


def base(path):
    with open(os.path.join(APP, path), encoding="utf-8") as f:
        return f.read()


def sub(text, pairs):
    """text の old を new に置き換える。old が無ければ止める（サンプルアプリが変わったときに気づくため）。"""
    for old, new in pairs:
        assert old in text, old
        text = text.replace(old, new, 1)
    return text


def planted(cid, desc, files, bug, tags=("planted",)):
    """サンプルアプリをコミットした後に files（パス → 中身）を未コミットの変更として重ね、レビューを頼む。
    bug は仕込んだバグを指摘したかの採点基準（英語）。None ならバグなしの差分（誤検知だけを人が見る）。"""
    d = f"{EV}/{cid}"
    w(f"{d}/case.yaml", case_yaml(cid, desc, ["frontend-code-review", *tags], 60, 1800, group="review"))
    w(f"{d}/prompt.md", PROMPT + "\n")
    overlay = "".join(heredoc(p, c) for p, c in files.items())
    w(f"{d}/fixture.sh", fixture() + overlay)  # fixture() の最後でコミットし、その後に重ねる
    stop_graders(d, scratch_ok=True)  # レビューの依頼なので src/ を書き換えない。検証役が一時ディレクトリの写しで再現するのは許す
    if bug:
        llm(d, "q1-found-bug", JUDGE + bug)
    skill_fired(d, "frontend-code-review")
    return d


def past(cid, desc, before, after, findings, tags=("past",), prompt=PROMPT):
    """マスターの before の状態を作業場所に展開してコミットし、after の状態を未コミットの変更として重ねる。
    findings は (slug, 採点基準) の並び。採点基準が PASS になるのが望ましい結果（真の指摘は「指摘した」、誤検知は「出さなかった」）。
    prompt は依頼文。frontend-code-review 2.1 の大きさの基準（1,000 行・20 ファイル超）を超える差分は LARGE_OK で範囲を了承し、Step 1 で止まらずにレビューさせる。"""
    d = f"{EV}/{cid}"
    w(f"{d}/case.yaml", case_yaml(cid, desc, ["frontend-code-review", *tags], 80, 2400, group="review"))
    w(f"{d}/prompt.md", prompt + "\n")
    w(f"{d}/fixture.sh", (
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        f"git -C {REPO} archive {before} | tar -x\n"
        "git init -q\n"
        "git add -A >/dev/null\n"
        'git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "before"\n'
        "# after の状態に置き換える（追跡中のファイルを消してから展開し、削除も差分に出す）。未コミットのまま残す\n"
        "git ls-files -z | xargs -0 rm -f\n"
        f"git -C {REPO} archive {after} | tar -x\n"
    ))
    no_write(d, "no-repo-files", "(?:scripts|\\.claude|tests)/")
    for i, (slug, text) in enumerate(findings, 1):
        llm(d, f"q{i}-{slug}", JUDGE + text)
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

# ---------------------------------------------------------------- P1・P3〜P10・N1・N2（20261028 固定。新しいレビューの agent を書く前）
BC = base(PC)
API = "src/api/products.ts"
DATA = "src/mocks/data.ts"
FMT = "src/features/products/formatPrice.ts"

# P1 stale closure: debounce の中で古い query を使う
planted(
    "p1-stale-closure", "仕込みバグ P1: 入力の 300ms 後に検索するが、タイマーの中で 1 つ前の query を使う（stale closure）",
    {PC: sub(BC, [
        ('import { type FormEvent, useState } from "react";', 'import { type ChangeEvent, type FormEvent, useRef, useState } from "react";'),
        ('  const [state, setState] = useState<State>({ status: "idle" });\n',
         '  const [state, setState] = useState<State>({ status: "idle" });\n  const timer = useRef<number | undefined>(undefined);\n'),
        ("  async function handleSubmit(event: FormEvent<HTMLFormElement>) {\n    event.preventDefault();\n    setState",
         "  // 入力が止まってから 300ms 後に検索する\n  function handleChange(event: ChangeEvent<HTMLInputElement>) {\n    setQuery(event.target.value);\n    window.clearTimeout(timer.current);\n    timer.current = window.setTimeout(() => {\n      void runSearch();\n    }, 300);\n  }\n\n  async function handleSubmit(event: FormEvent<HTMLFormElement>) {\n    event.preventDefault();\n    await runSearch();\n  }\n\n  async function runSearch() {\n    setState"),
        ("onChange={(e) => setQuery(e.target.value)}", "onChange={handleChange}"),
    ])},
    "PASS if it points out that the debounced timer callback uses a stale query value: runSearch reads the query from the render in which the timer was created, so after typing it searches with the previous value (missing the last keystroke), not the current input. FAIL if this problem is not mentioned.",
)

# P3 null: price を任意にしたが、表示で undefined を数値として扱う
planted(
    "p3-optional-price", "仕込みバグ P3: 価格を任意項目にしたが、表示の関数が as number で undefined を隠して toLocaleString を呼ぶ",
    {
        API: sub(base(API), [("  price: number;", "  /** 価格未定の商品は undefined */\n  price?: number;")]),
        DATA: sub(base(DATA), [("];", '  { id: "7", name: "ギフトカード", category: "その他" },\n];')]),
        FMT: 'export function formatPrice(price?: number): string {\n  return `¥${(price as number).toLocaleString()}`;\n}\n',
        PC: sub(BC, [
            ('import { type Product, searchProducts } from "../../api/products";', 'import { type Product, searchProducts } from "../../api/products";\nimport { formatPrice } from "./formatPrice";'),
            ("¥{p.price.toLocaleString()}", "{formatPrice(p.price)}"),
        ]),
    },
    "PASS if it points out that formatPrice casts a possibly undefined price with 'as number' and calls toLocaleString, which throws (or breaks rendering) for products without a price such as the new gift card. FAIL if this problem is not mentioned.",
)

# P4 境界: カンマ入りの上限が Number で NaN になり、全件が消える（空欄は正しく扱う。既存のテストは通る）
planted(
    "p4-nan-max", "仕込みバグ P4: 価格の上限で絞るが、「10,000」のようなカンマ入りの入力が Number で NaN になり、結果が全部消える",
    {PC: sub(BC, [
        ('  const [state, setState] = useState<State>({ status: "idle" });\n',
         '  const [state, setState] = useState<State>({ status: "idle" });\n  const [maxPrice, setMaxPrice] = useState("");\n'),
        ('        <button type="submit">検索</button>\n',
         '        <button type="submit">検索</button>\n        <label htmlFor="max-price">上限（円）</label>\n        <input id="max-price" inputMode="numeric" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} />\n'),
        ('      {state.status === "success" && state.products.length === 0 && <p>該当する商品はありません</p>}\n      {state.status === "success" && state.products.length > 0 && (\n        <ul aria-label="検索結果">\n          {state.products.map((p) => (',
         '      {state.status === "success" && visible.length === 0 && <p>該当する商品はありません</p>}\n      {state.status === "success" && visible.length > 0 && (\n        <ul aria-label="検索結果">\n          {visible.map((p) => ('),
        ("  return (\n", "  const limit = maxPrice === \"\" ? Number.POSITIVE_INFINITY : Number(maxPrice);\n  const visible = state.status === \"success\" ? state.products.filter((p) => p.price <= limit) : [];\n\n  return (\n"),
    ])},
    "PASS if it points out that a max price typed with thousands separators or other non-digit characters (for example '10,000', full-width digits, or '1万') becomes NaN through Number(), so every product is filtered out and the user just sees '該当する商品はありません'. FAIL if this problem is not mentioned.",
)

# P5 React: useEffect の依存配列が空で、キーワードの変化に追従しない
planted(
    "p5-effect-deps", "仕込みバグ P5: キーワードに合うカテゴリの一覧を出すが、useEffect の依存配列が空で最初の 1 回しか取得しない",
    {PC: sub(BC, [
        ('import { type FormEvent, useState } from "react";', 'import { type FormEvent, useEffect, useState } from "react";'),
        ('  const [state, setState] = useState<State>({ status: "idle" });\n',
         '  const [state, setState] = useState<State>({ status: "idle" });\n  const [categories, setCategories] = useState<string[]>([]);\n\n'
         '  // 入力中のキーワードに合う商品のカテゴリを候補として出す\n  useEffect(() => {\n    searchProducts(query)\n      .then((products) => setCategories([...new Set(products.map((p) => p.category))]))\n      .catch(() => setCategories([]));\n    // eslint-disable-next-line react-hooks/exhaustive-deps\n  }, []);\n'),
        ('      </form>\n', '      </form>\n      {categories.length > 0 && <p>カテゴリの候補: {categories.join("・")}</p>}\n'),
    ])},
    "PASS if it points out that the useEffect has an empty dependency array (with the exhaustive-deps rule disabled), so the category suggestions are fetched only once for the initial empty query and never follow the keyword. FAIL if this problem is not mentioned.",
)

# P6 React: key={index} で、並び替えるとチェックがずれる
planted(
    "p6-index-key", "仕込みバグ P6: 一覧に「お気に入り」のチェックと価格順の並び替えを足すが、key が index で並び替えるとチェックがずれる",
    {PC: sub(BC, [
        ('  const [state, setState] = useState<State>({ status: "idle" });\n',
         '  const [state, setState] = useState<State>({ status: "idle" });\n  const [byPrice, setByPrice] = useState(false);\n'),
        ('      {state.status === "success" && state.products.length > 0 && (\n        <ul aria-label="検索結果">\n          {state.products.map((p) => (\n            <li key={p.id}>\n              {p.name}',
         '      {state.status === "success" && state.products.length > 0 && (\n        <label>\n          <input type="checkbox" checked={byPrice} onChange={(e) => setByPrice(e.target.checked)} />\n          安い順に並べる\n        </label>\n      )}\n'
         '      {state.status === "success" && state.products.length > 0 && (\n        <ul aria-label="検索結果">\n          {(byPrice ? [...state.products].sort((a, b) => a.price - b.price) : state.products).map((p, i) => (\n            <li key={i}>\n              <label>\n                <input type="checkbox" />\n                お気に入り\n              </label>\n              {p.name}'),
    ])},
    "PASS if it points out that the list uses the array index as the key while the order can change (sorting by price), so the uncontrolled favorite checkboxes stay with the position instead of the product and end up checked on the wrong products. FAIL if this problem is not mentioned.",
)

# P7 エラー: 通信の失敗だけを握りつぶし、読み込み中のまま止まる（HTTP エラーは正しく扱うので既存のテストは通る）
planted(
    "p7-swallowed-error", "仕込みバグ P7: 失敗時の再試行ボタンを足すが、通信の失敗（TypeError）だけは状態を戻さず、読み込み中のまま止まる",
    {PC: sub(BC, [
        ("  async function handleSubmit(event: FormEvent<HTMLFormElement>) {\n    event.preventDefault();\n    setState({ status: \"loading\" });\n    try {\n      const products = await searchProducts(query);\n      setState({ status: \"success\", products });\n    } catch {\n      setState({ status: \"error\" });\n    }\n  }",
         "  async function handleSubmit(event: FormEvent<HTMLFormElement>) {\n    event.preventDefault();\n    await runSearch();\n  }\n\n  async function runSearch() {\n    setState({ status: \"loading\" });\n    try {\n      const products = await searchProducts(query);\n      setState({ status: \"success\", products });\n    } catch (error) {\n      if (error instanceof TypeError) {\n        // 通信が切れているときは、つながったら再試行してもらう\n        console.warn(\"offline\", error);\n        return;\n      }\n      setState({ status: \"error\" });\n    }\n  }"),
        ('      {state.status === "error" && <p role="alert">検索に失敗しました</p>}',
         '      {state.status === "error" && (\n        <p role="alert">\n          検索に失敗しました\n          <button type="button" onClick={() => void runSearch()}>\n            再試行\n          </button>\n        </p>\n      )}'),
    ])},
    "PASS if it points out that when the request fails at the network level (fetch rejects with a TypeError, for example offline), the catch block returns without leaving the loading state, so the UI stays on '読み込み中…' forever and the retry button (shown only in the error state) never appears. FAIL if this problem is not mentioned.",
)

# P8 セキュリティ: dangerouslySetInnerHTML に入力をそのまま入れる
planted(
    "p8-xss", "仕込みバグ P8: 商品名のキーワードを強調するが、dangerouslySetInnerHTML に入力と商品名をそのまま入れる（XSS）",
    {PC: sub(BC, [
        ("export function ProductSearch() {", "function highlight(name: string, keyword: string): string {\n  if (keyword === \"\") return name;\n  return name.replaceAll(keyword, `<mark>${keyword}</mark>`);\n}\n\nexport function ProductSearch() {"),
        ("              {p.name}（{p.category}）¥{p.price.toLocaleString()}",
         "              <span dangerouslySetInnerHTML={{ __html: highlight(p.name, query) }} />（{p.category}）¥{p.price.toLocaleString()}"),
    ])},
    "PASS if it points out that the highlight builds HTML from the user's keyword (and product names) without escaping and renders it with dangerouslySetInnerHTML, which allows HTML/script injection (XSS); suggesting rendering <mark> as React elements or escaping is fine. FAIL if this problem is not mentioned.",
)

# P9 a11y: アイコンだけのボタンで、アクセシブルな名前が無い
planted(
    "p9-icon-button", "仕込みバグ P9: 入力を消すボタンを足すが、アイコンだけでアクセシブルな名前が無い",
    {PC: sub(BC, [
        ('        <input id="query" value={query} onChange={(e) => setQuery(e.target.value)} />\n',
         '        <input id="query" value={query} onChange={(e) => setQuery(e.target.value)} />\n'
         '        {query !== "" && (\n          <button type="button" className="clear" onClick={() => setQuery("")}>\n'
         '            <svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12">\n              <path d="M1 1l10 10M11 1L1 11" stroke="currentColor" />\n            </svg>\n          </button>\n        )}\n'),
    ])},
    "PASS if it points out that the new clear button contains only an aria-hidden icon, so it has no accessible name for screen readers (needs aria-label or visible/visually hidden text). FAIL if this problem is not mentioned.",
)

# P10 テスト: 内部モジュールをモックし、呼び出しだけを確かめる
planted(
    "p10-mock-echo", "仕込みバグ P10: 検索のテストを足すが、API のモジュールを vi.mock で差し替え、呼び出し引数だけを確かめる（振る舞いを見ない）",
    {"src/features/products/ProductSearch.calls.test.tsx": """import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { searchProducts } from "../../api/products";
import { ProductSearch } from "./ProductSearch";

vi.mock("../../api/products", () => ({
  searchProducts: vi.fn().mockResolvedValue([]),
}));

describe("ProductSearch の検索", () => {
  it("入力したキーワードで検索する", async () => {
    const user = userEvent.setup();
    render(<ProductSearch />);

    await user.type(screen.getByLabelText("キーワード"), "モニター");
    await user.click(screen.getByRole("button", { name: "検索" }));

    expect(searchProducts).toHaveBeenCalledTimes(1);
    expect(searchProducts).toHaveBeenCalledWith("モニター");
  });
});
"""},
    "PASS if it points out that the new test mocks the app's own API module with vi.mock instead of mocking at the HTTP boundary (MSW, which the project already uses), and only asserts on the call arguments rather than on what the user sees, so it would keep passing if the results were not rendered. FAIL if this problem is not mentioned.",
)

# N1・N2 バグなし（誤検知だけを人が見る）
planted(
    "n1-result-count", "バグなし N1: 検索結果の件数を表示する（テストつき）",
    {
        PC: sub(BC, [('        <ul aria-label="検索結果">\n', '        <>\n        <p>{state.products.length} 件見つかりました</p>\n        <ul aria-label="検索結果">\n'),
                     ("          ))}\n        </ul>\n", "          ))}\n        </ul>\n        </>\n")]),
        PT: sub(base(PT), [('    expect(list).not.toHaveTextContent("ワイヤレスマウス");\n',
                            '    expect(list).not.toHaveTextContent("ワイヤレスマウス");\n    expect(screen.getByText("2 件見つかりました")).toBeInTheDocument();\n')]),
    },
    None, tags=("clean",),
)
planted(
    "n2-format-price", "バグなし N2: 価格の表示を関数に切り出す（テストつき）",
    {
        FMT: 'export function formatPrice(price: number): string {\n  return `¥${price.toLocaleString("ja-JP")}`;\n}\n',
        "src/features/products/formatPrice.test.ts": 'import { formatPrice } from "./formatPrice";\n\ndescribe("formatPrice", () => {\n  it("3 桁ごとに区切って円記号を付ける", () => {\n    expect(formatPrice(32800)).toBe("¥32,800");\n  });\n\n  it("0 円も表示する", () => {\n    expect(formatPrice(0)).toBe("¥0");\n  });\n});\n',
        PC: sub(BC, [
            ('import { type Product, searchProducts } from "../../api/products";', 'import { type Product, searchProducts } from "../../api/products";\nimport { formatPrice } from "./formatPrice";'),
            ("¥{p.price.toLocaleString()}", "{formatPrice(p.price)}"),
        ]),
    },
    None, tags=("clean",),
)

# ---------------------------------------------------------------- T1・T2 テストの指摘（A3。skill-loop-fixes）
# T1 は実装ファイルだけを変えるので、review-test はテストファイルが変わっていなくても起動する条件でしか呼ばれない
T1 = planted(
    "t1-missing-test", "テストの指摘 T1: 検索をやり直す「クリア」ボタンを足したが、テストを足していない",
    {PC: sub(BC, [
        ("  async function handleSubmit(", '  function handleClear() {\n    setQuery("");\n    setState({ status: "idle" });\n  }\n\n  async function handleSubmit('),
        ('        <button type="submit">検索</button>\n',
         '        <button type="submit">検索</button>\n        <button type="button" onClick={handleClear}>\n          クリア\n        </button>\n'),
    ])},
    "PASS if it points out that the new clear button (resetting the keyword and the results) has no test that exercises it, for example that no test clicks the clear button and checks that the input and results are cleared. FAIL if the missing test for the clear behavior is not mentioned.",
    tags=("test-review",),
)
# T2 の並べ替えのテストは、2 件が表示されることだけを見るので、sort を消しても逆順にしても通る
T2 = planted(
    "t2-shallow-test", "テストの指摘 T2: 結果を価格の安い順に並べ、並び順を確かめないテストを足す（形だけ）",
    {
        PC: sub(BC, [("          {state.products.map((p) => (",
                      "          {[...state.products].sort((a, b) => a.price - b.price).map((p) => (")]),
        PT: sub(base(PT), [('  it("該当がないときはその旨を表示する"',
                            '  it("価格の安い順に並べる", async () => {\n    const user = userEvent.setup();\n    render(<ProductSearch />);\n\n'
                            '    await user.type(screen.getByLabelText("キーワード"), "モニター");\n    await user.click(screen.getByRole("button", { name: "検索" }));\n\n'
                            '    const list = await screen.findByRole("list", { name: "検索結果" });\n    expect(list).toHaveTextContent("モニターアーム");\n'
                            '    expect(list).toHaveTextContent("27インチモニター");\n  });\n\n  it("該当がないときはその旨を表示する"')]),
    },
    "PASS if it points out that the new test for price ordering does not check the order of the items (it only checks that both names appear), so it would still pass if the sort were removed or reversed, AND it states how this was established (for example: it removed or reversed the sort and the test still passed, or it names the change to the sort that the test would not catch). FAIL if the problem is not mentioned, or if it is mentioned without saying how the implementation would be broken.",
    tags=("test-review",),
)
# A5: テストファイルが変わったら、検証の前に変える前のコードで流す（結果は q1 の「どう壊したか」に出る）。
# 中身を読んだだけで通らないよう、bash で実行した形だけを数える。T1 はテストファイルが変わらないので呼ばない
RUN_ON_BASE = "'\\bbash\\s+\\S*run-tests-on-base\\.sh'"
grader(f"{T2}/graders/q2-ran-tests-on-base.md", {"type": "tool_used", "tool": "Bash", "input_match": RUN_ON_BASE, "min": 1})
grader(f"{T1}/graders/q2-skips-tests-on-base.md", {"type": "tool_used", "tool": "Bash", "input_match": RUN_ON_BASE, "min": 0, "max": 0})

# ---------------------------------------------------------------- L1 大きい差分（費用を示して止まる）。20261108 に足した回帰ケース
def bench(name, n, ms):
    rows = ",\n".join(f'  {{"case": "{name}-{i:04d}", "ms": {ms + i % 37}, "ok": true}}' for i in range(n))
    return f"[\n{rows}\n]\n"


BENCH = [f"bench/results-{k}.json" for k in ("search", "list", "detail")]
L1 = f"{EV}/l1-large-diff"
w(f"{L1}/case.yaml", case_yaml("l1-large-diff", "大きい差分 L1: 評価の生成物が 1,800 行あり、費用の目安を示して止まる", ["frontend-code-review", "large"], 40, 1200, group="review"))
w(f"{L1}/prompt.md", PROMPT + "\n")
# 生成物は小さい版をコミットしておき、大きい版で上書きする（追跡中の変更として --shortstat に出す）。src の変更は N1 と同じ
w(f"{L1}/fixture.sh", fixture("".join(heredoc(p, bench(p.split("-")[1][:-5], 3, 100)) for p in BENCH))
  + "".join(heredoc(p, bench(p.split("-")[1][:-5], 600, 100 + 50 * i)) for i, p in enumerate(BENCH))
  + heredoc(PC, sub(BC, [('        <ul aria-label="検索結果">\n', '        <>\n        <p>{state.products.length} 件見つかりました</p>\n        <ul aria-label="検索結果">\n'),
                         ("          ))}\n        </ul>\n", "          ))}\n        </ul>\n        </>\n")])))
stop_graders(L1)
grader(f"{L1}/graders/stop-no-agent.md", {"type": "tool_used", "tool": "Agent", "min": 0, "max": 0})
llm(L1, "how-asks-cost", JUDGE + "The uncommitted change is about 1,800 changed lines, almost all in generated benchmark files under bench/, plus a small change in src/. "
    "PASS if the response, before reviewing, reports the size of the change (files or lines), gives a rough cost or time estimate, suggests narrowing the scope (for example excluding bench/), "
    "and asks whether to proceed, without presenting review findings. FAIL if it presents review findings, or does not give any cost or time estimate, or does not ask.")
skill_fired(L1, "frontend-code-review")

# ---------------------------------------------------------------- 過去の差分（真の指摘）。eval-material.md の 1
past("r-a-hardening", "過去の差分 R-a（20260725 skillset-hardening）: 真の指摘 T1〜T8", "1ff1701", "309b950", [
    ("t1-ask-bypass", "PASS if it points out that the permission 'ask' rules only cover Edit/Write, so an allowed Bash command such as 'git show ... > file' (redirection) can write gated files and bypass the approval gate. FAIL otherwise."),
    ("t2-empty-master", "PASS if it points out that in check_export_stopcontract.py the fail-closed check exists only on the export side: when the master side yields nothing (for example an empty --master), it compares zero pairs and still reports success. FAIL otherwise."),
    ("t3-stop-vocab", "PASS if it points out that STOP_VOCAB in check_export_stopcontract.py only matches the plain form '止まる' and misses other ways a stop contract is written (such as '待つ' or '書き込まない'), so stop contracts can be missed. FAIL otherwise."),
    ("t4-traceback", "PASS if it points out that validate_skills.py prints a raw Python traceback for an unknown flag instead of a usage error. FAIL otherwise."),
    ("t5-verbose-doc", "PASS if it points out that the --verbose behavior of check_export_stopcontract.py does not match what its docstring says. FAIL otherwise."),
    ("t6-truncation", "PASS if it points out that the report truncates text with [:120], so a difference located later in the line (for example around character 192) is not visible. FAIL otherwise."),
    ("t7-word-boundary", "PASS if it points out that removing skill names does not respect word boundaries (for example removing 'adr' also breaks 'adrenaline'). FAIL otherwise."),
    ("t8-stack-words", "PASS if it points out that STACK_WORDS lacks '.test.tsx' / '.spec.tsx' (or that the replacement order breaks them). FAIL otherwise."),
], prompt=LARGE_OK)  # 30 ファイル・1,926 行
past("r-b-deploy-integrity", "過去の差分 R-b（20260726 deploy-integrity）: 真の指摘 T9〜T14", "04b912c", "76779ff", [
    ("t9-exit2-masks", "PASS if it points out that in check_asset_consistency.py the exit code 2 for 'no target' swallows FAIL results from other contracts, so the hook stays silent even when something is broken. FAIL otherwise."),
    ("t10-warning-not-shown", "PASS if it points out that a warning documented as always listed is not printed in the default run. FAIL otherwise."),
    ("t11-master-hooks", "PASS if it points out that the check does not compare the hooks registered in the master's own .claude/settings.json. FAIL otherwise."),
    ("t12-settings-edit", "PASS if it points out that validate-skill-edit.sh does not trigger the check when .claude/settings.json is edited. FAIL otherwise."),
    ("t13-heredoc-comments", "PASS if it points out that dropping lines starting with '#' also removes lines inside heredocs (and that the shebang is not compared). FAIL otherwise."),
    ("t14-unanchored-glob", "PASS if it points out that the hook's path glob is not anchored, so edits in another worktree (or another path containing the same segment) also trigger it. FAIL otherwise."),
], prompt=LARGE_OK)  # 9 ファイル・1,281 行
past("r-c-rm-mv-policy", "過去の差分 R-c（20260806 rm-mv-policy）: 真の指摘 T15〜T19", "57be75a^", "57be75a", [
    ("t15-quoted-path", "PASS if it points out that in guard-gated-delete.sh a path wrapped in double quotes inside the JSON is cut by the [^\"]* pattern, so detection silently fails. FAIL otherwise."),
    ("t16-dir-without-slash", "PASS if it points out that a directory given without a trailing slash (for example 'rm -rf docs/knowledge') is not detected. FAIL otherwise."),
    ("t17-whole-command-grep", "PASS if it points out that grepping the whole command line wrongly denies commands like 'rm /tmp/a && ls docs/knowledge/' where the gated path is not being deleted. FAIL otherwise."),
    ("t18-partial-match", "PASS if it points out that partial matching of CLAUDE.md also denies files like CLAUDE.md.bak. FAIL otherwise."),
    ("t19-json-escapes", "PASS if it points out that JSON escapes such as \\t or \\n are not decoded, so detection can silently fail. FAIL otherwise."),
])
past("r-d-pr13-mustfix", "過去の差分 R-d（20260807 pr13-mustfix）: 真の指摘 T20・T21", "71a8071^", "71a8071", [
    ("t20-marker-parse", "PASS if it points out that parsing contract markers like '(g)(i)' wrongly picks up '(i)' (a false detection). FAIL otherwise."),
    ("t21-package-json", "PASS if it points out that when reading package.json fails, the details are lost (the error detail is dropped). FAIL otherwise."),
])

# ---------------------------------------------------------------- 過去の誤検知（出さないのが望ましい）
past("f1-semicolon", "過去の誤検知 F1: 空白の無い ; の連鎖で完全一致の検査が素通りする、という実測で否定された High", "2b7fdbe^", "2b7fdbe", [
    ("no-f1", "Background: this was checked by running it; shlex with punctuation_chars=True does split ';' even without spaces, and the four forms were confirmed to be asked. PASS if the review does NOT claim (as a real problem) that commands chained with ';' without spaces slip past the exact-match checks in the guard hooks. FAIL if it makes that claim."),
], tags=("past", "false-positive"), prompt=LARGE_OK)  # 19 ファイル・1,082 行
past("f4-env-example", "過去の誤検知 F4: Read(./.env*) が .env.example まで拒否する、という意図どおりの設定への指摘", "226c14d^", "226c14d", [
    ("no-f4", "Background: denying .env.example together with other .env files is an intentional, safe-side choice. PASS if the review does NOT raise, as a problem to fix, that the Read(./.env*) deny rule also blocks .env.example. FAIL if it does."),
], tags=("past", "false-positive"))

print("ok")
