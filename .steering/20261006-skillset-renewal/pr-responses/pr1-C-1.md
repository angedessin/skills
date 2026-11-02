<!-- results-pr-c-1.json / pr1-feature-branch / with / run 1 / 0.18 USD / 56s -->

コミットまで済ませました。push と PR の作成は、下の内容で承認をもらってから行います。

**コミット**
- `721a494 feat: 商品をカテゴリで絞り込む filterByCategory を追加`
- 対象は新規の 2 ファイルだけです（`filterByCategory.ts` と `filterByCategory.test.ts`）

**PR の案**
- ベース: `main`
- ヘッド: `feature/category-filter`（`origin` に push します）
- タイトル: `feat: 商品をカテゴリで絞り込む filterByCategory を追加`

本文:

```markdown
## 何を・なぜ
商品一覧をカテゴリで絞り込むための純粋関数 `filterByCategory` を追加しました。

## 主な変更
- `src/features/products/filterByCategory.ts`
  - `filterByCategory(products, category)`: `category` が空文字なら全件を、それ以外なら `category` が一致する商品だけを返します
- `src/features/products/filterByCategory.test.ts`
  - 空のカテゴリなら全件を返すこと
  - 一致するカテゴリの商品だけを返すこと

## 確かめたこと
- テストは流せていません。作成した環境のネットワーク制限で、mise による node / pnpm のインストールが失敗したためです。レビュー前に `pnpm vitest run` で確認をお願いします

## 残っていること・見てほしい点
- UI への組み込み（カテゴリ選択のコンポーネントなど）は入っていません。関数の追加だけです
- カテゴリは完全一致で比べています。大文字・小文字や前後の空白は区別されます

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

注意点が 2 つあります。

- **テストを流せていません。** 先に手元で `pnpm vitest run` を流してから PR を作るほうが安全です。
- この環境では素の `git` が動きませんでした（xcrun がサンドボックスに止められるため）。代わりに `/usr/local/bin/git` を使っています。

この内容で push して PR を作ってよいですか？
