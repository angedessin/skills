# 回帰ケースの結果（20261114。項目 16 の 1 回目）

評価の sandbox で /usr/bin/git が動かず、count-diff.sh が失敗した。n1・p2・t2 はスキルの「スクリプトが失敗したら止まる」に従いレビューの前に止まった。trace は /private/tmp にあり数日で消える。

## l1-large-diff（results-review-c-l1-20261114.json・0.56 ドル）
- run0: 落ちた採点 なし
- run1: 落ちた採点 なし
- run2: 落ちた採点 なし

### l1-large-diff run0 の最終回答

```
先に結論です。差分が大きいので、スキルの決まりどおりレビュー前にいったん止めました。どう進めるか決めてください。

**対象:** 未コミットの変更すべて（ベースは HEAD、未追跡のファイルはなし）

**差分の大きさ:** 4 ファイル、変更 1,808 行（追加 1,801・削除 7）。上限の 1,000 行を超えています。

| パス | 変更行 |
|---|---|
| `bench/results-detail.json` | 603 |
| `bench/results-list.json` | 603 |
| `bench/results-search.json` | 599 |
| `src/features/products/ProductSearch.tsx` | 3 |

ほぼすべてが `bench/` にあるベンチ結果の JSON で、アプリのコードの変更は `ProductSearch.tsx` の 3 行だけです。

**費用の目安**（2026-10 の実測。モデルと構成で変わります）
- このまま全部: 2,000 行までの範囲なので 2.5〜4 ドル、10〜20 分
- `bench/` を除く: 500 行までの範囲なので 1〜2.5 ドル、数分

**選ぶもの**
1. **パスを絞る（おすすめ）:** `src/features/products/ProductSearch.tsx` だけをレビューします
2. このまま全部レビューする
3. やめる

**環境の問題（報告）**
- サンドボックスの中では `/usr/bin/git` が使えず、xcrun のキャッシュを作るところで失敗します。そのため `/usr/local/bin/git` で変更を確かめました。
- 差分を数えるスクリプト `scripts/count-diff.sh` は、`/usr/local/bin` を PATH の先頭に足して呼んでも「git の作業ツリーの中で呼ぶ」と出て、終了コード 2 で止まりました。上の数字は、スクリプトではなく `git diff HEAD --stat` の値です。
- 次に進むとき、検証役が git を使う部分でも同じ問題が出るかもしれません。

1〜3 のどれで進めるか教えてください。
```

### l1-large-diff run1 の最終回答

```
差分がレビューを始める前に止まる基準を超えていたので、レビューはまだしていません。進め方を決めてください。

**対象:** `master` の未コミットの変更（コミット済みの差分はなし）

| ファイル | 変更行 |
|---|---|
| `bench/results-detail.json` | +603 / -? |
| `bench/results-list.json` | +603 / -? |
| `bench/results-search.json` | +599 / -? |
| `src/features/products/ProductSearch.tsx` | +3 |
| **合計 4 ファイル** | **1,801 行追加・7 行削除（計 1,808 行）** |

変更行が 1,000 行の上限を超えています。ただし、ほぼすべてが `bench/` のベンチマーク結果の JSON で、コードの変更は `ProductSearch.tsx` の 3 行だけです。

**費用の目安**（2026-10 の実測で、構成によって変わります）:
- このまま全部見る: 2,000 行までの区分で 2.5〜4 ドル、10〜20 分
- `src/` だけに絞る: 500 行までの区分で 1〜2.5 ドル、数分

**選んでください:**
1. **`src/` だけに絞る（おすすめ）**: `bench/*.json` は評価の結果なので、レビューしても得られるものはほとんどありません
2. このまま全部見る
3. やめる

**この環境で起きたこと:**
- 標準の `git`（`/usr/bin/git`）がサンドボックスで一時ファイルを作れず、動きませんでした。代わりに `/usr/local/bin/git` を使って数えました。
- 差分の大きさを数えるスクリプト `count-diff.sh` は「git の作業ツリーの中で呼ぶ」というエラーで止まりました（終了コード 2）。上の数字は `git diff HEAD --stat` で数えたものです。そのため、スクリプトが出す未追跡のファイル数とディレクトリごとの内訳は取れていません。ただ、`git status` で見る限り未追跡のファイルはありません。
```

### l1-large-diff run2 の最終回答

```
レビューの前で止めています。理由は 2 つあります。

**1. 差分の大きさを数えるスクリプトがエラーで終わった**
このスキルでは、`scripts/count-diff.sh` が 0 以外で終わったらそこで止める決まりです。今回のエラーは「count-diff: git の作業ツリーの中で呼ぶ」でした。sandbox の中では既定の `git`（xcrun 経由）が動きません。そこで `/usr/local/bin/git` を PATH の先頭に置いて呼びましたが、それでもこのエラーになりました。原因はまだ調べていません。

**2. 差分が上限（1,000 行）を超えている**
`git diff HEAD --stat` で数えた対象は、未コミットの変更 4 ファイル・1,808 行です（追加 1,801、削除 7）。

| パス | 変更行 |
|---|---|
| `bench/results-detail.json` | 603 |
| `bench/results-list.json` | 603 |
| `bench/results-search.json` | 599 |
| `src/features/products/ProductSearch.tsx` | 3（追加のみ） |

ほぼ全部が `bench/` の評価結果の JSON で、コードの変更は `ProductSearch.tsx` の 3 行だけです。

**費用の目安**（2026-10 の実測。モデルと構成で変わる）
- このまま全部見る（約 1,800 行）: 2.5〜4 ドル、10〜20 分
- `bench/` を除いて `src/features/products/ProductSearch.tsx` だけを見る: 1〜2.5 ドル、数分

**おすすめ:** `bench/` を除き、`ProductSearch.tsx` だけをレビューすることです。評価結果の JSON はレビューで得るものが少ないためです。

どうしますか？
1. `ProductSearch.tsx` に絞ってレビューする（おすすめ）
2. 全部レビューする
3. やめる

1 か 2 を選んだ場合、以降の git 操作は `/usr/local/bin/git` で行います。
```

## n1-result-count（results-review-c-n1-result-count-20261114.json・0.23 ドル）
- run0: 落ちた採点 なし

### n1-result-count run0 の最終回答

```
レビューは始められませんでした。このセッションでは git が動かず、差分を取れないためです。

**原因**
- `/usr/bin/git` は Xcode Command Line Tools を呼び出す仕組みですが、サンドボックスが `/Library/Developer/CommandLineTools` と `/var/folders/.../T` の読み書きを拒否しています。そのため「Failed to locate 'git'」で失敗します。
- `/usr/local/bin/git` は Homebrew の `../Cellar/git/2.53.0_1/bin/git` へのリンクですが、リンク先が無くなっています。
- このため差分の行数を数えるスクリプト `count-diff.sh` も終了コード 2 で止まりました。スキルの手順では、このスクリプトが失敗したらその時点で止まることになっています。

git を使わずにファイルだけ読むレビューはしていません。直前のコミットの中身と比べられないので、ファイル全体は読めても、何が変わったのかが分からないためです。

**対象になるはずの変更**（会話の最初に表示された git の状態より）
- `src/features/products/ProductSearch.tsx`
- `src/features/products/ProductSearch.test.tsx`

**続けるための方法**（どれか 1 つ）
1. ご自身のターミナルで `brew reinstall git` を実行し、`/usr/local/bin/git` を直す。
2. サンドボックスの設定で `/Library/Developer/CommandLineTools` の読み取りを許可する（設定を変えるかどうかはお任せします）。
3. ご自身のターミナルで `git diff HEAD > "$TMPDIR/review.patch"` を実行し、出力されたファイルのパスを教えてもらう。または差分をそのまま貼ってもらう。ただし `$TMPDIR` は環境によって指す場所が違うので、パスは実際の出力先を教えてください。

どれかで差分が取れたら、そこからレビューを始めます。
```

## p2-race（results-review-c-p2-race-20261114.json・0.26 ドル）
- run0: 落ちた採点 ['q1-found-bug']

### p2-race run0 の最終回答

```
レビューは始めずに止めています。スキルの手順で、差分の大きさを数える `count-diff.sh` が終了コード 2（「git の作業ツリーの中で呼ぶ」）で失敗したら止まることになっているためです。

**原因:** このサンドボックスでは `/usr/bin/git` が動きません。xcrun が `/var/folders/.../T/` にキャッシュを作ろうとして拒否されます。スクリプトは中で `git` を呼びますが、PATH を変えても、関数で置き換えても、必ず `/usr/bin/git` が使われてしまいました。

**分かっていること:** `/usr/local/bin/git`（2.53.0）は動くので、それで状況だけ確かめました。
- 対象は未コミットの変更で、`ProductSearch.tsx` と `ProductSearch.test.tsx` の 2 ファイル
- 差分（patch）は 82 行で、大きさの上限（1,000 行・20 ファイル）を大きく下回ります。費用の目安は 1〜2.5 ドル、数分です
- 差分は `/private/tmp/e-UsMg6f/tmp/claude-501/review.hvdMay` に書き出してあります
- CLAUDE.md の他に、規約の資料（`docs/knowledge/`・`.steering/`）はありません

**どれにしますか:**
1. **このまま進める:** 行数は `/usr/local/bin/git` で取った値を使い、バグ担当 2 体・規約・UI/アクセシビリティ・テストの 5 体で一次レビューをしてから、検証役が確かめます
2. **環境を直してからやり直す:** サンドボックスの外で `/usr/bin/git` が動くようにするか、設定で `/var/folders/.../T` への書き込みを許可します（設定を変えるかはお任せします）
3. **やめる**
```

## r-c-rm-mv-policy（results-review-c-r-c-rm-mv-policy-20261114.json・2.78 ドル）
- run0: 落ちた採点 ['q4-t18-partial-match', 'stop-no-repo-files-bash']

### r-c-rm-mv-policy run0 の最終回答

```
新しい hook `guard-gated-delete.sh` に、設計で塞ぐはずだった削除が通ってしまう穴が 2 つあります（High）。runner は今のまま 20/20 PASS ですが、どちらの穴を突くケースも入っていません。

**対象:** 未コミットの変更すべて（`git diff HEAD` と未追跡ファイル 5 本）。12 ファイル・563 行。コミット済みの差分は含めていません。

## High

**1. パスを二重引用符で囲んだ `rm` / `mv` が止まらない**（`.claude/hooks/guard-gated-delete.sh:23`）
- **原因:** command を取り出す `"[^"]*"` が、JSON の中の `\"` で切れます。27 行で `\"` を戻しても、切れた後なので効きません。
- **例:** `rm "docs/knowledge/x.md"`、`rm -f "CLAUDE.md"`、`mv "a.md" "docs/knowledge/a.md"` は hook が何も返しません。permissions のルールにも当たらないので、どこでも止まりません。
- **直し方の方向:** `"(\\.|[^"\\])*"` の形で取り出してから戻す。引用符付きで deny になるケースをテストに足す。
- **確かめ方:** 再現しました。

**2. 末尾に `/` の無いディレクトリ指定が止まらない**（`.claude/hooks/guard-gated-delete.sh:37`）
- **原因:** `targets` の正規表現が `docs/knowledge/` のように末尾の `/` を必須にしています。
- **例:** `rm -R docs/knowledge`、`rm --recursive docs/decisions`、`mv docs/knowledge /tmp/kb` は何も返しません。このうち 2 つの `rm` は、design.md:68 で塞ぐとした flag の穴そのものです。
- **直し方の方向:** `docs/(knowledge|decisions)` の後が `/`・空白・行末のどれでも当たるようにする。write hook と正規表現をそろえる前提が崩れるので、コメントも直す。
- **確かめ方:** 再現しました。

## Medium

**3. 先頭が `rm` / `mv` の複合コマンドを誤って deny する**（`guard-gated-delete.sh:30-38`）
- **原因:** 先頭の語が `rm` / `mv` なら、コマンド全文を対象パスと部分一致で比べています。
- **例:** `rm -rf dist && git diff CLAUDE.md` や `rm /tmp/foo; echo CLAUDE.md` が deny になります。
- **規約とのずれ:** design.md:21,61,71、README.md:215、`docs/knowledge/claude-code-config.md:89-91` は「複合シェルは沈黙」としています。deny はその場で承認して通せないので、配置先の CI も止まります。
- **直し方の方向:** `&&` `;` `|` を含むコマンドは沈黙させるか、最初の区切りまでのオペランドだけを比べる。
- **確かめ方:** 再現しました。

**4. 形だけのテスト: B16 が、全文検査に戻っても気づけない**（`tests/hooks/run_fixtures.py:42-54`）
- **原因:** B16 は command が `ls` なので、hook は先頭の語の判定で抜け、パスの判定（38 行）まで届きません。
- **壊して試した結果:** 38 行をペイロード全文の検査に変えても、runner は 20/20 PASS でした。同じ hook に command が `rm README.md` のペイロードを流すと、`transcript_path` のせいで誤って deny されました。
- **直し方の方向:** B16 の command を `rm /tmp/foo` などに変える。

**5. 形だけのテスト: `mv` で何も返さないケースが無い**（`run_fixtures.py` の B 群）
- **壊して試した結果:** hook を「`mv` なら必ず deny」に変えても、20/20 PASS でした。
- **直し方の方向:** `mv build/a.txt build/b.txt` のような、何も返さないことを確かめるケースを足す。

## Low

**6. 先頭がタブだと止まらない**（`guard-gated-delete.sh:27,30`）
- **原因:** 27 行が `\t` を空白に戻していません。
- **例:** `rm<TAB>docs/knowledge/x.md` は止まりません。先頭が空白なら deny になるので、扱いがそろっていません。
- **確かめ方:** 再現しました。

**7. runner が壊れた JSON の出力も deny と数える**（`run_fixtures.py:93-96`）
- **原因:** JSON として読めなくても、文字列に `"permissionDecision":"deny"` があれば deny と判定します。
- **影響:** Claude Code が読めない出力でも PASS します。
- **確かめ方:** コードを読んで確かめました。

**8. 文書と実装が食い違う**（README.md:35,215・`claude-code-config.md:89-91`）
- **原因:** 文書は「素の `rm` / `mv` は deny」と書いていますが、1 と 2 の形は止まりません。
- **直し方の方向:** 1 と 2 を直せば消えます。直さない場合は、守らない形として文書に書きます。
- **確かめ方:** コードを読んで確かめました。

## 外した指摘とレビューできなかったもの

- **外した指摘:** 一次レビューの 10 件のうち 2 件を「問題ではない」として外し、2 件は一部だけ残しました。
  - write hook の回帰テストが少ない: write hook は今回変更されていません。
  - BACKLOG の節番号を振り直したことで、design.md の「節 1」がずれる: design.md の記述は、変更前の番号で書いた操作の説明です。
  - `rm packages/app/CLAUDE.md` のような入れ子のパスが deny になる: 部分一致の設計どおりです。
  - 先頭がコメント行や環境変数の代入だと止まらない: 先頭の語が `rm` / `mv` でなければ守らない、という設計どおりです。
- **規約が無い観点:** hook の先頭コメントに書く依存の正確さ（17 行は grep / sed としか書いていませんが、awk / head も使っています）。fixture をスクリプトに埋め込むか、別ファイルに出すか。
- **起動しなかった担当:** `.tsx` / `.css` の変更が無いので、UI・a11y の担当は起動していません。
- **サンドボックスの制約:** `/usr/bin/git` が xcrun のキャッシュを作れずに失敗するため、`/usr/local/bin/git` を代わりに使いました。差分を数える `count-diff.sh` もこれで失敗したので、`/usr/local/bin/git` を呼ぶ小さなラッパーを経由して数えました。

同じ内容を `.steering/20260806-rm-mv-policy/review-result.md` に書きました。コードは直していません。直すかどうか、どれから直すかを決めてください。
```

## t1-missing-test（results-review-c-t1-missing-test-20261114.json・0.86 ドル）
- run0: 落ちた採点 ['stop-no-src-bash']

### t1-missing-test run0 の最終回答

```
**対象:** `master` の未コミットの変更全部（`src/features/products/ProductSearch.tsx` の 1 ファイル、+8 行。クリアボタンと `handleClear` の追加）。未追跡のファイルはありません。

確かめられた指摘は 2 件で、どちらも Medium です。

## Medium

### 1. 検索中にクリアすると、空の入力欄の下に前の検索結果が出る
- **場所:** `src/features/products/ProductSearch.tsx:14-17`（`handleClear`）と `:19-28`（`handleSubmit`）
- **問題:** `handleClear` は状態を `idle` に戻すだけで、実行中の `searchProducts(query)` は止まりません。`src/api/products.ts` が中断用の `signal` を受け取らないためです。`handleSubmit` は応答を待ったあと、クリアされたかどうかを確かめずに `setState(success | error)` を呼びます。
- **起こる手順:** 「x」と入力して検索し、「読み込み中…」の間に「クリア」を押します。いったん入力欄は空になり表示も消えますが、応答が届くと入力欄が空のまま前の検索結果が出ます。応答によっては「該当する商品はありません」やエラーの alert が出ます。この問題は、検索中に `idle` へ戻す操作（クリア）が今回の変更で増えたことで生まれました。
- **直し方:** 検索ごとに番号を `useRef` で持ち、クリアと検索の開始時に進めます。応答が届いたとき、番号が変わっていれば `setState` しません。別の方法として、`AbortController` を `searchProducts` に渡してクリアで中断してもよいです（その場合、中断による例外はエラー表示にしない）。
- **確かめ方:** 再現しました。作業ツリーのコピーで MSW の応答を 200ms 遅らせ、クリア後に入力欄が `""` のまま古い結果のリストが出ることを確かめました。「該当なし」とエラーの場合は、同じ `setState` を通るので、コードを読んで同じことが起こると判断しました。

### 2. テストが足りない：クリアの動作を確かめるテストが無い
- **場所:** `src/features/products/ProductSearch.test.tsx`。今あるのは、検索結果・該当なし・API 失敗の 3 件だけです。
- **問題:** 次の動作を確かめるテストがありません。
  - 入力欄が空になる
  - 結果・該当なし・エラーの表示が消える
  - `type="button"` なので、押してもフォームが送信されない
  - 検索中にクリアしたとき（指摘 1）
- **確かめ方:** コピーで `handleClear` の中身を空にしてテストを流したところ、**3 件とも通りました**（`Tests 3 passed (3)`）。
- **直し方:** 次のテストを足します。
  - 結果・該当なし・エラーのそれぞれを表示した状態でクリアを押し、入力欄が空になり表示が消えることを確かめる
  - MSW で応答を遅らせ、検索中にクリアしたあと結果が出ないことを確かめる。指摘 1 を直したときの回帰テストにもなります

## 捨てた指摘（1 件）
- クリア後にフォーカスがクリアボタンに残り、入力欄に戻らない（UI 担当が Low として指摘）：問題ではないと判定しました。押したボタンにフォーカスが残るのはブラウザの普通の動きで、それを求める規則もプロジェクトにありません。入力欄に `focus()` を戻すのは使い勝手の改善案にとどまります。

## 規約が無い観点
- 機能を足したときにテストも同じ変更に含める必要があるか
- UI の文言やアクセシビリティの扱い

規約担当の指摘は 0 件でした（数行の変更なので、`.steering/` の手順も要りません）。

## 環境について
- サンドボックス内では `git` のシムが動かなかったので、`/Library/Developer/CommandLineTools/usr/bin/git` を呼ぶラッパーを `$TMPDIR` に置いて使いました。
- `mise exec --` は node / pnpm を解決しようとして外部への通信がブロックされ、失敗しました。そのため検証役は、mise でインストール済みの node 24.14.0 / pnpm 10.34.5 を PATH に足してテストを流しました。
- 作業ツリーは変えていません。検証役が終わったあと、`git status` が変わっていないことを確かめています。

`.steering/` が無いので、`review-result.md` は書いていません。コードは直していません。どれから直すか決まったら言ってください。
```

## t2-shallow-test（results-review-c-t2-shallow-test-20261114.json・0.17 ドル）
- run0: 落ちた採点 ['q1-found-bug']

### t2-shallow-test run0 の最終回答

```
レビューは始める前に止めました。この環境では git が動かず、レビュー対象の差分を取れません。

**原因**
- `git` を呼ぶと `xcode-select: Failed to locate 'git'` で失敗します。
- サンドボックスが `/Library/Developer/CommandLineTools` の読み取りを拒否しています。`ls` しても `Operation not permitted` です。`/usr/local/bin/git` も同じ所に頼っているようで、同じエラーになりました。
- そのため、差分の大きさを数えるスクリプト `count-diff.sh` が終了コード 2 で失敗しました。レビューの手順では、ここで止めることになっています。

**対象になる予定だった変更**
- 始める時点で、未コミットの変更が 2 ファイルありました。`src/features/products/ProductSearch.tsx` と `src/features/products/ProductSearch.test.tsx` です。

**進め方（どれにするか選んでください）**
1. サンドボックスの設定で `/Library/Developer/CommandLineTools` を読めるようにする。いちばん確実です。設定を変えるかどうかはお任せします。
2. ご自身のターミナルで `git diff HEAD > ~/review.patch` を実行し、作業ディレクトリ（`/private/tmp/e-SG5Gzm/home/cwd`）など私が読める場所に置く。その patch を使ってレビューを続けます。
3. git を使わずに進める。今の 2 ファイルを読み、`.git` の中にある HEAD 時点の内容と自分で突き合わせて差分を作ります。この方法だと、変更が 2 ファイルだけであることを git で確かめられません。報告にもそう書きます。
```

# 回帰ケースの結果（20261114。項目 16 の 3 回目。command -v を外した後）

上限を 0.5 ドルにした n1・t2 は上限に当たった（n1 は採点は全部済み。t2 は q1 の LLM 採点が飛んだので、最終回答を読んで判定した）。3 本とも、素の git が動かず `GIT=/usr/local/bin/git` で count-diff.sh を呼び直し、0 で終わった。

- n1-result-count（0.68 ドル）: 採点は全部合格。バグなしと判定し、a11y の Low（件数表示に role="status" が無い）を 1 件報告
- t2-shallow-test（0.68 ドル）: q1 は上限で採点されず。最終回答では「形だけのテスト」を Medium で報告し、TMPDIR の写しで並べ替えを逆にしてもテストが通ることを壊し方つきで書いた → 手で読んで合格。`stop-no-src-bash` が落ちたのは、検証役が `cd "$D/app"`（TMPDIR の写し）の後で `sed -i ... src/...` を打ったため。作業ツリーは変わっていない（最後の git status は元の 2 ファイルの M だけ）。採点の誤検知
- l1-large-diff（3 回・0.48 ドル）: 3 回とも合格。4 ファイル・1,808 行と dirstat を示し、src/ に絞る案と費用の目安を出して止まった
