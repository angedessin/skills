<!-- results-review-b-rc.json / r-c-rm-mv-policy / with / 1.78 USD / 227s -->

## レビュー結果

hook（`guard-gated-delete.sh`）は、design が「塞ぐ」と約束した形を取りこぼし、「沈黙」と約束した形を止めています。配線（settings 登録、`deploy_skills.py`、consistency 契約、文書、permissions 不変）は design どおりです。

フルモードで test・impl・security・correctness の 4 役を並列で回しました。`.ts`/`.tsx`/`.css` の変更が無いので、a11y・perf・ui は対象なしです。重要な問題（Medium 以上）は 12 件で、4 役が同じ穴を指摘した分など重複 15 件を 1 件ずつにまとめています。

### High（3 件、すべて手元で hook に入力を通して再現済み）

1. **ダブルクォートで囲むと素通りする**（`.claude/hooks/guard-gated-delete.sh:23`）
   - `rm -f "docs/knowledge/x.md"` が沈黙します。エージェントがよく書く形です。
   - 原因は、`"[^"]*"` が JSON 内のエスケープされた `\"` の位置で切れることです。そのため 27 行目の `\"` を戻す処理には到達しません。
2. **ディレクトリそのものへの削除・移動が素通りする**（`guard-gated-delete.sh:37`）
   - 素通りするのは `rm -R docs/knowledge`、`rm -f -r docs/decisions`、`mv docs/knowledge /tmp/k`、`mv a.md docs/knowledge`、`rm -rf docs` です。
   - 原因は、対象パスの文字列が末尾の `/` を必須にしていることです。
   - 既存の permissions で止まるのは `rm -rf` / `rm -fr` だけです。
3. **後ろに続く別のコマンドで止めてしまう（design の契約コアと不一致）**（`guard-gated-delete.sh:37-38`）
   - `rm -f .tmp/a && git add docs/knowledge/x.md` が deny されます。
   - 原因は、オペランドだけでなくコマンド全文を検査していることです。design の「オペランドに対象パス」「複合は沈黙」に反します。

### Medium の主なもの
- **部分一致による誤 deny**: `rm OLD-CLAUDE.md` や `mv notes/CLAUDE.md.bak …` が deny されます。
- **ランナーの判定が緩い**: JSON パースに失敗したとき部分文字列一致に切り替わるので、壊れた出力でも pass します。`hookEventName` も検査していません。
- **B16 が回帰テストとして効いていない**: command が `ls` なので、先頭トークンの判定だけで沈黙します。全文検査禁止の確認になっていません。
- **フィクスチャの抜け**: 上の High の形、壊れた入力、write hook の回帰（2 件しかない）が足りていません。
- **文書と実装の食い違い**: README・starter-kit・claude-code-config の「複合は沈黙」と実装が合っていません。

### 判断していただきたいこと
- 3 は、実装を design に合わせれば直ります（design の変更は不要）。
- 1 と 2 は、hook で塞ぐか、「守らない形」として design と文書に明記して APPROVED を追認するかを決めてください。ディレクトリごとの削除がいちばん被害が大きいので、私は塞ぐ方を勧めます。

### 実行できなかったこと
- `pnpm run test:hooks` と `validate:assets` は実行できていません。サンドボックスが mise の取得通信と、anaconda の python・jq のライブラリ読み込みを拒否したためです。hook 系の指摘は bash で直接実行して確かめ、ランナー側の指摘はコードを読んで確かめました。

詳細は `.steering/20260806-rm-mv-policy/review-result.md`（Status: OPEN）に書き、`.codify-needed` も作成しました。レビュー用の差分は `.tmp/review.patch` に残っています（gitignore 対象）。

次のステップ:
- [ ] 1・2 の方針を決める（塞ぐか、design への明記と APPROVED の追認か）
- [ ] hook とフィクスチャを修正する
- [ ] 修正後に、指摘があった軸だけ再レビューする
- [ ] knowledge-capture、PR、compound、steering archive
