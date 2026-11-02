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
mkdir -p "$(dirname '.steering/archive/20260910-cart/review-result.md')"
cat > '.steering/archive/20260910-cart/review-result.md' <<'EOF_FIXTURE'
# review-result: cart

Status: RESOLVED

| # | 重要度 | 指摘 | 場所 | 対応 |
|---|---|---|---|---|
| 1 | Medium | カートの一覧の `key` に配列の index を使っている。商品を削除すると、数量の入力欄の値が隣の行にずれる | `src/features/cart/CartList.tsx:14` | 直した |
| 2 | Medium | `fetchCart` の戻り値の型が `Cart` だが、API は 404 のとき `null` を返す | `src/api/cart.ts:8` | 直した |
| 3 | Low | 合計金額の見出しのレベルが飛んでいる（h2 の次が h4） | `src/features/cart/CartSummary.tsx:5` | 直した |
EOF_FIXTURE
mkdir -p "$(dirname '.steering/archive/20260918-orders/review-result.md')"
cat > '.steering/archive/20260918-orders/review-result.md' <<'EOF_FIXTURE'
# review-result: orders

Status: RESOLVED

| # | 重要度 | 指摘 | 場所 | 対応 |
|---|---|---|---|---|
| 1 | Medium | 注文履歴の `key` に index を使っている。新しい注文が先頭に入ると、展開した行の状態が別の注文に移る | `src/features/orders/OrderHistory.tsx:22` | 直した |
| 2 | Low | 日付の表示がロケールに依存する | `src/features/orders/OrderHistory.tsx:30` | 直した |
EOF_FIXTURE
mkdir -p "$(dirname '.steering/archive/20261002-favorites/review-result.md')"
cat > '.steering/archive/20261002-favorites/review-result.md' <<'EOF_FIXTURE'
# review-result: favorites

Status: RESOLVED

| # | 重要度 | 指摘 | 場所 | 対応 |
|---|---|---|---|---|
| 1 | Medium | お気に入りの一覧で `key={index}` を使っている。並び替えるとチェックの状態がずれる | `src/features/favorites/FavoriteList.tsx:11` | 直した |
| 2 | Low | 空のときの文言が他の画面と揃っていない | `src/features/favorites/FavoriteList.tsx:4` | 直した |
EOF_FIXTURE
mkdir -p "$(dirname 'src/features/products/RecentKeywords.tsx')"
cat > 'src/features/products/RecentKeywords.tsx' <<'EOF_FIXTURE'
type Props = { keywords: string[]; onRemove: (index: number) => void };

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
EOF_FIXTURE
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture" --allow-empty
