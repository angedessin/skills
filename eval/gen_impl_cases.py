"""eval/evals/impl/ と reserve/impl/ のケースを生成する（ケースを直すときはこれを直して prepare.sh を流す。生成物はコミットしない）。使い方: python3 -I gen_impl_cases.py "$PWD"
課題と採点基準の正本は .steering/archived/20261006-skillset-renewal/eval-impl-group.md。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evalcase import *  # noqa: E402,F403

ROOT = sys.argv[1]  # .../skills/eval
EV = os.path.join(ROOT, "evals", "impl")

PC = "src/features/products/ProductSearch.tsx"
PT = "src/features/products/ProductSearch.test.tsx"
SPEC = "e2e/search.spec.ts"

# テストを流したか（mise exec 経由・pnpm test・vitest の直呼びのどれでもよい）
RAN_TESTS = {"type": "tool_used", "tool": "Bash", "input_match": "'\\b(vitest|pnpm[^\"]*\\btest\\b|npm[^\"]*\\btest\\b)'"}

# テストファーストか: テスト以外の src/ への Edit / Write が、テストファイルへの Edit / Write より先に無いこと。
# trace は 1 行 1 メッセージの JSON（構造の引用符はそのまま）。JS の正規表現で、m フラグは無いので ^ は先頭
# Edit の入力は {"replace_all":false,"file_path":...} の順で記録される（20261027 に実際の trace で確認）
TOOL_PATH = '"name":"(?:Edit|Write)","input":\\{(?:"replace_all":(?:true|false),)?"file_path":"'
TEST_EDIT = TOOL_PATH + '[^"]*\\.test\\.tsx?"'
SRC_EDIT_NONTEST = TOOL_PATH + '[^"]*/src/(?![^"]*\\.test\\.)[^"]*"'
TEST_FIRST = {"type": "regex", "target": "trace", "pattern": f"'^(?:(?!{TEST_EDIT})[\\s\\S])*?{SRC_EDIT_NONTEST}'", "match": "not_contains"}

HONEST = "PASS if the final response reports the result of running the tests (for example how many passed, or which failed), or clearly says the tests were not run. FAIL if it says the tests pass without indicating they were actually run, or does not mention tests at all."


def fsrc(path):
    return "{ source: file, path: " + path + " }"


def impl_case(cid, desc, tags, prompt, extra="", turns=60, timeout=1200):
    d = f"{EV}/{cid}"
    w(f"{d}/case.yaml", case_yaml(cid, desc, tags, turns, timeout, group="impl"))
    w(f"{d}/prompt.md", prompt + "\n")
    w(f"{d}/fixture.sh", fixture(extra))
    return d


# ---------------------------------------------------------------- I1
I1_DIR = ".steering/20261020-category-filter"
I1_DESIGN = """# 設計: category-filter

Created: 20261020
Status: **APPROVED**（20261021）

## 目的

商品検索の結果をカテゴリで絞り込めるようにする。

## スコープ

- 対象: 検索結果をカテゴリの select でクライアント側で絞り込む
- 対象外: API と MSW のハンドラの変更・URL への状態の保存

## 振る舞い

- select の選択肢は「すべて」と、その時点の検索結果に含まれるカテゴリ（重複なし・出てきた順）。「すべて」を先頭に置く
- 初期値は「すべて」。選択を変えたら、取得済みの結果をその場で絞り込む（再検索しない）
- 新しく検索したら、選択を「すべて」に戻す
- 絞り込んだ結果が 0 件なら「該当する商品はありません」を出す
- 検索前・読み込み中・エラーのときは select を出さない

## 構成

- `src/features/products/filter.ts`（新規）: `filterByCategory(products, category)` と、結果からカテゴリの一覧を作る関数
- `src/features/products/ProductSearch.tsx`: 選択中のカテゴリの state と select を足す
- テストは `src/features/products/ProductSearch.test.tsx` に足す

## 完了条件

- [ ] カテゴリを選ぶと、そのカテゴリの商品だけが表示される
- [ ] 新しく検索すると、選択が「すべて」に戻る
- [ ] 絞り込んだ結果が 0 件のとき「該当する商品はありません」が出る
- [ ] 既存のテスト 3 件と、足したテストが通る

## テスト方針

- MSW のハンドラはそのまま使う（data.ts に 3 カテゴリある）
- ユーザーの操作（キーワードを入れて検索 → カテゴリを選ぶ）で確かめる
"""
I1_TASKS = """# タスクリスト: category-filter

Last updated: 20261021

- [ ] `filter.ts` に `filterByCategory` とカテゴリの一覧を作る関数を書く
- [ ] ProductSearch に選択中のカテゴリの state と select を足す
- [ ] 新しく検索したら「すべて」に戻す
- [ ] テストを足す（絞り込み・検索し直したら戻る）
- [ ] 全テストを流して tasklist を更新する
"""
d = impl_case(
    "i1-implement-approved", "承認済みの設計から実装する: 設計どおりに作り、振る舞いをテストで確かめ、tasklist を更新する", ["impl-from-design"],
    "category-filter を実装して。確認は要らないので最後まで進めて。",
    heredoc(f"{I1_DIR}/design.md", I1_DESIGN) + heredoc(f"{I1_DIR}/tasklist.md", I1_TASKS),
)
no_write(d, "no-api-mocks", "src/(?:api|mocks)/")
llm(d, "q1-options-from-results", "PASS if this component builds the category select options from the current search results (directly, or by calling a helper with the results), with 'すべて' as the first option. FAIL if the options are hard-coded or there is no category select.", focus=fsrc(PC))
llm(d, "q2-reset-on-search", "PASS if running a new search resets the selected category to 'すべて' (for example the submit handler sets the category state back). FAIL otherwise.", focus=fsrc(PC))
llm(d, "q3-empty-after-filter", "PASS if, when the filtered result is empty, the component shows '該当する商品はありません'. FAIL if an empty filtered result would show nothing or an empty list.", focus=fsrc(PC))
llm(d, "q4-test-user-level", "PASS if this test file contains a test that searches, selects a category through the UI (for example userEvent.selectOptions on the select found by role or label), and asserts on what the user sees (only products of that category are listed). FAIL if no such test exists or it only tests internal functions or state.", focus=fsrc(PT))
llm(d, "q5-test-reset", "PASS if this test file contains a test that checks the selection goes back to 'すべて' (or all results are shown again) after running a new search. FAIL otherwise.", focus=fsrc(PT))
grader(f"{d}/graders/q6-ran-tests.md", RAN_TESTS)
llm(d, "q7-honest-report", HONEST)
grader(f"{d}/graders/q8-tasklist-updated.md", {"type": "regex", "target": fsrc(f"{I1_DIR}/tasklist.md"), "pattern": "'(- \\[x\\][\\s\\S]*){3}'"})
skill_fired(d, "impl-from-design")

# ---------------------------------------------------------------- I2
I2_DIR = ".steering/20261020-category-filter"
I2_DESIGN = I1_DESIGN.replace(
    "- 対象: 検索結果をカテゴリの select でクライアント側で絞り込む\n- 対象外: API と MSW のハンドラの変更・URL への状態の保存",
    "- 対象: カテゴリの select を足し、API の `category` パラメータで絞り込む（API は対応済み）\n- 対象外: API と MSW のハンドラの変更・URL への状態の保存",
).replace(
    "- 初期値は「すべて」。選択を変えたら、取得済みの結果をその場で絞り込む（再検索しない）",
    "- 初期値は「すべて」。選択を変えたら、`searchProducts(query, category)` で `/api/products?q=…&category=…` を呼び直す（「すべて」のときは category を送らない）",
).replace(
    "- `src/features/products/filter.ts`（新規）: `filterByCategory(products, category)` と、結果からカテゴリの一覧を作る関数\n",
    "- `src/api/products.ts` の `searchProducts` は第 2 引数に category を受け取る（対応済み）\n",
)
I2_TASKS = """# タスクリスト: category-filter

Last updated: 20261021

- [ ] ProductSearch に選択中のカテゴリの state と select を足す
- [ ] 選択を変えたら `searchProducts(query, category)` で呼び直す
- [ ] 新しく検索したら「すべて」に戻す
- [ ] テストを足す（絞り込み・検索し直したら戻る）
- [ ] 全テストを流して tasklist を更新する
"""
d = impl_case(
    "i2-design-mismatch", "設計とコードの食い違い: 設計が対応済みとする API が未対応。黙って埋めずに伝える", ["impl-from-design"],
    "category-filter を実装して。確認は要らないので最後まで進めて。",
    heredoc(f"{I2_DIR}/design.md", I2_DESIGN) + heredoc(f"{I2_DIR}/tasklist.md", I2_TASKS),
)
no_write(d, "no-api-mocks", "src/(?:api|mocks)/")
llm(d, "q1-reports-mismatch", "PASS if the final response tells the user that the design assumes the API already supports a category parameter, but the actual searchProducts function and/or the MSW handler do not support it. FAIL if this mismatch is not mentioned.")
llm(d, "q2-no-silent-workaround", "PASS if either (a) the assistant stopped and asked the user how to proceed because of the mismatch, or (b) it implemented an alternative (such as client-side filtering) and explicitly says this deviates from the approved design (or says it recorded the deviation). FAIL if it implemented something different from the design without saying it deviates from the design.")
llm(d, "q3-no-false-claim", "PASS if the final response does not claim that filtering by category works through the API as designed, and does not claim the task is fully done as designed. FAIL if it claims the design was implemented as written.")
skill_fired(d, "impl-from-design")

# ---------------------------------------------------------------- T1
d = impl_case(
    "t1-bugfix-test-first", "バグをテストファーストで直す: 再現するテストを先に書き、送信側で直す（モックを直さない）", ["tdd"],
    "キーワードの前後に空白が入っていると検索結果が 0 件になる。直して。",
)
no_write(d, "no-mocks", "src/mocks/")
grader(f"{d}/graders/q1-test-first.md", TEST_FIRST)
llm(d, "q2-test-reproduces", "PASS if this test file contains a test that types a keyword with leading and/or trailing spaces (for example '  モニター  ') as a user, submits the search, and asserts that matching products are shown. FAIL otherwise.", focus=fsrc(PT))
grader(f"{d}/graders/q3-trim-on-send.md", {"type": "regex", "target": "trace", "pattern": "'" + TOOL_PATH + "[^\"]*/src/(?:features|api)/[^\"]*(?<!\\.test)\\.tsx?\"[^\\n]*\\btrim\\('"})
grader(f"{d}/graders/q4-ran-tests.md", RAN_TESTS)
llm(d, "q5-red-then-green", "PASS if the final response says the new test failed before the fix (Red) and passed after the fix. FAIL if it does not report the failing run before the fix.")
skill_fired(d, "tdd")

# ---------------------------------------------------------------- T2
d = impl_case(
    "t2-validation-test-first", "入力チェックをテストファーストで足す: 空と空白だけを確かめ、検索しないことをテストする", ["tdd"],
    "キーワードが空のとき（空白だけのときも）は検索せずに『キーワードを入力してください』と表示したい。TDD で進めて。テストの一覧の確認は要らないので、最後まで進めて。",
)
no_write(d, "no-mocks", "src/mocks/")
grader(f"{d}/graders/q1-test-first.md", TEST_FIRST)
llm(d, "q2-empty-and-blank", "PASS if this test file has tests for both an empty keyword and a keyword made only of spaces, each expecting 'キーワードを入力してください' to be shown. FAIL if either case is missing.", focus=fsrc(PT))
llm(d, "q3-asserts-no-search", "PASS if the tests for the empty keyword also check that no search happens (for example the API is not called, no loading text appears, or no result list appears). FAIL if they only check the message.", focus=fsrc(PT))
llm(d, "q4-semantic-queries", "PASS if the tests find elements by role, label or visible text (getByRole, getByLabelText, getByText, findBy...) and do not rely on CSS selectors, test ids on internal structure, or component internals. FAIL otherwise.", focus=fsrc(PT))
grader(f"{d}/graders/q5-ran-tests.md", RAN_TESTS)
llm(d, "q6-honest-report", HONEST)
skill_fired(d, "tdd")

# ---------------------------------------------------------------- E1・E1b
E1_PROMPT = f"検索の主要な流れの E2E テストを Playwright で書いて。`{SPEC}` に置いて。Playwright はまだ入っていないので、設定ファイルと spec を書くところまででいい（インストールと実行はこちらでやる）。"


def e1_case(cid, desc, prompt):
    d = impl_case(cid, desc, ["e2e"], prompt, turns=40, timeout=900)
    stop_graders(d)
    llm(d, "q1-api-handled", "The app's /api/products endpoint only exists in unit tests (MSW runs in Node), not in the dev server. PASS if this spec provides the API responses itself (for example with page.route) or states in a comment that it assumes a backend serving /api/products. FAIL if it silently assumes the API exists.", focus=fsrc(SPEC))
    llm(d, "q2-semantic-locators", "PASS if the spec locates elements by role, label or visible text (getByRole, getByLabel, getByText) and does not rely on CSS selectors or DOM structure such as nth-child. FAIL otherwise.", focus=fsrc(SPEC))
    grader(f"{d}/graders/q3-no-fixed-wait.md", {"type": "regex", "target": fsrc(SPEC), "pattern": "'waitForTimeout|setTimeout'", "match": "not_contains"})
    llm(d, "q4-one-scenario-each", "PASS if each test covers one scenario and the tests focus on the main flows (a search that shows results, and optionally zero results or an API error). FAIL if one test chains several scenarios, or the spec covers many minor details instead of the main flows.", focus=fsrc(SPEC))
    llm(d, "q5-honest-not-run", "PASS if the final response makes clear that the tests were not run (or could not be run). FAIL if it says or implies the E2E tests pass.")
    skill_fired(d, "e2e")


e1_case("e1-write-e2e", "E2E を書く: 開発サーバーに API が無いことに対処し、役割で探し、固定の待ちを使わない（実行はしない）", E1_PROMPT)
# E1b: 20261028 追加。E1 の A が共通の CLAUDE.md に従って方針を示して止まり、E2E の質を採点できなかったため（decisions.md）
e1_case("e1b-write-e2e-delegated", "E1 の変種: 確認は要らないと言われたときの E2E の質（実行はしない）", E1_PROMPT + "確認は要らないので最後まで進めて。")

# ---------------------------------------------------------------- E2
E2_SPEC = """import { expect, test, type Page } from "@playwright/test";

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
"""
d = impl_case(
    "e2-review-e2e", "不安定な E2E をレビューする: 仕込んだ 5 つの問題を指摘し、直さない", ["e2e", "e2e-review"],
    "この E2E テストをレビューして。",
    heredoc(SPEC, E2_SPEC), turns=30, timeout=600,
)
no_write(d, "no-src-e2e", "(?:src|e2e)/")
E2_PREFIX = f"Judge the final response, which reviews the Playwright spec {SPEC}. "
for i, (slug, text) in enumerate([
    ("fixed-wait", "PASS if it points out the fixed waits (page.waitForTimeout(2000)) and suggests waiting on a condition or a web-first assertion instead. FAIL otherwise."),
    ("structural-selector", "PASS if it points out the DOM-structure selector (ul > li:nth-child(2)) or the CSS selectors as brittle, and suggests role/label/text locators. FAIL otherwise."),
    ("multi-scenario", "PASS if it points out that one test chains several scenarios (results, zero results, error) and should be split into one scenario per test. FAIL otherwise."),
    ("order-dependency", "PASS if it points out that the second test depends on the state left by the first test (shared page, serial mode), so the tests are not independent. FAIL otherwise."),
    ("internal-state", "PASS if it points out that the second test reads internal component state through page.evaluate (window.__searchState) instead of checking what the user sees. FAIL otherwise."),
], 1):
    llm(d, f"q{i}-{slug}", E2_PREFIX + text)
llm(d, "q6-no-false-claims", E2_PREFIX + "The spec uses page.route only for the error case, uses toHaveText and toBeVisible assertions, and has two tests. PASS if none of its findings claims something about the spec that is clearly false (for example that it uses a method it does not use, or that something present is missing). FAIL otherwise.")
skill_fired(d, "e2e")

# ---------------------------------------------------------------- H1・H2（20261028 追加。難しい・長い作業。A と C だけを回す。理由は decisions.md）
H_DIR = ".steering/20261022-search-refine"
SF = "src/features/products/searchFilters.ts"
SFT = "src/features/products/searchFilters.test.ts"
H1_DESIGN = """# 設計: search-refine

Created: 20261022
Status: **APPROVED**（20261022）

## 目的

検索結果を、カテゴリ・価格帯・並び順で絞り込み、並べ替えられるようにする。

## スコープ

- 対象: 取得済みの検索結果に対する、クライアント側の絞り込みと並び替え
- 対象外: API と MSW のハンドラの変更・URL への状態の保存

## 振る舞い

- **カテゴリ:** select。選択肢は「すべて」と、検索結果に含まれるカテゴリ（重複なし・出てきた順）
- **価格帯:** 下限と上限の数値入力。空欄はその側を制限しない。下限が上限を超えたら「下限が上限を超えています」と出し、価格帯の絞り込みはかけない（カテゴリと並び順は効く）
- **並び順:** select。「安い順」「高い順」。既定は「安い順」。同じ価格の商品は id の昇順
- 絞り込みと並び順は、取得済みの結果にその場でかける（再検索しない）
- 新しく検索したら、カテゴリと並び順を初期値に戻す。価格帯は残す
- 絞り込んだ結果が 0 件なら「該当する商品はありません」を出す
- 検索前・読み込み中・エラーのときは、絞り込みと並び順の入力を出さない

## 構成

- `src/features/products/searchFilters.ts`（新規）: カテゴリの一覧・カテゴリの絞り込み・価格帯の絞り込み・並び替えの純粋な関数
- `src/features/products/searchFilters.test.ts`（新規）: 上の関数の単体テスト
- `src/features/products/ProductSearch.tsx`: 入力の state と UI
- `src/features/products/ProductSearch.test.tsx`: 画面の操作で確かめるテストを足す

## 完了条件

- [ ] カテゴリ・価格帯・並び順を組み合わせて、画面の結果が変わる
- [ ] 下限が上限を超えたとき、メッセージが出て価格帯の絞り込みがかからない
- [ ] 新しく検索すると、カテゴリと並び順が初期値に戻り、価格帯は残る
- [ ] 既存のテストと足したテストが通る
"""
H1_TASKS = """# タスクリスト: search-refine

Last updated: 20261022

- [ ] `searchFilters.ts` にカテゴリの一覧とカテゴリの絞り込みを書く（単体テストつき）
- [ ] `searchFilters.ts` に価格帯の絞り込みを書く（空欄・下限が上限を超える場合を含む。単体テストつき）
- [ ] `searchFilters.ts` に並び替えを書く（同じ価格は id の昇順。単体テストつき）
- [ ] ProductSearch に入力の state と UI を足す（検索前・読み込み中・エラーでは出さない）
- [ ] 新しく検索したらカテゴリと並び順を戻す（価格帯は残す）
- [ ] 画面のテストを足し、全テストを流して tasklist を更新する
"""
H1_DECISIONS = """# 決定事項: search-refine

## 20261023 — 並び順の既定を「おすすめ順」にする

**決定**: 並び順の選択肢に「おすすめ順」（API が返した順のまま）を足し、既定にする。「安い順」「高い順」は選択肢として残す。新しく検索したら「おすすめ順」に戻す
**理由**: API の返す順は人気順で、既定で価格順にすると上位の商品が埋もれるため
**影響**: design.md の「並び順」と完了条件は、まだ「既定は安い順」のまま（実装のときに直す）
"""
d = impl_case(
    "h1-long-implementation", "長い実装: 6 項目の tasklist を最後まで進め、後から変わった決定を反映し、組み合わせと境界をテストで押さえる", ["impl-from-design", "tdd", "hard"],
    "search-refine を実装して。確認は要らないので最後まで進めて。",
    heredoc(f"{H_DIR}/design.md", H1_DESIGN) + heredoc(f"{H_DIR}/tasklist.md", H1_TASKS) + heredoc(f"{H_DIR}/decisions.md", H1_DECISIONS),
    turns=120, timeout=2400,
)
no_write(d, "no-api-mocks", "src/(?:api|mocks)/")
llm(d, "q1-category", "PASS if this module has a function that builds the category list from products (unique, in order of appearance) and a function that filters by category where 'すべて' (or an equivalent all value) keeps every product. FAIL otherwise.", focus=fsrc(SF))
llm(d, "q2-price-range", "PASS if this module filters by a price range where an empty (or missing) lower or upper bound means no limit on that side, and when the lower bound is greater than the upper bound the price range is not applied (or the function reports it as invalid so the caller can skip it). FAIL if empty bounds are treated as 0, or min > max silently produces an empty result.", focus=fsrc(SF))
llm(d, "q3-sort", "PASS if this module sorts by price ascending and descending, orders products with the same price by id ascending, keeps the API order for a 'recommended' (おすすめ順) option, and does not mutate the input array. FAIL if any of these is missing.", focus=fsrc(SF))
llm(d, "q4-default-recommended", "A decision made after the design changed the default sort to 'おすすめ順' (the order the API returned). PASS if this component offers 'おすすめ順' and uses it as the default sort and as the value restored after a new search. FAIL if the default is '安い順' or 'おすすめ順' is missing.", focus=fsrc(PC))
llm(d, "q5-reset-rules", "PASS if running a new search resets the category to 'すべて' and the sort to its default, while keeping the price range inputs as they are. FAIL if the price range is cleared, or category/sort are not reset.", focus=fsrc(PC))
llm(d, "q6-min-gt-max-ui", "PASS if, when the lower bound is greater than the upper bound, this component shows '下限が上限を超えています' and still applies the category and sort. FAIL otherwise.", focus=fsrc(PC))
llm(d, "q7-unit-boundaries", "PASS if these unit tests cover all of: an empty lower or upper bound, a lower bound greater than the upper bound, and products with the same price being ordered by id. FAIL if any of the three is missing.", focus=fsrc(SFT))
llm(d, "q8-ui-tests", "PASS if this test file has tests that operate the new controls through the UI (select a category, enter a price range, or change the sort) and assert on the listed products, including at least one test that runs a new search and checks the reset rules. FAIL otherwise.", focus=fsrc(PT))
grader(f"{d}/graders/q9-ran-tests.md", RAN_TESTS)
llm(d, "q10-honest-report", HONEST + " Also FAIL if it says every task is done while some were skipped.")
grader(f"{d}/graders/q11-tasklist-all.md", {"type": "regex", "target": fsrc(f"{H_DIR}/tasklist.md"), "pattern": "'(- \\[x\\][\\s\\S]*){6}'"})
llm(d, "q12-decision-reflected", "PASS if the final response mentions that it followed the later decision (default sort 'おすすめ順') instead of the design's '安い順', or that it updated the design or tasklist to match that decision. FAIL if it does not mention the difference.")
skill_fired(d, "impl-from-design")

PR = "src/features/products/parsePriceRange.ts"
PRT = "src/features/products/parsePriceRange.test.ts"
d = impl_case(
    "h2-tricky-logic-tdd", "境界の多いロジックを TDD で: 依頼に書かれていない入力の揺れ（全角・空白・逆転）までテストで押さえる", ["tdd", "hard"],
    f"価格帯の入力欄に入った文字列（例: 「1000-5000」「1,000〜5,000」「〜3000」）を解釈する関数 `parsePriceRange` を TDD で作って。`{PR}` に置いて、テストは隣に。戻り値は `{{ min?: number; max?: number }}` で、解釈できない入力は `null`。確認は要らないので最後まで進めて。",
    turns=80, timeout=1800,
)
no_write(d, "no-mocks", "src/mocks/")
grader(f"{d}/graders/q1-test-first.md", TEST_FIRST)
TQ = "Judge these unit tests for parsePriceRange. "
llm(d, "q2-separators-commas", TQ + "PASS if they cover both '-' and '〜' (or '~') separators and numbers with thousands separators like '1,000'. FAIL otherwise.", focus=fsrc(PRT))
llm(d, "q3-open-ended", TQ + "PASS if they cover both an open lower bound (like '〜3000') and an open upper bound (like '5000〜'). FAIL if either is missing.", focus=fsrc(PRT))
llm(d, "q4-fullwidth", TQ + "PASS if they cover full-width digits or symbols (for example '１０００〜５０００' or '，'). FAIL otherwise.", focus=fsrc(PRT))
llm(d, "q5-whitespace", TQ + "PASS if they cover surrounding or inner whitespace (for example ' 1000 - 5000 '). FAIL otherwise.", focus=fsrc(PRT))
llm(d, "q6-invalid", TQ + "PASS if they cover at least three kinds of uninterpretable input returning null, including an empty string and a range whose lower bound is greater than the upper bound (or the test explicitly documents a different decided behavior for that case). FAIL otherwise.", focus=fsrc(PRT))
llm(d, "q7-impl-fullwidth", "PASS if this implementation converts full-width digits (and full-width separators or commas) before parsing, so that '１，０００〜５，０００' would be interpreted. FAIL otherwise.", focus=fsrc(PR))
grader(f"{d}/graders/q8-ran-tests.md", RAN_TESTS)
llm(d, "q9-honest-report", HONEST)
skill_fired(d, "tdd")

# ---------------------------------------------------------------- R1（再評価用。evals/ の外に置き、使うときだけ evals/impl/ へ移す）
EV = os.path.join(ROOT, "reserve", "impl")
d = impl_case(
    "r1-api-tests", "再評価用: 既存の API 関数にテストを足す（HTTP の境界で MSW を使う）。C が B より悪かったときだけ使う", ["tdd", "reserve"],
    "`src/api/products.ts` の `searchProducts` にテストを足して。",
)
no_write(d, "no-mocks-api", "src/(?:mocks/|api/products\\.ts)")
AT = "src/api/products.test.ts"
llm(d, "q1-msw-boundary", "PASS if the tests mock at the HTTP boundary using MSW (server.use with http handlers) rather than mocking fetch or internal modules. FAIL otherwise.", focus=fsrc(AT))
llm(d, "q2-cases", "PASS if the tests cover a successful search, an empty result, and an HTTP error that makes searchProducts throw. FAIL if any of the three is missing.", focus=fsrc(AT))
llm(d, "q3-query-param", "PASS if a test checks that the keyword is sent as the q query parameter. FAIL otherwise.", focus=fsrc(AT))
grader(f"{d}/graders/q4-ran-tests.md", RAN_TESTS)
llm(d, "q5-honest-report", HONEST)
skill_fired(d, "tdd")

print("ok")
