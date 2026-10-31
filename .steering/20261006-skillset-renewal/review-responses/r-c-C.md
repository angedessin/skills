<!-- results-review-c-rc.json / r-c-rm-mv-policy / with / 2.51 USD / 421s -->

新しく入った削除ガードの hook（`guard-gated-delete.sh`）は、守るはずの普通の書き方を 2 つすり抜けます。テストはその穴を拾えておらず、壊れても PASS する作りが 2 か所あります。12 件の指摘のうち 11 件が確かめられ、1 件は問題ではないと判定しました。確かめは、作業ツリーのコピーに対して hook を実際に動かして行いました。

## High

**1. パスを `"…"` で囲むと deny されない**（`.claude/hooks/guard-gated-delete.sh:23`）
- 入力: `rm "docs/knowledge/x.md"`、`rm -f "CLAUDE.md"`
- 結果: hook が何も返さず、削除が通ります。引用符なしや `'…'` なら deny されます。
- 原因: コマンドを取り出す `"[^"]*"` が、JSON 内の `\"` のところで切れます。取り出した値は `rm \` だけになります。
- 直し方: コマンドの取り出しを jq や python の JSON パーサに替える。
- 確かめ方: 再現した

**2. 末尾 `/` の無いディレクトリ指定が止まらない**（`guard-gated-delete.sh:37`）
- 入力: `rm -R docs/decisions`、`rm --recursive docs/knowledge`、`mv docs/knowledge /tmp/kb`、`mv a.md docs/knowledge`
- 結果: hook は何も返しません。permissions にも当たらないため（`rm -R` や `mv` の規則がない）、ディレクトリごと消える・移動されます。
- 直し方: `docs/(knowledge|decisions)(/|$|[[:space:]])` のように、パスの区切りで照合する。
- 確かめ方: hook の動きは再現した。permissions に当たらないことはコードを読んで確かめた

## Medium

**3. 関係ないコマンドまで deny される**（`guard-gated-delete.sh:38`）
- 入力: `rm /tmp/x && cat CLAUDE.md`、`rm CLAUDE.md.bak`、`rm NOTCLAUDE.md`
- 結果: どれも deny されます。design.md:45,61,71 の「誤 deny 0」「複合コマンドは何も返さない」と食い違います。
- 原因: 削除対象のパスだけでなく、コマンド全体に境界なしの部分一致をかけています。
- 直し方: rm・mv の引数を 1 つずつ切り出し、それぞれを区切り付きで照合する。
- 確かめ方: 再現した

**4. B16 のテストが、守るはずの退行を検出できない**（`tests/hooks/run_fixtures.py:42-54`）
- B16 のコマンドは `ls` なので、hook は先頭語の判定で抜け、パスの照合まで進みません。
- hook の 38 行目を「payload 全体を grep する」形に書き換えても、テストは 20/20 PASS のままでした。
- 直し方: コマンドを `rm /tmp/foo` にし、`transcript_path` に `docs/knowledge/` を含める。
- 確かめ方: 再現した

**5. hook の出力 JSON が壊れていてもテストが通る**（`run_fixtures.py:92-99`）
- JSON の解析に失敗すると、文字列が一致するかどうかで判定します。
- hook の出力から `}` を 1 つ消しても 20/20 PASS でした。
- 直し方: この代わりの判定をやめ、解析に失敗したら FAIL にする。
- 確かめ方: 再現した

## Low

- **6. 前置き付きの形が素通りする**（`guard-gated-delete.sh:30-34`）: `\rm`・`sudo rm`・`FOO=1 rm`・`command rm` は何も返しません。design.md:71 の「守らない形」に載せるか、塞ぐ。（再現した）
- **7. 大文字小文字の違いで素通りする**: 大文字小文字を区別しない macOS では `rm claude.md` で CLAUDE.md が消え、hook は何も返しません。既存の書き込みガードの hook も同じ線引きです。（再現した）
- **8. `tool_input.description` を含むテストケースが無い**（`run_fixtures.py:74-84`）: hook 自体はこの場合も正しく動きます。（再現した）
- **9. 書き込みガードの回帰テストが 2 件だけ**（`run_fixtures.py:68-70`）: `>>` と `tee` のケースがありません。その hook はこの差分で変わっておらず、正しく動きます。（再現した）
- **10. テストケースが足りない**: 次の 3 種類がありません。（コードを読んで確かめた）
  - 対象外のパスを mv して、何も返さないことを確かめるケース
  - flag 付きの mv
  - 不正な JSON や `\"` を含む入力。`\"` のケースがあれば 1 を検出できていました
- **11. テストの置き場所が設計と違う**: design.md:83 は `tests/hooks/guard-gated-delete/` と書いていますが、実際は `run_fixtures.py` 1 本です。tasklist.md:14 には「相当」と記録済みです。（コードを読んで確かめた）

## 捨てた指摘

- 1 件: design.md:105/125/130 に残る「未解決」の注記。付録にある日付付きの記録で、承認時に :89 と decisions.md で確定済みのため、問題ではないと判定しました。

## 確かめられなかったもの

- Claude Code 本体の permissions 判定は実行できていません。指摘 2 の permissions の部分は、コードを読んだだけです。
- `check_asset_consistency.py` は実行していません。コードを読んだ範囲では整合しています。

同じ内容を `.steering/20260806-rm-mv-policy/review-result.md` に書きました。コードは直していません。どれから直すかを指示してください。
