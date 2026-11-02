#!/bin/bash
set -euo pipefail
cp -cR /Users/kentaro/Desktop/_lab/ai/skills-eval-app/. .
mkdir -p "$(dirname 'CLAUDE.md')"
cat > 'CLAUDE.md' <<'EOF_FIXTURE'
# skills-eval-app

Tech stack: React / TypeScript / Vitest / React Testing Library / MSW

## 作業の進め方

- 複数セッションにまたがる作業は、実装の前に `.steering/[YYYYMMDD]-[task]/` に design.md（冒頭に `Status: DRAFT`）と tasklist.md を作り、人間のレビューを求めて止まる。Status が APPROVED になるまで実装しない
- 1 セッションで終わるが決めることがある作業は、会話の中で設計を示し、OK をもらってから実装する
- 小さな作業（typo・数行の修正・調査だけ）は、この手順に乗せずにそのまま進める。どれに当たるか迷うときだけ聞く
- 作業を再開するときは、`.steering/` の tasklist.md を読んでから始める。作業を終えたら tasklist.md を更新する

## 自律実行の境界

- CLAUDE.md・docs/・.claude/ への書き込みは、承認を得てから Edit / Write ツールで行う
- 判断基準: (1) git で巻き戻せる (2) 失敗に気づける (3) 影響がタスク内に閉じる — 3 つ全て満たす操作のみ承認なしで実行してよい

## 環境

- mise 管理下では Bash から素の pnpm / node を呼ばず、`mise exec --` を使う
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261025-price-filter/design.md')"
cat > '.steering/20261025-price-filter/design.md' <<'EOF_FIXTURE'
# 価格の上限で絞り込む

Status: APPROVED

## 目的

検索結果を、入力した価格の上限以下に絞り込めるようにする。

## 振る舞い

- 「上限」の入力欄に数値を入れると、その価格以下の商品だけを表示する
- 空欄なら絞り込まない
- 絞り込んだ結果が 0 件なら「該当する商品はありません」

## 対象外

- 下限・並び替え
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261025-price-filter/tasklist.md')"
cat > '.steering/20261025-price-filter/tasklist.md' <<'EOF_FIXTURE'
# tasklist: price-filter

- [x] 上限の入力欄を足す
- [x] 絞り込みの関数を足す（`src/features/products/filterByMaxPrice.ts`）
- [x] テストを足す
- [x] レビューの指摘に対応する
- [x] 作業を終える
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261025-price-filter/decisions.md')"
cat > '.steering/20261025-price-filter/decisions.md' <<'EOF_FIXTURE'
# decisions: price-filter

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
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261025-price-filter/review-result.md')"
cat > '.steering/20261025-price-filter/review-result.md' <<'EOF_FIXTURE'
# review-result: price-filter

Status: RESOLVED

| # | 重要度 | 指摘 | 場所 | 対応 |
|---|---|---|---|---|
| 1 | High | 「10,000」のようなカンマ入りの上限を `Number` に渡すと NaN になり、`price <= NaN` がすべて false で全件が消える。カンマを除いてから数値にする | `filterByMaxPrice.ts:3` | 直した（`replace(/,/g, "")` の後に `Number`。NaN なら絞り込まない） |
| 2 | Medium | 上限の入力欄にラベルが無い | `ProductSearch.tsx:31` | 直した |
| 3 | Low | ラベルの typo「上眼」→「上限」 | `ProductSearch.tsx:31` | 直した |
| 4 | Low | 0 件のときの表示のテストが無い | `ProductSearch.test.tsx` | 足した |
| 5 | Low | `filterByMaxPrice` の引数名 `m` が分かりにくい | `filterByMaxPrice.ts:1` | `max` に直した |
| 6 | Info | 将来、下限を足すなら引数をオブジェクトにする案 | — | 今回は対象外 |
EOF_FIXTURE
mkdir -p "$(dirname '.steering/20261025-price-filter/blockers.md')"
cat > '.steering/20261025-price-filter/blockers.md' <<'EOF_FIXTURE'
# blockers: price-filter

## 20261025 — テストが単独では通るのに、まとめて流すと落ちる（半日）

「API が失敗したとき」のテストで `server.use` でエラーを返すハンドラに差し替えた後、次のテストでもエラーが返り続けた。`src/test/setup.ts` で `afterEach(() => server.resetHandlers())` を呼んでいなかったため、差し替えが次のテストに残っていた。setup に足して解決。テストの順番を変えると現れたり消えたりしたので、原因に気づくまで時間がかかった

## 20261025 — テストの実行が失敗する

`pnpm test` を Bash から素で呼ぶと、node が見つからずに失敗した。`mise exec -- pnpm test` で回す
EOF_FIXTURE
mkdir -p "$(dirname 'docs/knowledge/testing-patterns.md')"
cat > 'docs/knowledge/testing-patterns.md' <<'EOF_FIXTURE'
# テストのパターン

## モックの境界

- API はネットワークの手前（MSW）でモックする。`src/api/` の関数を `vi.mock` で差し替えない（呼び出しの確認だけになり、振る舞いを見なくなる）
- ハンドラは `src/mocks/handlers.ts` に置き、テストごとの差し替えは `server.use` で行う

## 要素の探し方

- 役割とアクセシブルな名前 → ラベル → 表示文字列の順で探す
EOF_FIXTURE
mkdir -p "$(dirname 'docs/knowledge/api-patterns.md')"
cat > 'docs/knowledge/api-patterns.md' <<'EOF_FIXTURE'
# API 呼び出しのパターン

- API の関数は `src/api/` に置き、画面からは直接 `fetch` を呼ばない
- 失敗は例外で返し、画面側で `status: "error"` にする
EOF_FIXTURE
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
