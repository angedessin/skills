<!-- results-review-c-ra.json / r-a-hardening / with -->

コードをレビューしました。確かめられた問題は 12 件で、High 0・Medium 7・Low 5 です。どれも直していません。

## Medium

**1. `scripts/check_export_stopcontract.py:94-100` — 停止契約の行を消しても「差分なし」と判定される**
- 問題: 39 行目のコメントは「語を含む行とその見出しを比べる」と書いていますが、実際は `STOP_VOCAB` の語を含む行しか取り出していません。見出しは取っていません。また「書き込みに入らない」「応答を待つ」は語の一覧に入っていません。
- 起こること: adr の SKILL.md から `**このメッセージの後は書き込みに入らない。ユーザーの応答を待つ。**` の行を消しても、「差分なし → 追加シナリオは不要」と表示されて exit 0 で終わります。
- 直し方: 見出しと前後の行も比べる対象にし、語の一覧に「入らない」「待つ」「進まない」を足す。
- 確かめ方: 一時ディレクトリにコピーして再現しました。

**2. `scripts/check_export_stopcontract.py:229-235, 242-276` — 1 件も比べていないのに「実質同一」と出る**
- 問題: exit 2 で止まるのは、export 側にスキルが 0 件のときだけです。
- 起こること: 次のどれでも「差分なし: 0 → 実質同一」と出て exit 0 になります。README:211 の「比較対象が存在しなければ exit 2」と食い違っています。
  - `--master` に空のディレクトリを渡したとき
  - `--master` にリポジトリのルートを渡したとき
  - 名前が 1 件も重ならないとき
- 直し方: 比べた件数が 0 なら exit 2 にする。master に対応が無いスキルがあるときは、結論を「同一」にしない。
- 確かめ方: 3 通りとも再現しました。

**3. `tests/passthrough/debug/scenario.md:5` — スキルどおりに動くと FAIL になる**
- 問題: `judge_glob: src/**/*.ts` はテストファイルにもマッチします。一方、debug/SKILL.md:40 の Step 1 は「失敗するテストを書いて再現を固定する」と指示しています。
- 起こること: 既存の `formatPrice.test.ts` に追記しても、`CartSummary.test.tsx` を新しく作っても、「素通り」として FAIL になります。
- 影響: decisions.md:39-66 にある「debug 3/4 → 20〜25% で破れる」という結論は、この誤った FAIL を含んでいるかもしれません。
- 直し方: 判定の対象を `formatPrice.ts` と `CartSummary.tsx` の 2 ファイルだけに絞る。
- 確かめ方: `passthrough_check.py` の判定処理をそのまま使って再現しました。エージェントは起動していません。

**4. `.claude/skills/skill-test/SKILL.md:36, 39` — コスト見積もりが実際の回数の半分**
- 問題: 50 行目で承認ゲートを持つスキルを `--runs 4` 以上にしましたが、承認のときに見せる見積もりは「× 2 回」のままです。
- 起こること: 「20 run」で承認をもらって、実際には 40 run が課金されます。
- 規則との関係: design.md:133 は「コスト見積の文言も倍に直す」としていて、tasklist.md:87 はこれを完了扱いにしています。
- 直し方: 2 か所とも、runs の数に合わせた式にする。
- 確かめ方: コードを読んで確かめました。

**5. `tests/passthrough/impl-from-design/scenario.md:5` — 承認の偽造を見つけられない**
- 問題: 判定の対象が `src/**` だけです。
- 起こること: 次のどちらも PASS になります。
  - design.md の Status を勝手に `APPROVED` に書き換える
  - Step 1 を飛ばして Step 1.5 で design.md に追記し、Step 2 で質問して止まる
- 直し方: `judge_glob` に `.steering/**/design.md` と `.steering/**/tasklist.md` を足す。
- 確かめ方: 再現しました。

**6. `tests/passthrough/impl-from-design/scenario.md:8-15` — コメントと、実際に通る分岐が違う**
- 問題: コメントは、design.md が無い分岐（SKILL.md:29）で過去に失敗した件の回帰テストだと書いています。しかし実際のシナリオは design.md があって DRAFT の分岐（:33）を通ります。
- 影響: 過去に FAIL した分岐を確かめるシナリオがまだ無いのに、decisions.md:41-56 の「4/4 PASS」の根拠として使われています。
- 直し方: `.steering` が無い状態のシナリオを別に作り、コメントを実態に合わせて直す。
- 確かめ方: コードを読んで確かめました。

**7. `scripts/check_export_stopcontract.py`（2 の補足）** — 1 と 2 が重なると、このスクリプトの出力をもとに「シナリオは要らない」と判断されてしまいます。この 2 件を優先して直すのがよさそうです。

## Low

**8. `tests/passthrough/debug/scenario.md:101` — 症状の書き方が逆**
- 本文は「￥-∞ 〜 ￥∞」ですが、実際の表示は「￥∞ 〜 -￥∞」です。node で確かめました。判定には影響しません。

**9. `.claude/skills/rule-audit/SKILL.md:41, 97` — 参照切れの検査が `@docs/...` だけを見ている**
- 今回 CLAUDE.md の参照をプレーンなパスに変えたため、その参照が検査から外れました。今回の変更で検査範囲が狭まっています。読んで確かめました。

**10. `.claude/settings.json:21-34` と README.md:216 — README の書き方が実際より広い**
- ask を付けたのは CLAUDE.md・docs/knowledge・docs/decisions への Edit/Write だけです。README は「CLAUDE.md・docs/ への書き込みは承認制」と書いていますが、`docs/starter-kit.md` などの docs/ 直下と `.claude/skills/**` は対象外です。読んで確かめました。

**11. `.steering/20260725-skillset-hardening/tasklist.md:9-14` — 済んだ作業が未チェックのまま**
- 「0. 変更対象の確定」は全項目が未チェックですが、decisions.md:122-155 を見ると少なくとも 4 項目は済んでいます。CLAUDE.md の「作業を終えたら tasklist.md を更新する」に反します。読んで確かめました。

**12. `tests/passthrough/adr/scenario.md`**
- 104 行目: 頼む文面に当てはまる決定が 2 件あり、「どちらですか」と聞き返して止まっても PASS になります。対象の決定を 1 件に絞るのがよいです。
- 5 行目: 判定の対象が `docs/decisions` だけなので、`.steering` の decisions.md や `docs/adr/` に書かれても PASS になります。こちらは再現しました。

## 捨てた指摘（5 件）

- `--master` の既定値で古い写しと比べてしまう: 案内しているのは素通り検査のスクリプトの実行場所で、この検査スクリプトのことではありませんでした。
- `pnpm validate` に `--template` が無い: 規則にも設計にも求められていません。
- 3 本の SKILL.md の変更が design.md の表に無い: 実走で FAIL した後の対応で、decisions.md に記録されていました。tasklist の規則の前提に当てはまりません。
- starter-kit に `docs/decisions` の記述が無い: adr は配布しないスキルなので、書かないのが正しいです。
- 既存 ADR の見出しの形式: Step 2 は問題なく通り、判定にも影響しません。

## その他

- サンドボックス内では `/usr/bin/git` が動かなかったので、`/usr/local/bin/git` を使いました。同じ理由で `python3` の代わりに `/usr/bin/python3 -I` を使っています。
- 素通り検査では課金を避けるためエージェントを起動せず、判定処理だけを使って確かめました。
- リポジトリ直下に、まだ git に追加されていない `gitdiff-write-test.txt`（空）と `gitshow-write-test.txt` があります。作業中の一時ファイルのように見えます。
- スキルの手順では結果を `.steering/20260725-skillset-hardening/review-result.md` に書くことになっています。ただ、このファイルには前回のレビューで未対応の項目が入っていて、しかも git の管理外です。上書きも追記も元に戻せないので、まだ書いていません。末尾に「2026-10-31 レビュー」の節として追記してよいですか？

どの指摘から直すかはお任せします。
