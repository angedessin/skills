# review-result: close-before-merge

## 20261121 — frontend-code-review（main...feature/close-before-merge-impl、.steering/ を除く。9 ファイル・374 行）

一次: review-bug ×2・review-rules・review-test。検証: review-verify（一時リポジトリと写しで再現）。作業ツリーの変化なし。

### High
- A: steering 閉じる手順 6 の `git rm -r` が、書き換え済みの tasklist.md（pr-create Step 5.2・再開の手順 4 が書く）で毎回止まる。-f で消すと変更は履歴に残らず、手順 2 の「消したフォルダの最後の中身として履歴に残る」「1 つのコミット」は成り立たない（一時リポジトリで再現）。方向: tasklist の更新を先に別コミットにして push は 1 回、または tasklist を書き換えず番号は索引の行だけに残す

### Medium
- D: 閉じる手順 3 の `gh pr view` は今のブランチの PR を返す。hook が印を付けた古いタスクを別ブランチで閉じると、無関係な PR 番号を索引に書き、その PR に push する（読み）。方向: push の予告は、タスクがこのブランチで作られた（統合ブランチの tree に無い）ときだけ
- E: 再開から閉じるとき、最後の項目の .steering/ の外の未コミットの変更が手順 2・7.2 で拾われず、PR に入らない（読み）。方向: 7.2 の前にリポジトリ全体の未コミットを見て、先にコミットするか聞く
- J: 「PR の項目: `pr-create` を含む行」が部分一致で、バッククォートの中（`pr-create/SKILL.md`・`stop-no-pr-create`）も当たる。このタスク自身の tasklist で当たる（読み）。方向: 閉じる項目と同じくバッククォートの中を除く
- T1（形だけのテスト）: hook の `^Status:…APPROVED` のアンカーを `grep -q APPROVED` に壊しても SS1〜SS12 は全部通る（写しで壊して流した）。方向: 本文に APPROVED を書いた DRAFT と、`Status: APPROVED（日付）` の fixture を足す
- T4（評価ケースが足りない）: steering の「PR の項目にチェックと番号が無ければ閉じる確認を出さない」を見るケースが無い（読み）。方向: s4 の PR の項目だけを未チェックにした s5

### Low
- A2: 手順 2 の例外が「チェックと番号だけ」で、設計の「項目のチェック」と再開の手順 4 の注記より狭い（安全側で止まる）
- B: 閉じてよい状態の条件 2 は番号を要るが、pr-create Step 4・5.1 は「チェックを付けたと仮定」だけ（評価ではモデルが補って 3/3）
- C: 手順 7 の PR 状態の再確認が書き込みの後。MERGED なら history.md と削除がブランチに残り、片付けが無い
- F: hook の `git show "$ref:.steering/..."` は repo の根からのパスで、サブディレクトリのプロジェクトでは印が付かない（再現。`./` を付ければ直る）
- G: origin/main で閉じ済みでも、古いローカル main にあれば印が付く（再現）
- H: 今は毎回 git を呼ぶ。CLT の無い macOS のスタブがダイアログを出しうる（読み。未再現）
- K: どの git も起動しないときの行き先が無く、archived へ移すと読まれうる（eval-s4 run 2 が案 B に出した）
- L: origin/HEAD が origin/main のとき、refs/heads/main を 2 回見る（再現）。partial clone で timeout を超えるかは確かめられない
- N: pr-create の description に、PR の後の閉じる確認で止まることが無い（template の「どこで止まるか」）
- T2: 統合ブランチの ref が複数ある fixture が無い
- T3: ref があり印が 0 件のとき、案内の 1 行が出ないことを見ていない
- T5: pr-create Step 4 の「未チェックが残る」「ベースが統合ブランチでない」の評価ケースが無い
- T6: s4 の q1-test-added は空のテストでも通る。stop-no-remove はタスクのフォルダへ cd してからの `rm -rf ./*` と変数経由を拾わない。pr5 の q1-no-close-notice は否定だけ（完了条件どおり）

### この差分で足したテストの免除
なし（exemptions: 0）

### 捨てた指摘
- 1 件: I（hook と「閉じずにマージ」の衝突）— 問題ではない。Step 4 の「閉じません」は開いた PR に作業を足す場面の文で、未チェックのままのマージは CLAUDE.md に反し、それを拾うのが hook の目的
- T6 の一部（`git -C <dir> rm` を拾わない）— 問題ではない（拾う）

### 規約が無いと報告された観点
- コードのコメントに経緯（日付つきの出来事）を書いてよいか（CLAUDE.md・docs/ に規則が無い。auto-memory には「コメントは理由だけ」）
- pr-create が gh を使わず Web で PR を作った場合の Step 5 の動き

### レビューできなかったもの
- 変える前のコードで新しいテストを流す手順（run-tests-on-base.sh）は vitest 用で、tests/hooks/run_fixtures.py（Python）には使えない。T1 は検証役が写しで実装を壊して確かめた

### 対応（20261121）
A・A2・B・C・D・E・F・J・K・L（重複）・N・T1・T2・T3・T4・T6 を直した。G・H・T5・L（partial clone）は残した（理由は decisions.md）。
