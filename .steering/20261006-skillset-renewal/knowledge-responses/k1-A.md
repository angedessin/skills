<!-- results-knowledge-b-1.json / k1-price-filter-capture / without / 0.26 USD / 72s -->

`.steering/20261025-price-filter/` の 5 ファイルと既存の `docs/knowledge/` を読みました。CLAUDE.md で `docs/` への書き込みは承認が必要なので、案だけ示します。

## 残す内容（案）

**1. `docs/knowledge/testing-patterns.md` に追記**（blockers.md の半日かかった件）

```markdown
## ハンドラの差し替えは各テストの後に戻す

- `server.use` で差し替えたハンドラは、`server.resetHandlers()` を呼ばないと次のテストにも残る
- 症状: テストを 1 つだけ流すと通るのに、まとめて流すと落ちる。並び順を変えると落ちたり通ったりする
- `src/test/setup.ts` の `afterEach` で `server.resetHandlers()` を呼んでいる。消さないこと
```

**2. `docs/knowledge/form-patterns.md` を新しく作る**（decisions.md とレビュー指摘 #1 から）

```markdown
# フォームのパターン

## 数値の入力欄

- `type="number"` ではなく `type="text"` に `inputMode="numeric"` を付ける。`type="number"` だと、ブラウザによっては「10,000」のようにカンマの入った値が空になる
- 数値にするときは、カンマを除いてから `Number` に渡す。そのまま渡すと NaN になり、`price <= NaN` がすべて false になって全件が消える
- NaN になったときは絞り込まない
- 空欄と 0 は別の値として扱う（`Number("")` は 0 になる）

## 絞り込みのロジック

- 絞り込みや変換は、画面から切り離した純粋な関数にする（例: `filterByMaxPrice(products, max)`）。そうすれば単体でテストできる
```

**3. `docs/knowledge/api-patterns.md` に追記**

```markdown
- 商品検索 API には価格の引数がなく、結果は最大 50 件。価格などで絞り込むときはクライアント側で行う（API は別の担当が持っている）
```

## 残さないもの

- `mise exec -- pnpm test`：CLAUDE.md に既に書いてあるため
- ラベルの抜け・typo・引数名・0 件表示のテスト：この作業の中で直して終わったもの
- 下限の引数をオブジェクトにする案：今回の範囲外で、まだ決まっていないため

## 確認してほしいこと

tasklist.md は全部完了になっていますが、`src/` に `filterByMaxPrice.ts` も上限の入力欄も見つかりません。`ProductSearch.tsx` はキーワード検索だけのままで、git のコミットもありません。実装がまだコミットされていないか、別のブランチにある可能性があります。

この案で書き込んでよいですか？足したり外したりしたいものがあれば教えてください。
