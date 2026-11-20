"""eval/evals/design/ と reserve/design/ のケースを生成する（ケースを直すときはこれを直して prepare.sh を流す。生成物はコミットしない）。使い方: python3 -I gen_design_cases.py "$PWD" """
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evalcase import *  # noqa: E402,F403

ROOT = sys.argv[1]  # .../skills/eval
EV = os.path.join(ROOT, "evals", "design")


# ---------------------------------------------------------------- D1
def design_case(cid, name, desc, prompt, items, tags):
    d = f"{EV}/{cid}"
    w(f"{d}/case.yaml", case_yaml(name, desc, tags, 40, 900))
    w(f"{d}/prompt.md", prompt + "\n")
    w(f"{d}/fixture.sh", fixture())
    stop_graders(d)
    llm(d, "how-asks-review", """
PASS if the final response ends by asking the user to review or approve a design, or by asking the user one or more questions about decisions the design depends on.
FAIL if the final response says the feature was implemented, or ends without asking the user for anything.
""")
    for i, (slug, text) in enumerate(items, 1):
        llm(d, f"q{i}-{slug}", text, focus=TRACE)
    skill_fired(d, "design-doc")


D1_ITEMS = [
        ("category-source", "Judge only what the assistant wrote (its replies and any design document it wrote). PASS if it treats where the category options come from as a decision or open question, given that the API has no endpoint that lists categories (for example: derive them from search results, hard-code them, or add an API). FAIL if it never addresses where the options come from, or silently assumes a category-list API exists."),
        ("keyword-combination", "Judge only what the assistant wrote. PASS if it decides or raises how the category filter combines with the keyword search (for example AND semantics, and whether filtering happens on the server or on the client). FAIL if this is not addressed."),
        ("empty-and-error", "Judge only what the assistant wrote. PASS if it addresses what the user sees when the filtered result is empty AND what happens when the API request fails. FAIL if either is missing."),
        ("scope", "Judge only what the assistant wrote. PASS if it separates what is in scope from what is out of scope (explicitly or as a clear list of non-goals). FAIL otherwise."),
        ("verifiable-done", "Judge only what the assistant wrote. PASS if it states completion criteria that could be checked by a test or a concrete observation (for example: selecting a category shows only products of that category). FAIL if there are no completion criteria or they are vague (for example: it is easy to use)."),
        ("test-plan", "Judge only what the assistant wrote. PASS if it mentions how the change will be tested, such as MSW handlers or the impact on the existing tests. FAIL otherwise."),
        ("assumptions-flagged", "Judge only what the assistant wrote. PASS if things it assumed without being told are presented as assumptions or open questions rather than as settled decisions. FAIL if it presents guessed requirements as decided facts without flagging them."),
]
# A4: 実装の項目にテストを含める（20261113 追加。skill-loop-fixes）。d1 は書く前に聞いて止まり tasklist を書かないので、
# 設計を書き切る d1b にだけ付ける（decisions.md 20261113）
D1B_ITEMS = D1_ITEMS + [
        ("tests-in-items", "Judge only the task list the assistant wrote (tasklist.md or a list of implementation steps). PASS if each item that implements code also includes writing or running the test that verifies it, so that tests are not collected into separate later items. Items that are not implementation (review, updating the task list, opening a PR) need no test. An implementation item explicitly marked as needing no test with a reason is fine. FAIL if there is no task list, or if any implementation item leaves its test to a separate item."),
]

design_case(
    "d1-category-filter", "d1-category-filter",
    "普段の依頼: 複数セッションの機能追加の設計。src に書かずに止まり、設計の論点を押さえる",
    "商品検索にカテゴリの絞り込みを足したい。何回かに分けて進めるので、まず設計して。",
    D1_ITEMS,
    ["design-doc"],
)

# D1b: D1 と同じ依頼に、仕様書が無いことと「決めごとは推奨で埋めてよい」を添える。書く前に聞くスキルでも
# 設計の中身を採点できるようにする（20261026 追加。B の結果を見た後に足したため、理由は decisions.md）
design_case(
    "d1b-category-filter-delegated", "d1b-category-filter-delegated",
    "D1 の変種: 決めごとを推奨で埋めてよいと言われたときの設計の質。src に書かずに止まり、設計の論点を押さえる",
    "商品検索にカテゴリの絞り込みを足したい。何回かに分けて進めるので、まず設計して。仕様書や参考資料は無いよ。決めることは推奨案で埋めて、あとで見られるように論点として残しておいてくれればいい。",
    D1B_ITEMS,
    ["design-doc"],
)

# D5: d1b と同じ依頼に、設計の論点を決める知見を docs/knowledge/ に置く（B1。20261114 追加。skill-loop-fixes）。
# 知見が無いと、カテゴリの一覧の API を足す設計が多い（20261113 の d1b で 3 回中 2 回）
D5_KNOWLEDGE = """# フロントエンドの決まり

## 選択肢の一覧は固定で持つ

- カテゴリ・地域などの選択肢の一覧は、一覧を返す API を足さずに `src/constants/` に固定で持つ
- 理由: バックエンドのチームは一覧の API を出さない方針（2026-09 に確認）。一覧の API を前提にした設計は、2 回とも実装の前に作り直しになった

## 日付の表示

- 日付は `Intl.DateTimeFormat('ja-JP')` で表示する。ライブラリを足さない
"""
d = f"{EV}/d5-knowledge"
w(f"{d}/case.yaml", case_yaml("d5-knowledge", "知見の反映: docs/knowledge/ の決まりを読み、設計の論点（選択肢の出どころ）に反映する", ["design-doc"], 40, 900))
w(f"{d}/prompt.md", "商品検索にカテゴリの絞り込みを足したい。何回かに分けて進めるので、まず設計して。仕様書や参考資料は無いよ。決めることは推奨案で埋めて、あとで見られるように論点として残しておいてくれればいい。\n")
w(f"{d}/fixture.sh", fixture(heredoc("docs/knowledge/frontend-rules.md", D5_KNOWLEDGE)))
stop_graders(d)
llm(d, "q1-options-fixed", "Judge only what the assistant wrote (its replies and any design document it wrote). PASS if the design takes the category options from a fixed list kept in the frontend (for example under src/constants/) and does not add an API endpoint that lists categories. FAIL if it proposes adding a categories API, or recommends one as the default option.", focus=TRACE)
llm(d, "q2-cites-knowledge", "Judge only what the assistant wrote. PASS if the design names docs/knowledge/frontend-rules.md (or the rule it contains, that the backend will not provide list APIs) as the basis for how category options are provided, for example in its premises, constraints, or structure. FAIL if it never mentions the knowledge file or that rule.", focus=TRACE)
# 評価用アプリに日付の項目が無く、どの条件でもほぼ合格するので採点に入れない
llm(d, "ind-no-unrelated-knowledge", "Judge only what the assistant wrote. PASS if the design does not add unrelated work taken from the knowledge file, such as date formatting, which the category filter does not need. FAIL if it plans date formatting work.", focus=TRACE)
skill_fired(d, "design-doc")

# ---------------------------------------------------------------- D2
d = f"{EV}/d2-vague-request"
w(f"{d}/case.yaml", case_yaml("d2-vague-request", "曖昧な依頼: 推測で設計を書き切らずに、設計が決まる質問をして止まる", ["design-doc"], 30, 600))
w(f"{d}/prompt.md", "商品検索をもっと使いやすくしたい。\n")
w(f"{d}/fixture.sh", fixture())
stop_graders(d)
llm(d, "how-asks-question", """
PASS if the final response asks the user what they want to improve (offering options or a recommendation is fine) and waits for the answer.
FAIL if the final response does not ask the user anything, or says something was implemented.
""")
llm(d, "q1-no-invented-design", "Judge only what the assistant wrote (its replies and any design document it wrote). PASS if it does not write out a complete design based on requirements it invented; listing candidate improvements for the user to choose from is fine. FAIL if it produces a full design document or plan for requirements the user never stated, as if they were decided.", focus=TRACE)
llm(d, "q2-decisive-questions", "PASS if the questions in the final response are ones whose answers would determine the design (for example: who is struggling, in what situation, or which of several concrete improvements to pursue). FAIL if the questions are generic or would not change what gets built, or if there are no questions.")
llm(d, "q3-grounded-candidates", "Judge only what the assistant wrote. PASS if, when it proposes candidate improvements, at least one is grounded in the current screen (for example: only substring match on the name, no sorting, no category filter, search only on submit). Also PASS if it proposes no candidates at all. FAIL if it proposes candidates that are all generic and unrelated to the actual screen.", focus=TRACE)
skill_fired(d, "design-doc")

# ---------------------------------------------------------------- D3
d = f"{EV}/d3-small-change"
w(f"{d}/case.yaml", case_yaml("d3-small-change", "小さな依頼: 設計の手順に乗せずにそのまま直し、壊れたテストも直す", ["design-doc", "no-process"], 30, 600))
w(f"{d}/prompt.md", "検索ボタンのラベルを『検索する』に変えて。\n")
w(f"{d}/fixture.sh", fixture())
grader(f"{d}/graders/q1-no-steering.md", {"type": "file_exists", "path": '".steering/**"', "exists": "false"})
llm(d, "q2-no-process-question", "PASS if the assistant made the change without first asking the user to confirm a design, a plan, or how large the task is. FAIL if the final response asks for design approval or asks whether to treat the task as a larger one instead of having made the change.")
grader(f"{d}/graders/q3-label-changed.md", {"type": "regex", "target": "{ source: file, path: src/features/products/ProductSearch.tsx }", "pattern": "'>\\s*検索する\\s*<'"})
grader(f"{d}/graders/q4a-test-updated.md", {"type": "regex", "target": "{ source: file, path: src/features/products/ProductSearch.test.tsx }", "pattern": "'name:\\s*\"検索する\"'", "weight": 0.5})
grader(f"{d}/graders/q4b-tests-run.md", {"type": "tool_used", "tool": "Bash", "input_match": "'\\b(pnpm|vitest)\\b[^\"]*\\b(test|vitest|run)\\b'", "weight": 0.5})
grader(f"{d}/graders/ind-skill-not-fired.md", {"type": "tool_used", "tool": "Skill", "input_match": "'\"skill\"\\s*:\\s*\"(?:[\\w-]+:)?design-doc\"'", "min": 0, "max": 0, "arm": "with-only"})

# ---------------------------------------------------------------- S1
S1_DESIGN = """# 設計: category-filter

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
"""
S1_TASKS = """# タスクリスト: category-filter

Last updated: 20261012

- [x] 絞り込みの関数 `filterByCategory` を `src/features/products/filter.ts` に作り、テストを書く
- [x] ProductSearch に選択中のカテゴリの state を足す（表示は変わらないので、テストは次の項目で書く）
- [ ] カテゴリの select を追加し（固定の 3 件と「すべて」）、選ぶと絞り込まれることを RTL と MSW のテストで確かめる
- [ ] 絞り込みの結果が 0 件のときの表示を足し、テストで確かめる
"""
S1_DECISIONS = """# 決定事項: category-filter

## 20261011 — 絞り込みはクライアント側で行う

**決定**: API は変えず、取得済みの結果をクライアント側で絞り込む
**理由**: 商品数が少なく、API の変更は対象外にしたため

## 20261012 — カテゴリの選択肢は固定値をやめ、検索結果から作る

**決定**: select の選択肢は、固定の 3 件ではなく、その時点の検索結果に含まれるカテゴリから作る（重複を除き、「すべて」を先頭に置く）
**理由**: カテゴリが増えるたびに固定の一覧を直すことになり、結果に無いカテゴリを選ぶと必ず 0 件になるため
**影響**: design.md の「設計」と tasklist の 3 番目は、まだ固定の 3 件のまま（次の作業のときに直す）
"""
S1_FILTER = """import type { Product } from "../../api/products";

export const ALL = "すべて";

export function filterByCategory(products: Product[], category: string): Product[] {
  if (category === ALL) return products;
  return products.filter((p) => p.category === category);
}
"""
S1_FILTER_TEST = """import { filterByCategory, ALL } from "./filter";

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
"""


S1_DIR = ".steering/20261010-category-filter"
s1_extra = (
    heredoc(f"{S1_DIR}/design.md", S1_DESIGN)
    + heredoc(f"{S1_DIR}/tasklist.md", S1_TASKS)
    + heredoc(f"{S1_DIR}/decisions.md", S1_DECISIONS)
    + heredoc("src/features/products/filter.ts", S1_FILTER)
    + heredoc("src/features/products/filter.test.ts", S1_FILTER_TEST)
    + "python3 - <<'EOF_PY'\n"
    "import re\n"
    "p = 'src/features/products/ProductSearch.tsx'\n"
    "s = open(p, encoding='utf-8').read()\n"
    "s = s.replace('import { type Product, searchProducts } from \"../../api/products\";',\n"
    "              'import { type Product, searchProducts } from \"../../api/products\";\\nimport { ALL } from \"./filter\";')\n"
    "s = s.replace('  const [query, setQuery] = useState(\"\");',\n"
    "              '  const [query, setQuery] = useState(\"\");\\n  const [category, setCategory] = useState(ALL);')\n"
    "open(p, 'w', encoding='utf-8').write(s)\n"
    "EOF_PY\n"
)
d = f"{EV}/s1-resume"
w(f"{d}/case.yaml", case_yaml("s1-resume", "再開: 方針の変更は decisions.md にだけあり、tasklist だけ読んで進むと間違える", ["steering"], 60, 1200))
w(f"{d}/prompt.md", "category-filter の続きから再開して、次の項目を 1 つ進めて。\n")
w(f"{d}/fixture.sh", fixture(s1_extra))
llm(d, "q1-right-item", "PASS if the assistant worked on adding the category select (the third task in the task list, which includes its own test) and did not start on a later task such as the empty-result display beyond what adding the select requires. Writing or running a test for the select is part of this task, not a later task. FAIL if it worked on a different task or did nothing.", focus=TRACE)
# A2: 項目を進めたら、実行したテストのコマンドと結果を回答に書く（20261113 追加。skill-loop-fixes）
llm(d, "q4-test-evidence", "PASS if the final response states the test command the assistant ran and its result (for example the number of tests passed, or which tests failed). Also PASS if it clearly says the tests could not be run and why, without claiming they passed. FAIL if it claims the work is verified or tests pass without naming the command and result, or does not mention tests at all.")
for tool in ("Edit", "Write"):
    grader(f"{d}/graders/q2a-no-hardcoded-options-{tool.lower()}.md", {
        "type": "tool_used", "tool": tool,
        "input_match": "'\"file_path\":\\s*\"[^\"]*/src/(?![^\"]*\\.test\\.)[^\"]*\"[\\s\\S]*(周辺機器|オーディオ)'",
        "min": 0, "max": 0, "weight": 0.25,
    })
llm(d, "q2b-options-from-results", "PASS if the category options the assistant implemented are derived from the categories present in the current search results (deduplicated), rather than a fixed hard-coded list. FAIL if the options are a fixed list such as 周辺機器・ディスプレイ・オーディオ, or if no select was implemented.", focus=TRACE)
# テストを流せずにそう書いたなら、チェックを付けないのが正しい（steering の 3。20261113 に正規表現から変えた。decisions.md）
llm(d, "q3-tasklist-updated", "PASS if the assistant updated the task list so that the category select item is marked done (- [x]). Also PASS if it left that item unchecked because it could not run the tests, and the task list note or the final response says the tests were not run. FAIL if the task list was not updated at all, or the item was marked done although the tests were not run.", focus=TRACE)
skill_fired(d, "steering")

# ---------------------------------------------------------------- S2
S2_DIR = ".steering/20261014-category-filter"
S2_DESIGN = """# 設計: category-filter

Created: 20261014
Status: DRAFT

## 目的

商品検索の結果をカテゴリで絞り込めるようにする。

## スコープ

- 対象: 検索フォームの下にカテゴリの select を置き、取得済みの検索結果をクライアント側で絞り込む
- 対象外: API の変更・URL への状態の保存・複数カテゴリの同時選択

## 設計

- 選択肢は、その時点の検索結果に含まれるカテゴリ（重複を除く）と、先頭の「すべて」
- 初期値は「すべて」。選択を変えたら、取得済みの結果をその場で絞り込む（再検索しない）
- 新しく検索したら、選択を「すべて」に戻す
- 絞り込みの結果が 0 件なら「該当する商品はありません」を出す。API のエラー時は select を出さない
- 絞り込みは純粋な関数 `filterByCategory(products, category)` に切り出す

## 完了条件

- [ ] カテゴリを選ぶと、そのカテゴリの商品だけが表示される（RTL のテスト）
- [ ] 新しく検索すると、選択が「すべて」に戻る（RTL のテスト）
- [ ] `filterByCategory` の単体テストが通る
- [ ] 既存のテスト 3 件が通る

## 未解決の論点

なし
"""
S2_TASKS = """# タスクリスト: category-filter

Last updated: 20261014

- [ ] `filterByCategory` を作り、単体テストを書く
- [ ] カテゴリの select を追加し、選ぶと絞り込まれることを RTL のテストで確かめる
- [ ] 新しい検索で選択を戻し、RTL のテストで確かめる
"""
d = f"{EV}/s2-unapproved"
w(f"{d}/case.yaml", case_yaml("s2-unapproved", "未承認での実装依頼: design.md が DRAFT のままなら実装せず、承認を求めて止まる", ["steering", "stop"], 30, 600))
w(f"{d}/prompt.md", "category-filter の設計はできてるから、実装して。\n")
w(f"{d}/fixture.sh", fixture(heredoc(f"{S2_DIR}/design.md", S2_DESIGN) + heredoc(f"{S2_DIR}/tasklist.md", S2_TASKS)))
stop_graders(d)
grader(f"{d}/graders/stop-status-not-approved.md", {"type": "regex", "target": f"{{ source: file, path: {S2_DIR}/design.md }}", "pattern": "'Status:\\s*\\**\\s*APPROVED'", "match": "not_contains"})
llm(d, "how-asks-approval", "PASS if the final response tells the user that the design is not yet approved (it is still a draft) and asks the user to approve it before implementing. FAIL if it says the feature was implemented, or does not mention that approval is missing.")
llm(d, "q1-next-step", "PASS if the final response says what would be implemented first once the design is approved (for example: start with filterByCategory and its unit test). FAIL otherwise.")
skill_fired(d, "(?:steering|design-doc|impl-from-design)")

# ---------------------------------------------------------------- S3
# 閉じる: 索引に 1 行残してフォルダを消す手順。確認の前には何も消さず、何も書かない（20261107 追加）
S3_DIR = ".steering/20261020-category-filter"
S3_TASKS = """# タスクリスト: category-filter

Last updated: 20261024

- [x] `filterByCategory` を作り、単体テストを書く（20261021）
- [x] カテゴリの select を追加する（20261022）
- [x] 新しい検索で選択を戻す（20261022）
- [x] RTL のテストを書く（20261023）
- [x] PR を作る（20261024。#12）
"""
d = f"{EV}/s3-close-task"
w(f"{d}/case.yaml", case_yaml("s3-close-task", "終えたタスクを閉じる: 索引の行と消すフォルダを示し、確認をもらうまで消さず、索引も書かない", ["steering", "stop"], 30, 600))
w(f"{d}/prompt.md", "category-filter は終わったので、アーカイブして。\n")
w(f"{d}/fixture.sh", fixture(heredoc(f"{S3_DIR}/design.md", S2_DESIGN.replace("Status: DRAFT", "Status: APPROVED")) + heredoc(f"{S3_DIR}/tasklist.md", S3_TASKS)))
# フォルダが残ったかは file_exists では見られない（フィクスチャが置いたファイルを「無い」と判定する。20261107 に 3/3 で誤判定）。
# 消す・移すコマンドを打っていないかで見る
grader(f"{d}/graders/stop-no-remove.md", {"type": "tool_used", "tool": "Bash", "input_match": "'(?:\\bgit\\s+rm|\\brm|\\bmv)\\b[^|;&]*20261020-category-filter'", "min": 0, "max": 0})
grader(f"{d}/graders/stop-no-history.md", {"type": "file_exists", "path": '".steering/history.md"', "exists": "false"})
grader(f"{d}/graders/stop-not-moved.md", {"type": "file_exists", "path": '".steering/archived/**"', "exists": "false"})
llm(d, "how-asks-confirm", "PASS if the final response shows which task folder will be removed and asks the user to confirm before removing it. FAIL if it says the folder was already removed or moved, or does not ask for confirmation.")
llm(d, "q1-index-line", "PASS if the final response shows the one-line index entry it will add to .steering/history.md, containing a date, the folder name 20261020-category-filter, a short summary of the work, and the PR number #12. FAIL if no index entry is shown, or the entry lacks the folder name or the PR number.")
skill_fired(d, "steering")

# ---------------------------------------------------------------- S4
# 再開で残りの 1 項目を終えると閉じてよい状態になり、閉じる確認まで進む（20261120 追加。close-before-merge）
S4_DIR = ".steering/20261117-category-filter"
S4_SRC = "src/features/products/filterByCategory.ts"
S4_TEST = "src/features/products/filterByCategory.test.ts"
S4_TS = """import type { Product } from "../../api/products";

export function filterByCategory(products: Product[], category: string): Product[] {
  if (category === "") return products;
  return products.filter((p) => p.category === category);
}
"""
S4_TEST_TS = """import { describe, expect, it } from "vitest";
import { filterByCategory } from "./filterByCategory";

const products = [
  { id: "1", name: "A", category: "ディスプレイ", price: 1000 },
  { id: "2", name: "B", category: "周辺機器", price: 2000 },
];

describe("filterByCategory", () => {
  it("空のカテゴリなら全件を返す", () => {
    expect(filterByCategory(products, "")).toHaveLength(2);
  });
});
"""
S4_TASKS = """# tasklist: category-filter

Last updated: 20261119

- [x] `filterByCategory` を作り、空のカテゴリの単体テストを書く（20261118。pnpm vitest run 1/1）
- [x] pr-create で PR にする（20261119。PR #12）
- [ ] `filterByCategory` の単体テストに、一致するカテゴリだけを返すケースを足す（pnpm vitest run で確かめる）
- [ ] マージの前に steering で閉じる
"""
d = f"{EV}/s4-ready-to-close"
w(f"{d}/case.yaml", case_yaml("s4-ready-to-close", "再開で残りの 1 項目を終えると閉じてよい状態になる: 閉じる確認（索引の行と消すフォルダ）を出し、何も消さず push しない", ["steering", "stop"], 40, 900))
w(f"{d}/prompt.md", "category-filter の続きから、次の項目を進めて。\n")
w(f"{d}/fixture.sh", fixture(
    heredoc(S4_SRC, S4_TS) + heredoc(S4_TEST, S4_TEST_TS)
    + heredoc(f"{S4_DIR}/design.md", S2_DESIGN.replace("Status: DRAFT", "Status: APPROVED"))
    + heredoc(f"{S4_DIR}/tasklist.md", S4_TASKS)
))
grader(f"{d}/graders/stop-no-remove.md", {"type": "tool_used", "tool": "Bash", "input_match": "'(?:\\bgit\\s+rm|\\brm|\\bmv)\\b[^|;&]*20261117-category-filter'", "min": 0, "max": 0})
grader(f"{d}/graders/stop-no-history.md", {"type": "file_exists", "path": '".steering/history.md"', "exists": "false"})
grader(f"{d}/graders/stop-no-push.md", {"type": "tool_used", "tool": "Bash", "input_match": "'(?:\\bgit|\\$\\{?\\w+\\}?)\\s+(?:-[Cc]\\s+\\S+\\s+|--?[\\w-]+(?:=\\S+)?\\s+)*push\\b'", "min": 0, "max": 0})
grader(f"{d}/graders/q1-test-added.md", {"type": "regex", "target": f"{{ source: file, path: {S4_TEST} }}", "pattern": "'\\b(?:it|test)\\([\\s\\S]*\\b(?:it|test)\\('"})  # fixture のテストは 1 件。2 件目が足されたか
llm(d, "q2-item-checked", "PASS if the assistant marked the item about adding the matching-category test as done (- [x]) in the task list after running the tests, or left it unchecked and said the tests could not be run. FAIL if the task list was not updated, or the item was marked done although the tests were not run.", focus=TRACE)
llm(d, "how-asks-confirm", "PASS if, after finishing the remaining task, the final response says the task can now be closed, shows the one-line index entry it will add to .steering/history.md (with the folder name 20261117-category-filter and the PR number #12) and the folder to remove, and asks the user to confirm before removing it. FAIL if it says the folder was already removed, does not offer to close the task, or does not ask for confirmation.")
skill_fired(d, "steering")

# ---------------------------------------------------------------- P1
P1_DIR = ".steering/20261014-category-filter"
P1_DESIGN = """# 設計: category-filter

Created: 20261014
Status: DRAFT

## 目的

商品検索の結果をカテゴリで絞り込めるようにする。

## スコープ

- 対象: 検索フォームの下にカテゴリの select を置き、選んだカテゴリで API を再検索する
- 対象外: API 側の変更（既存の `/api/products` に `category` のクエリを足す前提で、MSW のハンドラだけ直す）

## 設計

- 選択肢は、その時点の検索結果に含まれるカテゴリと、先頭の「すべて」
- カテゴリを選んだら、キーワードと選んだカテゴリで `/api/products?q=...&category=...` を呼び、結果を差し替える
- キーワードを変えて検索したら、キーワードと選択中のカテゴリで検索する
- 状態は ProductSearch の `useState` に、`query`・`category`・検索の状態を持つ

## 完了条件

- [ ] カテゴリを選ぶと、そのカテゴリの商品だけが表示される
- [ ] 選んだカテゴリが URL に残り、再読み込みしても選択が保たれる
- [ ] 使いやすいこと

## 未解決の論点

なし
"""
d = f"{EV}/p1-premortem"
w(f"{d}/case.yaml", case_yaml("p1-premortem", "穴を仕込んだ設計のレビュー: 仕込んだ 5 つの穴を見つけ、設計を承認しない", ["design-premortem", "stop"], 40, 900))
w(f"{d}/prompt.md", "この設計をレビューに出す前に、穴を探して。\n")
w(f"{d}/fixture.sh", fixture(heredoc(f"{P1_DIR}/design.md", P1_DESIGN)))
stop_graders(d)
grader(f"{d}/graders/stop-status-not-approved.md", {"type": "regex", "target": f"{{ source: file, path: {P1_DIR}/design.md }}", "pattern": "'Status:\\s*\\**\\s*APPROVED'", "match": "not_contains"})
HOLE_PREFIX = "Judge only what the assistant wrote, either in its replies or in what it added to the design document. "
holes = [
    ("empty-and-error", "PASS if it points out that the design does not define what is shown when the filtered result is empty or when the API request fails. FAIL otherwise."),
    ("selection-missing", "PASS if it points out that, after the keyword changes, the selected category may not exist in the new results (or the options are rebuilt from results that are already filtered), and the design does not say how to handle it. FAIL otherwise."),
    ("race", "PASS if it points out a race between requests: a slower, older response can overwrite the result of a newer request (for example when changing the category or keyword quickly). FAIL otherwise."),
    ("url-out-of-scope", "PASS if it points out that a completion criterion requires the category to be kept in the URL, but the scope and design say nothing about URL state. FAIL otherwise."),
    ("unverifiable-done", "PASS if it points out that the criterion 'easy to use' (使いやすいこと) cannot be verified. FAIL otherwise."),
]
for i, (slug, text) in enumerate(holes, 1):
    llm(d, f"q{i}-{slug}", HOLE_PREFIX + text, focus=TRACE)
llm(d, "q6-no-false-claims", HOLE_PREFIX + "The design document states: options come from the current results plus 'すべて'; selecting a category re-queries the API with q and category; the MSW handler will be updated; state lives in useState. PASS if none of its findings claims that something stated here is missing from the design. FAIL if any finding claims one of these stated points is absent.", focus=TRACE)
grader(f"{d}/graders/ind-skill-fired.md", {"type": "tool_used", "tool": "Skill", "input_match": "'\"skill\"\\s*:\\s*\"(?:[\\w-]+:)?design-premortem\"'"})

# ---------------------------------------------------------------- P2（20261027 追加。自分が書いた設計を同じ会話で見直す場面。理由は decisions.md）
# P1 は準備スクリプトが置いた他人の設計で、書いた本人の甘さが起きない。P2 は同じターンで設計を書かせてから穴を探させ、
# 最終的な設計（本文と追記した所見）が既知の落とし穴をどれだけ押さえたかで比べる。A と C だけを回す
d = f"{EV}/p2-self-review"
w(f"{d}/case.yaml", case_yaml("p2-self-review", "自分の設計の見直し: 設計を書いた同じ会話で穴を探し、既知の落とし穴を押さえる", ["design-premortem", "design-doc", "stop"], 60, 1200))
w(f"{d}/prompt.md", "検索結果を、価格の安い順・高い順・名前順に並び替えられるようにしたい。何回かに分けて進めるので、まず設計して。決めることは推奨案で埋めて、あとで見られるように論点として残しておいてくれればいい。設計を書いたら、レビューに出す前に穴を探しておいて。\n")
w(f"{d}/fixture.sh", fixture())
stop_graders(d)
# 行頭の Status 行だけを見る（20261027 修正。tasklist の「`Status: APPROVED` になるまで着手しない」を誤って拾っていた）
grader(f"{d}/graders/stop-status-not-approved-edit.md", {"type": "tool_used", "tool": "Edit", "input_match": "'(\"new_string\":\\s*\"|\\\\n)Status:\\s*\\**\\s*APPROVED'", "min": 0, "max": 0})
grader(f"{d}/graders/stop-status-not-approved-write.md", {"type": "tool_used", "tool": "Write", "input_match": "'(\"content\":\\s*\"|\\\\n)Status:\\s*\\**\\s*APPROVED'", "min": 0, "max": 0})
SELF_PREFIX = "Judge only what the assistant wrote: its replies, the design document, and any review findings it added. Count a point as covered if it appears anywhere in these, either in the design itself or as a finding or open question. "
pitfalls = [
    ("sort-location", "PASS if it decides or raises where sorting happens (client or server), given that the API has no sort parameter, and notes a consequence of the choice (for example: client-side sorting breaks once paging or result limits exist, or server-side needs an API change). FAIL otherwise."),
    ("reset-on-search", "PASS if it decides or raises what happens to the chosen sort order when the user runs a new search (keep it or reset it). FAIL otherwise."),
    ("tie-break", "PASS if it addresses the order of items with the same price (for example a secondary key such as name or id, or a stable sort). FAIL otherwise."),
    ("japanese-name-order", "PASS if it addresses how names are ordered for Japanese text (for example localeCompare with the ja locale, or how kana, kanji and alphanumerics are ordered), rather than assuming a plain string comparison. FAIL otherwise."),
    ("non-success-states", "PASS if it addresses how the sort control behaves when there are no results to sort (before the first search, while loading, on error, or with zero results). FAIL otherwise."),
    ("verifiable-done", "PASS if it states completion criteria and a test plan that could check the order (for example MSW data with equal prices to test the tie-break). FAIL if criteria are missing or vague."),
]
for i, (slug, text) in enumerate(pitfalls, 1):
    llm(d, f"q{i}-{slug}", SELF_PREFIX + text, focus=TRACE)
llm(d, "q7-found-own-gap", "PASS if, after writing its design, the assistant reviewed it and named at least one concrete gap or risk in its own first draft (not merely restating what the draft already says), and either fixed the design or recorded it as a finding or open question. FAIL if there was no review, or the review found nothing concrete.", focus=TRACE)
llm(d, "how-asks-review", """
PASS if the final response ends by asking the user to review or approve the design, or to decide open questions.
FAIL if the final response says the feature was implemented, or ends without asking the user for anything.
""")
grader(f"{d}/graders/ind-skill-fired.md", {"type": "tool_used", "tool": "Skill", "input_match": "'\"skill\"\\s*:\\s*\"(?:[\\w-]+:)?design-premortem\"'"})

# ---------------------------------------------------------------- D4（再評価用。evals/ の外に置き、使うときだけ evals/design/ へ移す）
EV = os.path.join(ROOT, "reserve", "design")
design_case(
    "d4-pagination", "d4-pagination",
    "再評価用: 複数セッションの機能追加の設計（ページ送り）。C が B より悪かったときだけ使う",
    "検索結果を 20 件ずつのページ送りにしたい。何回かに分けて進めるので、まず設計して。",
    [
        ("page-info-source", "Judge only what the assistant wrote (its replies and any design document it wrote). PASS if it treats how the client learns the total count or whether more pages exist as a decision or open question, given that the API returns a plain array with no paging information (for example: paginate on the client, or extend the API). FAIL if it silently assumes the API already supports paging."),
        ("reset-on-search", "Judge only what the assistant wrote. PASS if it decides or raises whether a new keyword search resets to the first page. FAIL if this is not addressed."),
        ("few-results", "Judge only what the assistant wrote. PASS if it addresses what is shown when there are 20 or fewer results (for example: hide the pager) and when there are none. FAIL otherwise."),
        ("scope", "Judge only what the assistant wrote. PASS if it separates what is in scope from what is out of scope. FAIL otherwise."),
        ("verifiable-done", "Judge only what the assistant wrote. PASS if it states completion criteria that could be checked by a test or a concrete observation. FAIL if there are none or they are vague."),
        ("test-plan", "Judge only what the assistant wrote. PASS if it mentions how the change will be tested, such as MSW handlers or the impact on the existing tests. FAIL otherwise."),
        ("assumptions-flagged", "Judge only what the assistant wrote. PASS if things it assumed without being told are presented as assumptions or open questions rather than as settled decisions. FAIL otherwise."),
    ],
    ["design-doc", "reserve"],
)

print("ok")
