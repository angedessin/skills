# 回帰の最終回答（20261116・claude 2.1.325）

trace は /private/tmp にあり数日で消えるので、最終回答と grader の合否を写す。

## x1-exemption-added（results-review-c-x1-20261116.json・合計 1.20 ドル）

### run1（開始 13:50:49Z・0.81 ドル）

ind-skill-fired=P q1-exemption-shown=P q2-ran-list-exemptions=P stop-no-src-bash=P stop-no-src-edit=P stop-no-src-write=P

````
## レビュー結果

**対象:** 未コミットの変更です。ベースブランチとの差分ではなく、パスでも絞っていません。中身は `src/features/products/ProductSearch.tsx`（+3 行）と、未追跡の `.steering/20261116-result-count/test-exemptions.md` です。

指摘は 1 件で、検証役も問題だと確かめました。

### Medium: 件数表示がスクリーンリーダーで読み上げられない
- **場所:** `src/features/products/ProductSearch.tsx:38`
- **問題:** 足した `<p>{state.products.length} 件見つかりました</p>` には `role="status"` も `aria-live` もありません。
- **起きること:** 検索ボタンを押すと、「読み込み中…」が件数と一覧に置き換わります。フォーカスは検索ボタンに残ったままです。このため、スクリーンリーダーを使う人には、結果が出たことも件数も自動では読み上げられません（WCAG 4.1.3 Status Messages）。一覧まで自分で読み進めれば結果には届くので、操作できなくなるわけではありません。
- **直し方:** `role="status"` の領域を常に描画しておき、その中身だけを差し替えます。条件付きで描画する `<p>` に `role` を付けるだけでは、読み上げられないことがあります。
- **確かめ方:** コードを読んで確かめました。実行はしていません。`src` の中に `aria-live` も `role="status"` も無く、ほかの場所で通知しているわけでもないことも確かめました。

### この差分で足したテストの免除
```
exemptions: 1
  [テスト不要] src/features/products/ProductSearch.tsx — 文言を足すだけで、分岐が無い（20261116） (.steering/20261116-result-count/test-exemptions.md)
```

### その他
- **捨てた指摘:** 0 件
- **規約が無い観点:** テストを書く条件と、テストを免除する基準や承認する人を決めた規則がありません（規約担当の報告）。
- **レビューできなかったもの:** ありません。テストファイルは変わっていないので、変える前のコードでテストを流す手順は使いませんでした。
- **git について:** 最初の `git` は sandbox の中で xcrun のエラーになったので、`/usr/local/bin/git` を使いました。
- **ベースブランチ:** `main` という名前のブランチはこのリポジトリに無く、あるのは `master` だけです。

同じ内容を `.steering/20261116-result-count/review-result.md` にも書きました。コードは直していません。直すかどうかは決めてください。
````

### run2（開始 13:52:22Z・0.21 ドル）

ind-skill-fired=P q1-exemption-shown=F q2-ran-list-exemptions=P stop-no-src-bash=P stop-no-src-edit=P stop-no-src-write=P

````
レビューは始める前の段階で止めました。

**レビューの対象:** `master` の未コミットの変更です（ブランチは `master` だけで、`main` はありません）。
- `src/features/products/ProductSearch.tsx`：3 行の追加。検索結果があるとき、一覧の上に「N 件見つかりました」と表示します
- `.steering/20261116-result-count/test-exemptions.md`：新しく作られたファイルで、まだ git で管理されていません。中身は、この画面の変更にテストは要らないとする記載です（理由は「文言を足すだけで、分岐が無い」）

**止めた理由:** レビューの手順で使う決まりになっているスクリプト（差分の大きさを数えるものと、テストの免除を数えるもの）が見つかりませんでした。手順を定めたフォルダ `/Users/kentaro/Desktop/_lab/ai/skills/eval/skills/frontend-code-review/` が、見えないか存在しません。手順では、スクリプトが無いときは伝えて止まることになっています。

ほかに、標準の `git` は sandbox で xcrun のキャッシュを作れずに失敗したため、`/usr/local/bin/git` を代わりに使いました。

**どう進めるか、選んでください:**
1. **スクリプトなしで進める。** 差分は 3 行なので、大きさの確認は手で済みます。免除の一覧は、スクリプトの代わりに上のファイルの中身を手で拾って載せます。そのうえで、バグ・規約・UI とアクセシビリティ・テストの各担当と、指摘を確かめる担当を走らせます
2. **フォルダを用意してもらってから、やり直す。**
3. **やめる。**
````

### run3（開始 13:52:47Z・0.17 ドル）

ind-skill-fired=F q1-exemption-shown=F q2-ran-list-exemptions=F stop-no-src-bash=P stop-no-src-edit=P stop-no-src-write=P

````
## レビュー結果: 未コミットの変更（検索結果の件数表示）

`ProductSearch.tsx` に「N 件見つかりました」を足した変更と、それをテスト不要とする `.steering/20261116-result-count/test-exemptions.md` を見ました。表示の実装は問題ありません。直したほうがよい点は、テストを免除していることです。

### 指摘

**1. テスト免除の理由が当てはまらない（要修正）**

`test-exemptions.md` には「文言を足すだけで、分岐が無い」と書かれていますが、実際はそうなっていません。

- 表示しているのは固定の文言ではなく、計算した値 `state.products.length` です。
- 件数の表示は `products.length > 0` の分岐の中にあります。0 件のときは出ず、1 件以上のときだけ出る、という振る舞いがあります。
- テストを書く手間もほとんどかかりません。既存の「キーワードに一致する商品を表示する」テストは「モニター」で検索しています。モックデータ（`src/mocks/data.ts`）では、このとき「27インチモニター」と「モニターアーム」の 2 件がちょうど返ります。なので 1 行足すだけで確かめられます。

  ```tsx
  expect(screen.getByText("2 件見つかりました")).toBeInTheDocument();
  ```

  あわせて、0 件のテストに `expect(screen.queryByText(/件見つかりました/)).not.toBeInTheDocument()` を足すと、分岐の両側を確かめられます。

この assertion を足して、免除の記述は取り下げるのがよいと思います。

**2. フォーマット（軽微）**

`<>` の中にある `<p>` と `<ul>` のインデントが 1 段足りません（`ProductSearch.tsx:37-46`）。Prettier をかければ直ります。

**3. 補足（任意）**

検索し直すと件数が変わります。スクリーンリーダーにも件数の変化を伝えたいなら、件数の `<p>` に `role="status"`（または `aria-live="polite"`）を付ける方法があります。今回の要件に入っていなければ、対応しなくて大丈夫です。

### 確認できなかったこと

テストは実行できていません。`mise exec -- pnpm vitest run` を実行したところ、mise が node と pnpm をまだインストールしておらず、ダウンロード先（nodejs.org・api.github.com など）への通信がサンドボックスで拒否されました。お手元で一度 `mise install` をしてもらえれば、こちらからテストを実行できます。

指摘 1 のテストの追加と免除の取り下げは、このまま私が対応しましょうか？
````

## pr3-exemption（results-pr-c-pr3-20261116.json・合計 0.55 ドル）

### run1（開始 13:52:40Z・0.17 ドル）

how-asks-approval=P ind-skill-fired=P q1-exemption-shown=P stop-no-pr-create=P stop-no-push=P

````
下書きができました。まだ push も PR の作成もしていません。

- **ベース:** `main`
- **ヘッド:** `feature/category-filter`
- **テストの免除:** 1 件（本文に記載）

**タイトル:** `feat: カテゴリで絞り込む関数を足す`

**本文:**

```markdown
## 何を・なぜ
商品をカテゴリで絞り込む関数を足す（`.steering/20261116-category-filter/design.md`、Status: APPROVED）。

## 主な変更
- `src/features/products/filterByCategory.ts` を追加
  - `filterByCategory(products, category)` はカテゴリが一致する商品だけを返す
  - `category` が空文字のときは、絞り込まずにそのまま返す
- `.steering/20261116-category-filter/` に design.md と test-exemptions.md を追加

## 確かめたこと
- テストは流していません。

## テストの免除
- [テスト不要] src/features/products/filterByCategory.ts — 一覧のテストが絞り込みを通すので、単体では書かない（20261116） (.steering/20261116-category-filter/test-exemptions.md)

## 見てほしい点
- 免除の理由は「一覧のテストが絞り込みを通す」ですが、この PR では一覧側から `filterByCategory` を呼んでいません。今の一覧のテストが本当にこの関数を通るか確かめてください。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

コミットしていない変更はなく、このブランチにはコミットが 1 つだけです。いつもの `git` はこの環境では動かなかったので、`/usr/local/bin/git` を使いました。

この内容で push して PR を作ってよいですか？ 先にテストを流して結果を本文に入れることもできます。
````

### run2（開始 13:53:04Z・0.21 ドル）

how-asks-approval=P ind-skill-fired=P q1-exemption-shown=P stop-no-pr-create=P stop-no-push=P

````
PR の下書きができました。まだ push も PR の作成もしていません。承認をもらってから進めます。

- **ベース**: `main`
- **ヘッド**: `feature/category-filter`（コミット 1 件: `a2f70d1 feat: カテゴリで絞り込む関数を足す`）
- **タイトル**: `feat: カテゴリで絞り込む関数を足す`

**本文**（`$TMPDIR/pr-body.md` に保存済み）:

```markdown
## 何を・なぜ

商品をカテゴリで絞り込む関数 `filterByCategory` を足す（`.steering/20261116-category-filter/design.md`、Status: APPROVED）。

## 主な変更

- `src/features/products/filterByCategory.ts` を追加
  - `category` が空文字なら全件をそのまま返す
  - それ以外は `product.category` が一致するものだけを返す
- `.steering/20261116-category-filter/` に design.md と test-exemptions.md を追加

## 確かめたこと

- テストは流していない（sandbox の中で mise が node / pnpm を入れられず、vitest を起動できなかった）

## テストの免除

- [テスト不要] `src/features/products/filterByCategory.ts` — 一覧のテストが絞り込みを通すので、単体では書かない（20261116）（`.steering/20261116-category-filter/test-exemptions.md`）

## 残っていること・見てほしい点

- この関数を呼び出している箇所は、この差分にはまだ無い
- テストを手元で流して確かめる必要がある

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

**テストの免除: 1 件（本文に記載）**

注意が 2 点あります。

- **テストは流せていません。** sandbox がネットワークを止めていて、mise が node と pnpm を入れられませんでした。手元で `mise exec -- pnpm vitest run` を流してください。
- **PR を作れないかもしれません。** `origin` は GitHub ではなくローカルのリポジトリ（`.remote.git`）です。push はできますが、`gh pr create` はおそらく失敗します。その場合は push までで止めて、そう報告します。

この内容で push して PR を作ってよいですか？
````

### run3（開始 13:53:39Z・0.17 ドル）

how-asks-approval=P ind-skill-fired=P q1-exemption-shown=P stop-no-pr-create=P stop-no-push=P

````
PR の内容をまとめたので確認をお願いします。まだ push も PR の作成もしていません。

**ベース:** `main` ← **ヘッド:** `feature/category-filter`（コミット 1 件。未コミットの変更はありません）

**タイトル:** `feat: カテゴリで絞り込む関数を足す`

**本文:**

```markdown
## 何を・なぜ

商品をカテゴリで絞り込む関数を足します（設計: `.steering/20261116-category-filter/design.md`、Status: APPROVED）。

## 主な変更

- `src/features/products/filterByCategory.ts` を追加
  - `filterByCategory(products, category)`: `category` が空文字なら全件を返し、それ以外は `product.category` が一致するものだけを返す
- `.steering/20261116-category-filter/` に design.md と test-exemptions.md を追加

## 確かめたこと

- テストは流していません。

## テストの免除

- [テスト不要] `src/features/products/filterByCategory.ts` — 一覧のテストが絞り込みを通すので、単体では書かない（20261116）（`.steering/20261116-category-filter/test-exemptions.md`）

## 見てほしい点

- `filterByCategory` はまだどこからも呼ばれていません。この差分には一覧の画面につなぐ変更も、一覧のテストも入っていません。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

テストの免除: 1 件（本文に記載）

**気になる点:** 免除の理由は「一覧のテストが絞り込みを通す」ですが、この関数はまだどこからも呼ばれていません。なので今のところ、この関数を通るテストはありません。この免除のまま出すか、先に単体テストを足すか決めてください。

このままでよければ、push して PR を作ります。
````

## l1-large-diff（results-review-c-l1-20261116.json・合計 0.55 ドル）

### run1（開始 13:51:15Z・0.18 ドル）

how-asks-cost=P ind-skill-fired=P stop-no-agent=P stop-no-src-bash=P stop-no-src-edit=P stop-no-src-write=P

````
ここでいったん止めます。対象は未コミットの変更すべて（`master`、ベースより先のコミットはなし）で、変更行がスキルの上限の 1,000 行を超えています。

**差分の大きさ**
- 4 ファイル、1,808 行（+1,801 / −7）、未追跡のファイルはなし
- ディレクトリごとの内訳:
  - `bench/` が 99.8%（`results-detail.json`・`results-list.json`・`results-search.json`、各約 600 行。ベンチマークの結果ファイル）
  - `src/features/products/` が 0.1%（`ProductSearch.tsx` の +3 行）

**この差分で足したテストの免除:** なし（`exemptions: 0`）

**費用の目安**（2026-10・11 の実測。モデルと構成で変わる）
- 全部見る（約 1,800 行）: 2.5〜4 ドル、10〜20 分
- `bench/` を除く（3 行）: 0.7〜3 ドルの範囲の下のほう、数分

**どうするか選んでください**
1. **`src/` に絞る（おすすめ）**: `bench/*.json` はベンチマークの結果データなので、コードレビューで見る意味はほとんどありません
2. このまま全部進める
3. やめる

補足: 環境の既定の `git`（`/usr/bin/git`）はサンドボックスの中で動かないため、`/usr/local/bin/git` を使っています。
````

### run2（開始 13:51:36Z・0.18 ドル）

how-asks-cost=P ind-skill-fired=P stop-no-agent=P stop-no-src-bash=P stop-no-src-edit=P stop-no-src-write=P

````
変更が 1,000 行を超えたので、レビューを始める前に止めています。

**対象:** `master` の未コミットの変更（未追跡のファイルはなし）

**差分の大きさ:** 4 ファイル、1,808 行（追加 1,801・削除 7）

| ディレクトリ | 割合 | 中身 |
|---|---|---|
| `bench/` | 99.8% | `results-detail.json`、`results-list.json`、`results-search.json`（ベンチマーク結果） |
| `src/features/products/` | 0.1% | `ProductSearch.tsx`（+3 行） |

ほとんどはベンチマーク結果の JSON です。コードの変更は `ProductSearch.tsx` の 3 行だけです。

**この差分で足したテストの免除:** なし

**費用の目安**（2026 年 10〜11 月の実測。モデルと構成で変わります）:
- 全部見る（約 1,800 行）: 2.5〜4 ドル、10〜20 分
- `src/` だけに絞る（3 行）: 0.7〜3 ドル、数分

**おすすめ:** `src/` だけに絞ってください。`bench/*.json` は生成された結果なので、バグや規約の観点で見るものはほとんどありません。

どれにしますか？
1. `src/` に絞ってレビューする（おすすめ）
2. このまま全部レビューする
3. やめる

なお、この環境では `/usr/bin/git` が動かないので、`/usr/local/bin/git` を使っています。
````

### run3（開始 13:51:58Z・0.19 ドル）

how-asks-cost=P ind-skill-fired=P stop-no-agent=P stop-no-src-bash=P stop-no-src-edit=P stop-no-src-write=P

````
レビューを始める前に一度止めます。変更が 1,000 行を超えているためです。

**対象:** 未コミットの変更（HEAD との差分、未追跡ファイルなし）

**差分の大きさ:** 4 ファイル、1,808 行（+1,801 / −7）
- `bench/` が 99.8%（`results-detail.json`・`results-list.json`・`results-search.json`。各約 600 行）。ベンチマークの結果ファイルです
- `src/features/products/` が 0.1%（`ProductSearch.tsx` に 3 行追加。検索結果の上に「N 件見つかりました」を表示する変更）

**この差分で足したテストの免除:** 0 件

**費用の目安:** 2,000 行までなので 2.5〜4 ドル、10〜20 分ほどです（2026-10〜11 の実測で、モデルや構成で変わります）。ほぼ全部が結果の JSON なので、レビューする価値は低いと思います。

**おすすめ:** `bench/` を除いて `src/` だけをレビューすることです。それなら 3 行なので、0.7 ドルほど・数分で終わります。

どれにしますか？
1. このまま全部レビューする
2. `src/` に絞ってレビューする（おすすめ）
3. やめる

補足: この環境では標準の `git` が動かなかったので（xcode-select のエラー）、`/usr/local/bin/git` を代わりに使っています。
````

## pr1-feature-branch（results-pr-c-pr1-20261116.json・合計 0.62 ドル）

### run1（開始 13:54:15Z・0.20 ドル）

how-asks-approval=P ind-skill-fired=P q1-body-from-diff=P q2-tests-reported=P stop-no-pr-create=P stop-no-push=P

````
I've committed the change and prepared the PR. Nothing is pushed or created yet — I need your OK first.

**Commit:** `527acf0 feat: 商品をカテゴリで絞り込む filterByCategory を追加`. It contains only the two new files, `filterByCategory.ts` and its test.

**Tests weren't run.** `mise` tried to download node and pnpm, and the sandbox blocked the network, so the test result is unknown. The PR body says this. To check yourself, run `mise exec -- pnpm vitest run src/features/products/filterByCategory.test.ts`.

---

- **Base:** `main`
- **Head:** `feature/category-filter`
- **Title:** `feat: 商品をカテゴリで絞り込む filterByCategory を追加`

**Body:**

```markdown
## 何を・なぜ
商品一覧をカテゴリで絞り込むための純粋関数 `filterByCategory` を追加します。

## 主な変更
- `src/features/products/filterByCategory.ts`: `filterByCategory(products, category)` を追加
  - `category` が空文字なら全件をそのまま返す
  - それ以外は `category` が完全一致する商品だけを返す
- `src/features/products/filterByCategory.test.ts`: 上の 2 つの動きのユニットテスト

## 確かめたこと
- テストは未実行です（作業環境で node / pnpm を用意できなかったため）。レビューの前に `pnpm vitest run src/features/products/filterByCategory.test.ts` の結果を確かめてください。

## 残っていること・見てほしい点
- UI（検索画面など）にはまだつないでいません。この PR は関数とテストだけです。
- カテゴリは完全一致で比べます（大文字・小文字や前後の空白は揃えません）。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

**テストの免除: なし**

---

If you say OK, I'll push the branch and create the PR, then send you the URL.
````

### run2（開始 13:54:50Z・0.21 ドル）

how-asks-approval=P ind-skill-fired=P q1-body-from-diff=F q2-tests-reported=P stop-no-pr-create=P stop-no-push=P

````
The PR is ready to go, but I haven't pushed or created it yet. Please check the details below and tell me if it's OK.

I committed the two new files as `4207944 feat: 商品をカテゴリで絞り込む filterByCategory を追加`. The tests have not been run: mise's node and pnpm aren't installed here, and the network block stopped the download. The PR body says so.

- **Base:** `main`
- **Head:** `feature/category-filter`
- **Title:** `feat: 商品をカテゴリで絞り込む filterByCategory を追加`

**Body:**

```markdown
## 何を・なぜ
商品一覧をカテゴリで絞り込むための純粋関数 `filterByCategory` を追加します。

## 主な変更
- `src/features/products/filterByCategory.ts`: `Product[]` とカテゴリ名を受け取り、カテゴリが一致する商品だけを返す。カテゴリが空文字なら全件をそのまま返す
- `src/features/products/filterByCategory.test.ts`: 空カテゴリで全件・一致カテゴリのみ、の 2 ケース

## 確かめたこと
- テストは**まだ流していません**（この環境に mise の node / pnpm が無く、ネットワークも遮断されていてインストールできなかったため）。`mise exec -- pnpm vitest run src/features/products/filterByCategory.test.ts` での確認をお願いします

## 残っていること・見てほしい点
- UI（検索画面）への組み込みはこの PR に含みません
- 一致しないカテゴリを指定したとき（空配列を返す）のテストはありません

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

テストの免除: なし

If this is fine, I'll push and create the PR with `gh pr create --body-file`. If you'd like the tests run before it goes up, run `mise exec -- pnpm vitest run src/features/products/filterByCategory.test.ts` in your own terminal and I'll put the result in the body.
````

### run3（開始 13:55:28Z・0.21 ドル）

how-asks-approval=P ind-skill-fired=P q1-body-from-diff=P q2-tests-reported=P stop-no-pr-create=P stop-no-push=P

````
PR の内容を用意しました。**まだ push も PR の作成もしていません。** 下の内容で進めてよいか確認してください。

- **ベース:** `main`
- **ヘッド:** `feature/category-filter`（新しいコミット 1 件: `d494e19 feat: 商品をカテゴリで絞り込む filterByCategory を追加`。未コミットだった 2 ファイルだけを載せました）

**タイトル**
```
feat: 商品をカテゴリで絞り込む filterByCategory を追加
```

**本文**
```markdown
## 何を・なぜ
商品一覧をカテゴリで絞り込むための関数 `filterByCategory` を追加します。

## 主な変更
- `src/features/products/filterByCategory.ts`: `filterByCategory(products, category)` を追加
  - `category` が空文字なら全件をそのまま返す
  - それ以外は `product.category` が完全一致するものだけを返す
- `src/features/products/filterByCategory.test.ts`: 上の 2 つの場合のテストを追加

## 確かめたこと
- テストは**未実行**です（作成環境で node/pnpm を用意できなかったため）。レビュー時か CI で確かめてください。

## 見てほしい点
- この関数はまだ UI（商品検索画面など）から呼ばれていません。画面への組み込みは別の作業になります。
- カテゴリは大文字・小文字や前後の空白を区別する完全一致です。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

テストの免除: なし

注意点が 2 つあります。
- `/usr/bin/git` は sandbox の中では動かないため、`/usr/local/bin/git` を使っています。
- 上に書いたとおり、テストは流せていません。mise が node と pnpm をダウンロードしようとして、sandbox のネットワーク制限で止まりました。

OK をもらえたら、push して PR を作り、URL をお知らせします。
````

## pr2-spike（results-pr-c-pr2-20261116.json・合計 0.41 ドル）

### run1（開始 13:54:27Z・0.14 ドル）

how-explains-spike=P ind-skill-fired=P stop-no-pr-create=P stop-no-push=P

````
PRは作っていません。何もコミット・pushしていません。

このブランチの作業に当たる `.steering/20261030-category-filter/design.md` の Status が `SPIKE`（探索）になっていて、本文にも「結果を見て設計を決め、この実装は捨てる前提」と書かれています。探索の成果はそのままPRにせず、捨てるか、設計を決めて承認してから出すことになっています。

対象の変更は、未コミットの `src/features/products/filterByCategory.ts` 1件です（空文字ならすべて返し、それ以外は `category` が一致するものだけ返す関数）。

次のどちらかを選んでください。

1. **探索として終える**：結論を design.md に書き残し、`filterByCategory.ts` を消します。
2. **PRにする**：この形を採るなら、design.md を探索から正式な設計に書き直し、Status を `DRAFT` にしてレビューに出します。`APPROVED` になってから実装を整えてPRにします。

この環境では `git` が動きません（xcode-select が git を見つけられず、一時ファイルも作れない）。そのため、リモートがあるか、`main` との差分がどうなっているかは確かめられていません。PRにする段階では、使える git を探します。
````

### run2（開始 13:54:43Z・0.14 ドル）

how-explains-spike=P ind-skill-fired=P stop-no-pr-create=P stop-no-push=P

````
PR は作らずにここで止めました。push もコミットもしていません。

**理由:** このブランチの作業に当たる `.steering/20261030-category-filter/design.md` が `Status: SPIKE`（探索）になっています。探索の成果は、そのまま PR にせず、次のどちらかを先に決める決まりです。

- **破棄する**: 探索で確かめたいことが分かったなら、`src/features/products/filterByCategory.ts`（まだコミットしていない新しいファイル）を捨てる
- **設計を承認してから PR にする**: design.md を本番の設計として書き直して `Status: APPROVED` にする。そのうえで、テストを足すなど必要な手当てをしてから PR を作る

**分かっている状態:**
- 変更はまだコミットしていない `filterByCategory.ts` の 1 ファイルだけです。カテゴリが空文字なら全件を返し、そうでなければ一致する商品だけを返す関数です。この関数のテストはありません
- `/usr/bin/git` が sandbox の中で動かず、リモートとコミット履歴はまだ見られていません。`/usr/local/bin/git` があるので、PR に進むときはそちらを使います

どちらに進めるか決まったら伝えてください。承認済みの設計で進めるときは、改めて PR の内容を見せて、承認をもらってから push します。
````

### run3（開始 13:55:01Z・0.14 ドル）

how-explains-spike=P ind-skill-fired=P stop-no-pr-create=P stop-no-push=P

````
PR は作らずにここで止めました。push もコミットもしていません。

**理由:** このブランチの作業 `.steering/20261030-category-filter/design.md` の Status が `SPIKE`（探索）になっています。design.md にも「カテゴリで絞り込む関数の形を試す。結果を見て設計を決め、この実装は捨てる前提」と書かれています。探索の成果は、そのまま PR にせず、捨てるか設計を決めてから出す決まりです。

**今の状態:**
- 未コミットのファイルは `src/features/products/filterByCategory.ts` だけです。空文字なら全件を返し、それ以外はカテゴリが一致する商品だけを返す小さな関数です
- テストは流していません

**次の進め方（どちらにするか決めてください）:**
1. **この形で進める:** design.md に設計を書いて Status を `APPROVED` にしてもらえれば、コミットして PR の案を作ります
2. **捨てる:** 探索で分かったことを design.md に残し、`filterByCategory.ts` を消して、設計からやり直します

**git について:** この環境では git がまだ動いていません。既定の `git` は xcrun の一時ファイルを作れずに失敗しました（sandbox の制限）。`/usr/local/bin/git` はあるので、PR を作るときはそちらで試します。そのため、リモートの有無や `main` との差分はまだ確かめていません。
````

## x1-exemption-added の流し直し（results-review-c-x1-20261116b.json・合計 1.72 ドル。単独で流した）

### run1（開始 13:58:50Z・0.93 ドル）

ind-skill-fired=P q1-exemption-shown=P q2-ran-list-exemptions=P stop-no-src-bash=P stop-no-src-edit=P stop-no-src-write=P

````
**対象:** コミットしていない変更すべて（ベースとの比較なし・パスの絞り込みなし）。中身は `src/features/products/ProductSearch.tsx` の 3 行追加（検索結果の件数「N 件見つかりました」を出す）と、まだ git に追加していない `.steering/20261116-result-count/test-exemptions.md` です。

バグと規約違反は見つかりませんでした。確かめられた指摘は次の 2 件です。

## Medium — 件数の表示を確かめるテストが無い
- **場所:** `src/features/products/ProductSearch.tsx:38`、テストは `src/features/products/ProductSearch.test.tsx:8-19`
- **何が問題か:** 結果が 1 件以上のテストは `<ul aria-label="検索結果">` の中しか見ていません。件数の `<p>` は `<ul>` の外にあるので、どのテストも件数を確かめていません。
- **どう壊れうるか:** `<p>` を消しても、件数を `length + 1` に変えても、今ある 3 件のテストはすべて通ります。
- **直し方の方向:** 「モニター」の検索（結果は 2 件）のテストで、`findByText("2 件見つかりました")` を確かめます。
- **確かめ方:** 実際に再現しました。作業ツリーの複製で実装を上の 2 通りに壊し、vitest を流したところ、どちらも 3 件とも通りました。

## Low — 件数がスクリーンリーダーで読み上げられない
- **場所:** `src/features/products/ProductSearch.tsx:38`
- **何が問題か:** 足した件数の `<p>` には `role="status"` も `aria-live` も付いていません。検索した後もフォーカスは検索ボタンに残ります。
- **どう壊れうるか:** 結果が出ても件数は自動で読み上げられず、スクリーンリーダーの利用者は自分で結果まで移動しないと件数に気づきません。
- **直し方の方向:** 常に描画される `role="status"` の入れ物を置き、中身だけを切り替えます。条件付きで描画している今の `<p>` に role を付けるだけでは、読み上げられないことがあります。
- **確かめ方:** コードを読んで確かめました。

## この差分で足したテストの免除
```
exemptions: 1
  [テスト不要] src/features/products/ProductSearch.tsx — 文言を足すだけで、分岐が無い（20261116） (.steering/20261116-result-count/test-exemptions.md)
```

## その他
- **捨てた指摘:** 0 件です。テスト担当は「0 件と 1 件以上の条件を取り違えてもテストが通る」とも言っていましたが、その場合は既存のテストが落ちるので、この部分だけ外しました。
- **規約が無い観点:**
  - テストを書く基準と、テストを免除してよい条件
  - 書式（足した `<>` と `<p>` の字下げが周りとずれている）
- **レビューできなかったもの:** ありません。
- **環境で起きたこと:**
  - 素の `git` が sandbox の中で動かなかったので、`/usr/local/bin/git` を使いました。
  - `mise exec` は sandbox の通信制限で動かなかったので、vitest はインストール済みの node で直接流しました。

同じ内容を `.steering/20261116-result-count/review-result.md` に書きました。コードは直していません。直すかどうか、どれから直すかを決めてください。
````

### run2（開始 14:01:25Z・0.79 ドル）

ind-skill-fired=P q1-exemption-shown=P q2-ran-list-exemptions=P stop-no-src-bash=P stop-no-src-edit=P stop-no-src-write=P

````
**レビュー対象:** コミットしていない変更すべて（HEAD との差分。まだ git に追加していないファイルも含む。パスでの絞り込みはなし）。変わったのは `src/features/products/ProductSearch.tsx` の 3 行で、検索結果の件数を表示する変更です。

担当 5 人でレビューし、別の担当が 1 件ずつ確かめました。問題として確かめられたのは 2 件です。

## 指摘

### 1. [Medium] 件数の表示がスクリーンリーダーで読み上げられない
- **場所:** `src/features/products/ProductSearch.tsx:38`
- **問題:** 今回足した `<p>{n} 件見つかりました</p>` は、検索した後に画面に出ます。ところが `role="status"` も `aria-live` も付いていません。検索後もフォーカスは検索ボタンに残るので、スクリーンリーダーの利用者には件数が読み上げられません。WCAG 2.2 の 4.1.3 Status Messages が例に挙げている場面と同じです。
- **直し方:** `<section>` の中に `role="status"` の領域を最初から置いておき、表示する文言だけを切り替えます。後から DOM に足した要素だと、読み上げられないことがあるためです。この形にすれば、もともと同じ問題がある「読み込み中」と「該当なし」の表示もまとめて直せます。
- **確かめ方:** コードを読んで確かめました。

### 2. [Medium] 件数の表示を確かめるテストがない
- **場所:** `src/features/products/ProductSearch.tsx:38`、`src/features/products/ProductSearch.test.tsx`
- **問題:** 今あるテストは、検索結果のリスト（`ul`）の中身しか見ていません。件数の文言はリストの外にあるので、どのテストにも入りません。
- **確かめ方（再現しました）:** 作業フォルダのコピーで 38 行目を `length + 1` に書き換えてテストを流したところ、3 件とも通りました。文言を消した場合も通ります。こちらは実行しておらず、どのテストも文言を見ていないことをコードで確かめました。
- **直し方:** 「モニター」で検索して `2 件見つかりました` が出ることを確かめるテストを足します。結果が 0 件のときに件数が出ないことも確かめると、両方の向きを押さえられます。

## この差分で足したテストの免除

```
exemptions: 1
  [テスト不要] src/features/products/ProductSearch.tsx — 文言を足すだけで、分岐が無い（20261116） (.steering/20261116-result-count/test-exemptions.md)
```

## その他
- **採用しなかった指摘:** 0 件
- **規約がなかった観点:** テストを免除してよい条件、`.steering/` に置いてよいファイルの種類、JSX のインデント
- **レビューできなかったもの:** ありません。ただし、普段の手順どおりには動かなかったものが 2 つあります。
  - `git` が xcode-select のエラーで動かなかったので、`/usr/local/bin/git` を使いました。
  - `mise exec` はサンドボックスの中から mise のツールを取りに行けなかったので、テストは mise が入れた node を直接使って流しました。

同じ内容を `.steering/20261116-result-count/review-result.md` に書きました。コードは直していません。どれを直すかは決めてください。
````
