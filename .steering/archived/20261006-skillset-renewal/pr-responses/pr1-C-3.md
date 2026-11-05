<!-- results-pr-c-1.json / pr1-feature-branch / with / run 3 / 0.18 USD / 44s -->

コミットまで済ませました。push と PR 作成はまだしていません。下の内容でよければ承認をお願いします。

**準備の結果**
- 未コミットだった 2 ファイル（`filterByCategory.ts` とそのテスト）は、どちらもこの作業のものだったので、その 2 つだけをコミットしました（`6be52cd`）。
- **テストは流せていません。** `mise exec -- pnpm vitest run` を実行したところ、node と pnpm がまだインストールされておらず、ダウンロード先（nodejs.org など）への通信がサンドボックスで拒否されました。
- 普段の `git`（`/usr/bin/git`）はサンドボックス内で動かなかったため、`/usr/local/bin/git` を使いました。

**PR の内容（案）**
- ベース: `main` ← ヘッド: `feature/category-filter`
- タイトル: `feat: 商品をカテゴリで絞り込む filterByCategory を追加`
- 本文:

```markdown
## 何を・なぜ
商品一覧をカテゴリで絞り込むための純粋関数 `filterByCategory` を追加します。

## 主な変更
- `src/features/products/filterByCategory.ts`: `Product[]` とカテゴリ名を受け取り、カテゴリが一致する商品だけを返す。カテゴリが空文字なら全件をそのまま返す
- `src/features/products/filterByCategory.test.ts`: 空カテゴリで全件が返ること、一致したカテゴリだけが返ることをテスト

## 確かめたこと
- テストはまだ流していません（作業環境で node/pnpm を入れられなかったため）。レビューの前に CI かローカルで `pnpm vitest run src/features/products/filterByCategory.test.ts` を確認してください

## 残っていること・見てほしい点
- 関数を追加しただけで、画面（検索 UI）からはまだ使っていません
- カテゴリの比較は完全一致で、大文字小文字や前後の空白はそろえていません

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

承認をもらったら、`origin` に push して `gh pr create` で PR を作り、URL をお伝えします。
