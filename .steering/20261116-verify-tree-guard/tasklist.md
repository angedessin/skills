# tasklist: verify-tree-guard

Last updated: 20261119

design.md が APPROVED になり、`20261116-exemption-visibility` が main に入るまで着手しない。課金のある項目（★）は、見積もりを示して承認を取ってから、通常のターミナルで流してもらう。

## 0. 前提を確かめる

- [x] 公式の hooks のページで、差し戻しが続いたときの Claude Code の側の上限と、`PostToolUse(Agent)` の入力の形を読む（無料）。結果を decisions.md に書く（20261117。上限は 8 回続けての続行。前景の Agent は終了後・背景は起動直後に来る。`report` は PostToolUse(Agent) と親の Stop の両方に置くと決めた。読みだけでテストは無し）
- [x] sandbox の中で、`.env` のある作業ツリーを、denyRead の型を除いて複製する試作を 1 回流す（無料。前提の 8）。結果を decisions.md に書く（20261117。`cp -cR` は .env・.pem で rc=1、除外つきの `rsync -a` は rc=0。複製は rsync にすると決めた。試作のコマンドを手で流しただけで、機械の検査は 1 の run_make_copy.py に入れる）
- [x] ★ 発火を記録するだけの hook（`SubagentStart`・`SubagentStop`・`PostToolUse(Agent)`。入力の JSON をワークスペースの外のファイルに書き、stderr と `additionalContext` に決まった印を出す）を評価の plugin に入れ、`t2-shallow-test` を 1 回流す（0.7〜0.9 ドル）。次を確かめて decisions.md に書く（20261117。`--runs 1` を落として 3 回・2.11 ドル。発火・入力・TMPDIR・.git の regex は可、trace に印は載らない。probe は消して hooks.json を戻した）
  - 3 つのイベントが発火するか
  - `PostToolUse(Agent)` が来るのは起動の直後か終了の後か。入力から agent の id を引けるか
  - stderr と `additionalContext` の印が trace に載るか
  - 評価の sandbox の `$TMPDIR` の値と、Bash からそこに書けるか
  - `SubagentStart` の入力に `agent_id`・`cwd` があるか。4 つのイベント（親の `Stop` を含む）の `session_id` がそろうか
  - ワークスペースの `.git/` の下に書いたファイルを、regex の grader で拾えるか（試しの grader を 1 つ足しておく）
- [x] 上の結果で、design.md の分岐（`report` を置くイベント・印を残す場所・評価をやるか）のどれを採るかを decisions.md に 1 行ずつ書く。評価をやらないなら、4 の項目を「`eval/README.md` に見えないことを書く」だけに直す（20261117。評価は行い、印は .git/ の下に写して regex で見る。report は PostToolUse(Agent) と親の Stop の両方。読み合わせのみでテストは無し）

## 1. 写しと一時ディレクトリのスクリプト

- [x] `frontend-code-review/scripts/make-copy.sh` の写しのモードを書き、`tests/skills/run_make_copy.py` で確かめる（成功時のパスと中身・`.git` が無い・`.git` がファイルの worktree・`GIT=`・`.env` などを除いて `excluded:` を出す）（20261118。複製は除外つきの rsync。写しは review-copy.*/tree、印は review-copy.*/made。python3 tests/skills/run_make_copy.py 13/13。壊した写し 9 種のうち、打ち切りの TERM を外したものだけ通る（KILL で 3 秒以内に止まるため害なし））
- [x] 失敗の扱いを足し、テストで確かめる（`TMPDIR` が書けない・作った先がリポジトリの中・打ち切り。どれもパスを出さず、作りかけが残らない）（20261118。1 つ目と同時に書いた。rsync の失敗・git の外・引数の誤りも足した。同じテストで確かめた）
- [x] `--empty` と古い写しの掃除を足し、テストで確かめる（空のディレクトリ・1 日より古いものだけ消す・古さは印のファイルで測り、時刻の古い作業ツリーから作った写しを消さない）。`package.json` の `test:skills` に足す（20261118。印の無い作りかけはディレクトリの時刻で測る。pnpm run test:skills 全件通過・lint・validate 11/11）
- [x] `review-verify.md`（写しの作り方・差し戻されたときに戻してよいもの）と `frontend-code-review/SKILL.md` の Step 3（スクリプトを渡す・親が自分で再現するときもスクリプトを使う）を直す（`validate` が通ることを確かめる。振る舞いは 4 の評価で確かめる）（20261118。frontend-code-review は 2.3 に。validate 11/11、validate:portability は既存の steering の 2 件だけ。振る舞いは 4 の評価で確かめる）

## 2. 作業ツリーの見張り

- [x] `subagent-tree-guard.sh` の `start` と `stop` の比べる所を書き、`tests/hooks/run_fixtures.py` で確かめる（違いなし・コミット・ブランチ・きれいな追跡ファイル・既に変更のあるファイル・未追跡のファイルの中身・未追跡のディレクトリの下・ステージ・削除・リモートの ref だけ・`stop` の `cwd` が別のリポジトリや写しの中でも控えた根と比べる）（20261118。状態は HEAD・ref（heads・tags・stash）・HEAD と違う追跡ファイルの中身のハッシュ・索引の raw・未追跡のファイルごとのハッシュ。無視されたファイルが変わっても 0 も足した。python3 tests/hooks/run_fixtures.py 501/501（TG1〜TG13）。壊した hook 6 種のうち 5 種を捕まえ、残る 1 種は結果の変わらない書き換え）
- [x] 差し戻しの上限と記録を足し、フィクスチャで確かめる（1 回だけ差し戻す・2 回目は違いが同じでも変わっていても 0・戻った／戻っていないの記録・`start` の 2 回目は上書きしない・控えが無い・git や jq が無い）（20261118。1 つ目と同じ hook に書いた。TG14〜TG20 で確かめた。記録は result に same・differs・returned・not-returned・unchecked）
- [x] `report` を、0 で決めたイベントに合わせて書き、フィクスチャで確かめる（違いのあった未報告の記録を知らせる・「確かめていない」は session ごとに 1 回知らせる・2 回知らせない・記録が無ければ何も出さない・古い記録の掃除）（20261119。PostToolUse は additionalContext、親の Stop は exit 2。async_launched は読まない。差し戻した直後の differs は知らせず、検証役が終わってから知らせる。python3 tests/hooks/run_fixtures.py 512/512（RP1〜RP11）。壊した hook 6 種をすべて捕まえた）
- [x] `settings.json` と `templates/settings.template.json` に登録を足し、`tests/sandbox/check_settings.py` に検査と self-test を足す（壊すと落ちることを確かめる）。`Stop` に足すなら別のグループにし、既存の Stop のゲートの self-test を名前で探す形に直して、足した後も壊すと落ちることを確かめる（20261119。matcher は `^review-verify$`。report は PostToolUse の別グループ（Agent）と Stop の別グループ。self-test の Stop のゲートを名前で探す形に直した。python3 tests/sandbox/check_settings.py OK: 0 failed、見張りの self-test 9 種）
- [x] `frontend-code-review/SKILL.md` に、知らせを受けたときの手順（自分では戻さない・範囲の行の直後に警告・「確かめていない」は「レビューできなかったもの」に書く・`Stop` の分岐なら返答と `review-result.md` に追記）を足し、版を上げる（`validate` が通ることを確かめる）（20261119。Step 3 に受けたときの手順、Step 4 に範囲の行の直後の警告と、報告の後に届いたときの追記を書いた。版は同じブランチで上げた 2.3 のまま。validate 11/11。振る舞いは 4 の評価で確かめる）
- [x] README の hook の依存の一覧・「hook と設定」・コピーの手順・スキルのフォルダのスクリプトを直し、`validate` で一覧と実体の一致を確かめる（20261119。登録と同時に直した。validate 11/11）

## 3. 評価（0 の結果が可のときだけ。否なら最後の項目だけ）

- [x] `prepare.sh` が `eval/hooks/hooks.json` を生成するようにし（追跡をやめ、`eval/.gitignore` に足す）、review の C では見張りを入れる。`./prepare.sh c review` の後に正しい JSON で見張りが入り、`./prepare.sh c design` では今と同じ中身になることを確かめる（20261119。hook に `--mirror-gitdir` を足し、stop の結果を `.git/tree-guard.log` に TREE-GUARD-CHECKED・DIFF・UNCHECKED で写す（TG21〜TG24。run_fixtures.py 516/516）。c review は 4 イベントの登録と hook の複製あり、c design は jq -S で前の hooks.json と一致。b は sandbox の中で mktemp が拒まれて流せず（前からある制約。今回の変更とは別）。一回限りの手での確かめ）
- [x] `eval/gen_review_cases.py` の t2 だけに `stop-tree-checked` を足し、`tests/skills/run_eval_graders.py` の型で正規表現を確かめる（印が 1 回以上で違いが 0 回なら合格・印が無ければ不合格・違いの印があれば不合格）（20261119。evalcase.py に tree_checked を足し、T2 だけで呼ぶ。.git/tree-guard.log に CHECKED があり DIFF が無ければ合格。python3 tests/skills/run_eval_graders.py 26/26（EG21〜EG26）。ファイルが無いときに grader が落ちるかは、4 の評価で確かめる）
- [x] `eval/README.md` の回帰テストの表を直す。評価をやらない場合は、検証役の書き込みが評価では見えないことを書く（20261119。hooks/ の行と、frontend-code-review の行の t2 の説明に stop-tree-checked を足した。文書だけでテストは無し）

## 4. 回帰と仕上げ

- [x] ★ `t2-shallow-test` を 1 回、`l1-large-diff` を 3 回、`x1-exemption-added` を 1 回流す（2〜2.35 ドル。ケースごとに `--runs` を表の回数で必ず付ける）。grader ごとの合否を読み、t2 の trace で検証役が `make-copy.sh` を呼んだことと、`stop-tree-checked` の合否を確かめる。最終回答をこのフォルダに写し、結論と、流さなかったケース（n1・p2・r-c・t1）と理由を decisions.md に書く（20261119。2.24 ドル。全ケース全 grader 合格。検証役は make-copy.sh と cd <パス> && を守った。decisions.md に結論と流さなかったケースを書いた）
- [x] 無料の検査を全部流す（`validate`・`validate:portability`・`test:hooks`・`test:skills`・`test:sandbox`・`lint`）。コマンドと結果を書く（20261119。validate 11/11・validate:portability rc=0・test:hooks 516/516・test:skills 全件・test:sandbox 0 failed・lint 通過）
- [ ] 普段のセッションで、このブランチの差分に frontend-code-review をかけ、見張りの記録（`${TMPDIR}/claude-tree-guard/`）に「確かめた」が残ることを確かめる（一回限りと decisions.md に書く）。出た指摘を直す（20261119 途中。レビューは済み（review-result.md。見張りの記録は same。一回限り）。指摘 1〜5・8〜15 を直して 49585cb。無料の検査は全部通過（test:hooks 530/530）。残り: 壊した hook で ref をブランチだけにしたときに TG26（タグ）が落ちるかを確かめ直す（自動の検査では落ちなかったが、手で流すと hook はタグを見逃した。検査の流し方の問題の疑い）。直した hook は評価で流していない。課金の t2 を 1 回流し直すかを決める）
- [ ] `.steering/skill-issues.md` の 20261114「review-verify の再現が作業ツリーに書き込んだ」に、入れた対策を 1 行添える
- [ ] tasklist.md を更新する
- [ ] pr-create で PR にする（本文に、決めたこと・前提の確かめの結果・回帰の結果を書く）
- [ ] マージの前に steering で閉じる
