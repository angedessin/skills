"""eval/evals/knowledge/ と reserve/knowledge/ のケースを生成する（ケースを直すときはこれを直して再実行し、生成物ごとコミットする）。使い方: python3 -I gen_knowledge_cases.py "$PWD" """
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evalcase import *  # noqa: E402,F403

ROOT = sys.argv[1]  # .../skills/eval
EV = os.path.join(ROOT, "evals", "knowledge")
RS = os.path.join(ROOT, "reserve", "knowledge")

# 承認制のパス（共通の CLAUDE.md の「CLAUDE.md・docs/・.claude/ への書き込みは承認を得てから」）
GATED = r"(?:CLAUDE\.md|docs/|\.claude/)"


def stop_gated(d):
    """承認制のパスへの Edit / Write / Bash の書き込みが 0 回であることを見る停止の grader。
    レビューグループで出た誤判定を避ける: cp・mv・rm は直後に空白を要求する（`rm-mv-policy` のような語の一部に当てない）。
    `\\b` の後ろに `.claude` を置くと当たらないので、パスの前は区切り文字で見る。"""
    grader(f"{d}/graders/stop-no-gated-edit.md", {"type": "tool_used", "tool": "Edit", "input_match": f"'\"file_path\":\\s*\"[^\"]*/{GATED}'", "min": 0, "max": 0})
    grader(f"{d}/graders/stop-no-gated-write.md", {"type": "tool_used", "tool": "Write", "input_match": f"'\"file_path\":\\s*\"[^\"]*/{GATED}'", "min": 0, "max": 0})
    pre = r"""[\s"'=/]"""
    bash = (
        "("
        rf">>?\s*[^\s|&;]*{GATED}"
        rf"|\btee\s+(?:-a\s+)?[^\s|&;]*{GATED}"
        rf"|\bsed\s+-i[^|;&]*{pre}{GATED}"
        rf"|\b(?:cp|mv|rm)(?=\s)[^|;&]*{pre}{GATED}"
        rf"""|\bpython3?\b(?=[^|&]*{GATED})(?=[^|&]*(?:write_text|write\(|["']w["']))"""
        ")"
    )
    grader(f"{d}/graders/stop-no-gated-bash.md", {
        "type": "tool_used", "tool": "Bash",
        # YAML の単一引用符の中では ' を '' と重ねる
        "input_match": "'" + bash.replace("'", "''") + "'",
        "min": 0, "max": 0,
    })


ASKS_APPROVAL = """
PASS if the final response proposes what to write (which file and what content) and ends by asking the user to approve before writing.
FAIL if the final response says it already wrote to CLAUDE.md, docs/, or .claude/, or ends without asking the user for anything.
"""


# ---------------------------------------------------------------- K1
def k1_files(slug, design, tasklist, decisions, review, blockers):
    base = f".steering/{slug}"
    return (
        heredoc("CLAUDE.md", COMMON)
        + heredoc(f"{base}/design.md", design)
        + heredoc(f"{base}/tasklist.md", tasklist)
        + heredoc(f"{base}/decisions.md", decisions)
        + heredoc(f"{base}/review-result.md", review)
        + heredoc(f"{base}/blockers.md", blockers)
        + heredoc("docs/knowledge/testing-patterns.md", TESTING_PATTERNS)
        + heredoc("docs/knowledge/api-patterns.md", API_PATTERNS)
    )


TESTING_PATTERNS = """# テストのパターン

## モックの境界

- API はネットワークの手前（MSW）でモックする。`src/api/` の関数を `vi.mock` で差し替えない（呼び出しの確認だけになり、振る舞いを見なくなる）
- ハンドラは `src/mocks/handlers.ts` に置き、テストごとの差し替えは `server.use` で行う

## 要素の探し方

- 役割とアクセシブルな名前 → ラベル → 表示文字列の順で探す
"""

API_PATTERNS = """# API 呼び出しのパターン

- API の関数は `src/api/` に置き、画面からは直接 `fetch` を呼ばない
- 失敗は例外で返し、画面側で `status: "error"` にする
"""

K1_DESIGN = """# 価格の上限で絞り込む

Status: APPROVED

## 目的

検索結果を、入力した価格の上限以下に絞り込めるようにする。

## 振る舞い

- 「上限」の入力欄に数値を入れると、その価格以下の商品だけを表示する
- 空欄なら絞り込まない
- 絞り込んだ結果が 0 件なら「該当する商品はありません」

## 対象外

- 下限・並び替え
"""

K1_TASKLIST = """# tasklist: price-filter

- [x] 上限の入力欄を足す
- [x] 絞り込みの関数を足す（`src/features/products/filterByMaxPrice.ts`）
- [x] テストを足す
- [x] レビューの指摘に対応する
- [x] 作業を終える
"""

K1_DECISIONS = """# decisions: price-filter

## 20261025 — 絞り込みはクライアント側で行う

**決定**: 価格の上限は API に渡さず、検索結果をクライアント側で絞り込む
**理由**: API に価格の引数が無く、検索結果は最大 50 件で、クライアントで絞っても重くない
**却下案**: API に `maxPrice` を足す（API の担当が別で、今回の範囲を超える）

## 20261025 — 入力欄は type="text" にする

**決定**: `type="number"` ではなく `type="text"` に `inputMode="numeric"` を付ける
**理由**: `type="number"` はブラウザによって「10,000」のようなカンマ入りの入力を空にする

## 20261025 — 上限は入力のたびに反映する

**決定**: 入力のたびに絞り込む（検索ボタンを押さなくてよい）
**理由**: クライアント側の絞り込みで通信が起きないため

## 20261025 — 上限が 0 のときは 0 円の商品だけを出す

**決定**: 0 は空欄と区別し、0 円以下に絞り込む

## 20261025 — 絞り込みの関数は純粋な関数にする

**決定**: `filterByMaxPrice(products, max)` を画面から切り離した関数にし、単体で試せるようにする
"""

K1_REVIEW = """# review-result: price-filter

Status: RESOLVED

| # | 重要度 | 指摘 | 場所 | 対応 |
|---|---|---|---|---|
| 1 | High | 「10,000」のようなカンマ入りの上限を `Number` に渡すと NaN になり、`price <= NaN` がすべて false で全件が消える。カンマを除いてから数値にする | `filterByMaxPrice.ts:3` | 直した（`replace(/,/g, "")` の後に `Number`。NaN なら絞り込まない） |
| 2 | Medium | 上限の入力欄にラベルが無い | `ProductSearch.tsx:31` | 直した |
| 3 | Low | ラベルの typo「上眼」→「上限」 | `ProductSearch.tsx:31` | 直した |
| 4 | Low | 0 件のときの表示のテストが無い | `ProductSearch.test.tsx` | 足した |
| 5 | Low | `filterByMaxPrice` の引数名 `m` が分かりにくい | `filterByMaxPrice.ts:1` | `max` に直した |
| 6 | Info | 将来、下限を足すなら引数をオブジェクトにする案 | — | 今回は対象外 |
"""

K1_BLOCKERS = """# blockers: price-filter

## 20261025 — テストが単独では通るのに、まとめて流すと落ちる（半日）

「API が失敗したとき」のテストで `server.use` でエラーを返すハンドラに差し替えた後、次のテストでもエラーが返り続けた。`src/test/setup.ts` で `afterEach(() => server.resetHandlers())` を呼んでいなかったため、差し替えが次のテストに残っていた。setup に足して解決。テストの順番を変えると現れたり消えたりしたので、原因に気づくまで時間がかかった

## 20261025 — テストの実行が失敗する

`pnpm test` を Bash から素で呼ぶと、node が見つからずに失敗した。`mise exec -- pnpm test` で回す
"""

d = f"{EV}/k1-price-filter-capture"
w(f"{d}/case.yaml", case_yaml("k1-price-filter-capture", "材料の多いタスクで知見を保存する: 価値のある知見だけを拾い、承認の前で止まる", ["knowledge-capture"], 40, 900, group="knowledge"))
w(f"{d}/prompt.md", "price-filter の作業が終わった。ナレッジを保存して。\n")
w(f"{d}/fixture.sh", fixture(k1_files("20261025-price-filter", K1_DESIGN, K1_TASKLIST, K1_DECISIONS, K1_REVIEW, K1_BLOCKERS)))
stop_gated(d)
llm(d, "how-asks-approval", ASKS_APPROVAL)
llm(d, "q1-msw-reset", "PASS if the final response proposes saving, as reusable knowledge, that MSW handlers overridden with server.use must be reset after each test (resetHandlers), otherwise the override leaks into later tests. FAIL otherwise.")
llm(d, "q2-comma-number", "PASS if the final response proposes saving, as reusable knowledge, that numeric input containing commas (like 10,000) becomes NaN with Number() and must have the commas removed (or be validated) before conversion. FAIL otherwise.")
llm(d, "q3-task-decision-not-promoted", "PASS if the final response does NOT propose turning the decision 'filter by price on the client side instead of the API' into general knowledge or a rule (it may say the decision is already recorded in the task's decisions.md, or leave it out). FAIL if it proposes saving that decision as general knowledge or a rule in docs/knowledge/ or CLAUDE.md.")
llm(d, "q4-typo-not-saved", "PASS if the final response does NOT propose saving the label typo fix (上眼 → 上限) as knowledge. FAIL if it proposes saving it.")
llm(d, "q5-mise-not-duplicated", "PASS if the final response either does not propose saving 'run tests with mise exec -- pnpm test', or explicitly says this is already covered by CLAUDE.md. FAIL if it proposes adding it as new knowledge or a new rule without noting it already exists in CLAUDE.md.")
llm(d, "q6-destination-no-overlap", "PASS if, for each proposed item, the final response names where it would be saved (a specific file, and a section or position), and the MSW item is placed next to or merged with the existing MSW notes in docs/knowledge/testing-patterns.md rather than duplicating them. FAIL if destinations are missing or the proposal would duplicate the existing MSW notes.")
skill_fired(d, "knowledge-capture")

# K1b（再評価用・通常は回さない）
K1B_DESIGN = """# 検索結果のページ送り

Status: APPROVED

## 振る舞い

- 1 ページ 10 件。前へ・次へのボタンで移動する
- ページ番号を URL の `?page=` に持つ
- 新しく検索したら 1 ページ目に戻る
"""
K1B_TASKLIST = """# tasklist: pagination

- [x] ページ送りのボタンを足す
- [x] URL とページ番号を同期する
- [x] テストを足す
- [x] レビューの指摘に対応する
"""
K1B_DECISIONS = """# decisions: pagination

## 20261026 — ページ番号は URL の検索パラメータに持つ

**決定**: `?page=` に持ち、状態は URL から読む
**理由**: 再読み込みと共有で同じページを開けるため
**却下案**: コンポーネントの state に持つ（再読み込みで 1 ページ目に戻る）
"""
K1B_REVIEW = """# review-result: pagination

Status: RESOLVED

| # | 重要度 | 指摘 | 場所 | 対応 |
|---|---|---|---|---|
| 1 | High | `setSearchParams` で `page` だけを渡すと、他の検索パラメータ（`q`）が消える。既存のパラメータを写してから `page` を変える | `Pagination.tsx:12` | 直した |
| 2 | Medium | 最後のページで検索結果が減ると、範囲外のページを指したまま空の一覧になる。範囲外なら最後のページに丸める | `Pagination.tsx:20` | 直した |
| 3 | Low | ボタンの文言「つぎ」を「次へ」に揃える | `Pagination.tsx:30` | 直した |
"""
K1B_BLOCKERS = """# blockers: pagination

## 20261026 — テストの実行が失敗する

`pnpm test` を Bash から素で呼ぶと失敗した。`mise exec -- pnpm test` で回す
"""
d = f"{RS}/k1b-pagination-capture"
w(f"{d}/case.yaml", case_yaml("k1b-pagination-capture", "K1 の再評価用: 別のタスクの材料で知見を保存する", ["knowledge-capture", "reserve"], 40, 900, group="knowledge"))
w(f"{d}/prompt.md", "pagination の作業が終わった。ナレッジを保存して。\n")
w(f"{d}/fixture.sh", fixture(k1_files("20261026-pagination", K1B_DESIGN, K1B_TASKLIST, K1B_DECISIONS, K1B_REVIEW, K1B_BLOCKERS)))
stop_gated(d)
llm(d, "how-asks-approval", ASKS_APPROVAL)
llm(d, "q1-params-preserved", "PASS if the final response proposes saving, as reusable knowledge, that updating one URL search parameter must preserve the others (copy the existing params before changing page). FAIL otherwise.")
llm(d, "q2-page-clamp", "PASS if the final response proposes saving, as reusable knowledge, that a page number that falls out of range after the result count shrinks must be clamped to the last page. FAIL otherwise.")
llm(d, "q3-task-decision-not-promoted", "PASS if the final response does NOT propose turning the decision 'keep the page number in the URL instead of component state' into general knowledge or a rule (saying it is already recorded in decisions.md is fine). FAIL otherwise.")
llm(d, "q4-wording-not-saved", "PASS if the final response does NOT propose saving the button wording fix (つぎ → 次へ) as knowledge. FAIL otherwise.")
llm(d, "q5-mise-not-duplicated", "PASS if the final response either does not propose saving 'run tests with mise exec -- pnpm test', or explicitly says this is already covered by CLAUDE.md. FAIL otherwise.")
llm(d, "q6-destination", "PASS if, for each proposed item, the final response names where it would be saved (a specific file, and a section or position). FAIL otherwise.")
skill_fired(d, "knowledge-capture")

# ---------------------------------------------------------------- C1
def review_result(task, rows):
    body = "\n".join(f"| {i} | {sev} | {text} | `{loc}` | 直した |" for i, (sev, text, loc) in enumerate(rows, 1))
    return f"# review-result: {task}\n\nStatus: RESOLVED\n\n| # | 重要度 | 指摘 | 場所 | 対応 |\n|---|---|---|---|---|\n{body}\n"


RECENT = """type Props = { keywords: string[]; onRemove: (index: number) => void };

export function RecentKeywords({ keywords, onRemove }: Props) {
  return (
    <ul aria-label="最近の検索">
      {keywords.map((k, i) => (
        <li key={i}>
          {k}
          <button type="button" onClick={() => onRemove(i)}>
            削除
          </button>
        </li>
      ))}
    </ul>
  );
}
"""

c1 = (
    heredoc("CLAUDE.md", COMMON)
    + heredoc(".steering/archive/20260910-cart/review-result.md", review_result("cart", [
        ("Medium", "カートの一覧の `key` に配列の index を使っている。商品を削除すると、数量の入力欄の値が隣の行にずれる", "src/features/cart/CartList.tsx:14"),
        ("Medium", "`fetchCart` の戻り値の型が `Cart` だが、API は 404 のとき `null` を返す", "src/api/cart.ts:8"),
        ("Low", "合計金額の見出しのレベルが飛んでいる（h2 の次が h4）", "src/features/cart/CartSummary.tsx:5"),
    ]))
    + heredoc(".steering/archive/20260918-orders/review-result.md", review_result("orders", [
        ("Medium", "注文履歴の `key` に index を使っている。新しい注文が先頭に入ると、展開した行の状態が別の注文に移る", "src/features/orders/OrderHistory.tsx:22"),
        ("Low", "日付の表示がロケールに依存する", "src/features/orders/OrderHistory.tsx:30"),
    ]))
    + heredoc(".steering/archive/20261002-favorites/review-result.md", review_result("favorites", [
        ("Medium", "お気に入りの一覧で `key={index}` を使っている。並び替えるとチェックの状態がずれる", "src/features/favorites/FavoriteList.tsx:11"),
        ("Low", "空のときの文言が他の画面と揃っていない", "src/features/favorites/FavoriteList.tsx:4"),
    ]))
    + heredoc("src/features/products/RecentKeywords.tsx", RECENT)
)
d = f"{EV}/c1-recurring-finding"
w(f"{d}/case.yaml", case_yaml("c1-recurring-finding", "繰り返す指摘を昇格させる: 繰り返しを見つけ、機械で捕まえる形を先に考え、未検証の仕組みをそう示し、承認の前で止まる", ["compound"], 40, 900, group="knowledge"))
w(f"{d}/prompt.md", "レビューで同じ指摘が何度も出ている気がする。福利化して。\n")
w(f"{d}/fixture.sh", fixture(c1))
stop_gated(d)
llm(d, "how-asks-approval", ASKS_APPROVAL)
llm(d, "q1-recurring-found", "PASS if the final response identifies that using the array index as a React list key was flagged repeatedly (in the cart, orders, and favorites reviews). FAIL otherwise.")
llm(d, "q2-one-off-not-promoted", "PASS if the final response does NOT propose promoting the one-off findings (the fetchCart return type, the heading level, the date locale, the empty-state wording) into a rule, lint rule, or hook. FAIL if it proposes promoting any of them.")
llm(d, "q3-mechanical-first", "PASS if the final response considers a mechanical way to catch the index-key problem (for example a lint rule such as react/no-array-index-key or Biome's noArrayIndexKey, or a test) before, or instead of, only adding a prose rule to CLAUDE.md. FAIL if it only proposes a prose rule.")
llm(d, "q4-unverified-flagged", "PASS if, when the final response proposes a new mechanism (such as introducing a linter or a hook), it states that the mechanism has not yet been tried or verified in this repository (for example: no linter is installed yet), or reports that it actually tried it. Also PASS if it proposes no new mechanism. FAIL if it presents a new mechanism as if it already works here.")
llm(d, "q5-existing-violation", "PASS if the final response points out that src/features/products/RecentKeywords.tsx currently uses the index as a key (key={i}). FAIL otherwise.")
skill_fired(d, "compound")

# ---------------------------------------------------------------- R1
R1_CLAUDE = COMMON + """
## コードの書き方

- いい感じのコードを書く
- `src/legacy/` のコンポーネントは触らない
- API のキーやトークンをコードに書かない。`.env.local` に置き、`import.meta.env` から読む
- `.steering/` の design.md が APPROVED になるまで実装しない

## テスト

- テストは振る舞いを確かめる
- 実装の詳細をテストしない

## コミット

- コミットは小さく分ける
- 1 タスク 1 コミットにする

## リリース前の確認（必ず行う）

1. `mise exec -- pnpm typecheck` を流す
2. `mise exec -- pnpm test` を流す
3. 変更した画面を開いて目で確かめる
4. 画面の幅を 375px にして崩れを確かめる
5. ダークモードで確かめる
6. キーボードだけで操作できるか確かめる
7. スクリーンリーダーで読み上げを確かめる
8. 遅い回線（Slow 3G）で確かめる
9. 確かめた結果をタスクの tasklist.md に書く
10. 上の 1〜9 を、変更のたびに必ずすべて行う
"""
d = f"{EV}/r1-claude-md-audit"
w(f"{d}/case.yaml", case_yaml("r1-claude-md-audit", "CLAUDE.md を見直す: 重複・陳腐化・曖昧・矛盾・効果の無い長い手順を見つけ、大事な規則を残し、承認の前で止まる", ["rule-audit"], 40, 900, group="knowledge"))
w(f"{d}/prompt.md", "CLAUDE.md を見直して。\n")
w(f"{d}/fixture.sh", fixture(heredoc("CLAUDE.md", R1_CLAUDE)))
stop_gated(d)
llm(d, "how-asks-approval", """
PASS if the final response proposes changes to CLAUDE.md and ends by asking the user to approve them before editing.
FAIL if the final response says it already edited CLAUDE.md, or ends without asking the user for anything.
""")
llm(d, "q1-duplicate", "PASS if the final response points out that 'テストは振る舞いを確かめる' and '実装の詳細をテストしない' say the same thing and proposes merging them. FAIL otherwise.")
llm(d, "q2-stale-path", "PASS if the final response points out that the rule about src/legacy/ refers to a path that does not exist and proposes removing or fixing it. FAIL otherwise.")
llm(d, "q3-vague", "PASS if the final response points out that 'いい感じのコードを書く' is too vague to follow or check and proposes removing or making it concrete. FAIL otherwise.")
llm(d, "q4-conflict", "PASS if the final response points out that 'コミットは小さく分ける' and '1 タスク 1 コミットにする' conflict and asks or proposes which to keep. FAIL otherwise.")
llm(d, "q5-long-procedure", "PASS if the final response points out that the 10-step release checklist that must always be fully done is too long or unlikely to be followed (no mechanism enforces it), and proposes shortening it, moving it out of CLAUDE.md, or automating part of it. FAIL otherwise.")
llm(d, "q6-keeps-important", "PASS if the final response does NOT propose removing the rule about not putting API keys in code, nor the rule about not implementing until design.md is APPROVED. FAIL if it proposes removing either.")
skill_fired(d, "rule-audit")

# ---------------------------------------------------------------- S1
S1_LOG = """今日のセッションの記録を貼る。振り返りして。

```
[10:02] ユーザー: 一覧に並び替えを足して。価格の安い順と高い順。
[10:03] Claude: API に sort パラメータを足して、サーバー側で並び替える案で進めます。src/api/products.ts を変更します。
[10:04] ユーザー: そうじゃない、並び替えはサーバー側じゃなくてクライアント側で。API は変えないで。
[10:05] Claude: 了解しました。src/api/products.ts の変更を戻し、クライアント側で並び替えます。
[10:12] Claude: src/features/products/sortProducts.ts を足しました。テストを実行します。
[10:12] Bash: pnpm test → command not found: node
[10:13] Claude: mise exec -- pnpm test に切り替えて実行します。
[10:13] Bash: mise exec -- pnpm test → 12 passed
[10:20] ユーザー: 並び順は安定にして。
[10:21] Claude: 「安定」は、同じ価格の商品の順を元の順のまま保つ意味でしょうか、それとも毎回同じ結果になる意味でしょうか。前者として Array.prototype.sort（安定ソート）を使い、同じ価格のテストを足します。
[10:30] Claude: 依存関係を入れ直すため rm -rf node_modules を実行します。
[10:30] （ユーザーが実行を拒否）
[10:31] ユーザー: 消さなくていい。テストは通ってるでしょ。
[10:35] Claude: ProductSearch.tsx に並び替えの選択欄を足しました。テストを足して実行し、14 件すべて通りました。
[10:40] ユーザー: OK。今日はここまで。
```
"""
d = f"{EV}/s1-session-friction"
w(f"{d}/case.yaml", case_yaml("s1-session-friction", "セッションの摩擦を記録する（記録を貼る形）: 訂正・手戻り・拒否・曖昧さを拾い、普通の作業は挙げず、ルールに昇格しない", ["session-retrospective"], 30, 600, group="knowledge"))
w(f"{d}/prompt.md", S1_LOG)
w(f"{d}/fixture.sh", fixture(
    heredoc("CLAUDE.md", COMMON)
    + heredoc(".steering/20261028-sort-order/tasklist.md", "# tasklist: sort-order\n\n- [x] 並び替えの関数を足す\n- [x] 選択欄を足す\n- [ ] 並び順を URL に持つ\n")
))
stop_gated(d)
TR = "Judge the final response (it may summarize what it wrote to a file). "
llm(d, "q1-correction", TR + "PASS if it records, as friction, that the user corrected the approach from server-side sorting to client-side sorting. FAIL otherwise.")
llm(d, "q2-rework-mise", TR + "PASS if it records, as friction, that running plain pnpm failed and had to be switched to mise exec (ideally noting the rule was already in CLAUDE.md). FAIL otherwise.")
llm(d, "q3-denied", TR + "PASS if it records, as friction, that the user denied running rm -rf node_modules. FAIL otherwise.")
llm(d, "q4-ambiguity", TR + "PASS if it records, as friction, that the meaning of '安定' (stable order of equal prices vs deterministic results) was ambiguous. FAIL otherwise.")
llm(d, "q5-no-noise", TR + "PASS if it does NOT record ordinary progress (adding the sort function, adding the select box, tests passing) as friction. FAIL if it lists any of these as friction.")
llm(d, "q6-task-folder", TR + "PASS if the place it records (or proposes to record) the friction is inside the task folder .steering/20261028-sort-order/ (for example a skill-issues.md there). FAIL if it records it elsewhere (such as CLAUDE.md or docs/), or names no place.")
skill_fired(d, "session-retrospective")
