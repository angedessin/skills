# tasklist: verify-tree-guard

Last updated: 20261116

design.md が APPROVED になり、`20261116-exemption-visibility` が main に入るまで着手しない。課金のある項目（★）は、見積もりを示して承認を取ってから、通常のターミナルで流してもらう。

## 0. 前提を確かめる

- [ ] 公式の hooks のページで、差し戻しが続いたときの Claude Code の側の上限と、`PostToolUse(Agent)` の入力の形を読む（無料）。結果を decisions.md に書く
- [ ] ★ 発火を記録するだけの hook（`SubagentStart`・`SubagentStop`・`PostToolUse(Agent)`。入力の JSON をワークスペースの外のファイルに書き、stderr と `additionalContext` に決まった印を出す）を評価の plugin に入れ、`t2-shallow-test` を 1 回流す（0.7〜0.9 ドル）。次を確かめて decisions.md に書く
  - 3 つのイベントが発火するか
  - `PostToolUse(Agent)` が来るのは起動の直後か終了の後か。入力から agent の id を引けるか
  - stderr と `additionalContext` の印が trace に載るか
  - 評価の sandbox の `$TMPDIR` の値と、Bash からそこに書けるか
- [ ] 上の結果で、design.md の分岐（`report` を置くイベント・印を残す場所・評価をやるか）のどれを採るかを decisions.md に 1 行ずつ書く。評価をやらないなら、4 の項目を「`eval/README.md` に見えないことを書く」だけに直す

## 1. 写しと一時ディレクトリのスクリプト

- [ ] `frontend-code-review/scripts/make-copy.sh` の写しのモードを書き、`tests/skills/run_make_copy.py` で確かめる（成功時のパスと中身・`.git` が無い・`.git` がファイルの worktree・`GIT=`）
- [ ] 失敗の扱いを足し、テストで確かめる（`TMPDIR` が書けない・作った先がリポジトリの中・打ち切り。どれもパスを出さず、作りかけが残らない）
- [ ] `--empty` と古い写しの掃除を足し、テストで確かめる（空のディレクトリ・1 日より古いものだけ消す）。`package.json` の `test:skills` に足す
- [ ] `review-verify.md` と `frontend-code-review/SKILL.md` の Step 3（スクリプトを渡す）を直す（`validate` が通ることを確かめる。振る舞いは 4 の評価で確かめる）

## 2. 作業ツリーの見張り

- [ ] `subagent-tree-guard.sh` の `start` と `stop` の比べる所を書き、`tests/hooks/run_fixtures.py` で確かめる（違いなし・コミット・ブランチ・きれいな追跡ファイル・既に変更のあるファイル・未追跡のファイルの中身・未追跡のディレクトリの下・ステージ・削除・リモートの ref だけ）
- [ ] 差し戻しの上限と記録を足し、フィクスチャで確かめる（1 回だけ差し戻す・2 回目は違いが同じでも変わっていても 0・戻った／戻っていないの記録・`start` の 2 回目は上書きしない・控えが無い・git や jq が無い）
- [ ] `report` を、0 で決めたイベントに合わせて書き、フィクスチャで確かめる（違いのあった未報告の記録だけ知らせる・2 回知らせない・記録が無ければ何も出さない・古い記録の掃除）
- [ ] `settings.json` と `templates/settings.template.json` に登録を足し、`tests/sandbox/check_settings.py` に検査と self-test を足す（壊すと落ちることを確かめる）
- [ ] `frontend-code-review/SKILL.md` に、知らせを受けたときの手順（自分では戻さない・報告の先頭に警告）を足し、版を上げる（`validate` が通ることを確かめる）
- [ ] README の hook の依存の一覧・「hook と設定」・コピーの手順・スキルのフォルダのスクリプトを直し、`validate` で一覧と実体の一致を確かめる

## 3. 評価（0 の結果が可のときだけ。否なら最後の項目だけ）

- [ ] `prepare.sh` が `eval/hooks/hooks.json` を生成するようにし（追跡をやめ、`eval/.gitignore` に足す）、review の C では見張りを入れる。`./prepare.sh c review` の後に正しい JSON で見張りが入り、`./prepare.sh c design` では今と同じ中身になることを確かめる
- [ ] `eval/gen_review_cases.py` に `stop-tree-checked` を足し、`tests/skills/run_eval_graders.py` の型で正規表現を確かめる（印が 1 回以上で違いが 0 回なら合格・印が無ければ不合格・違いの印があれば不合格）
- [ ] `eval/README.md` の回帰テストの表を直す。評価をやらない場合は、検証役の書き込みが評価では見えないことを書く

## 4. 回帰と仕上げ

- [ ] ★ `t2-shallow-test` を 1 回、`l1-large-diff` を 3 回流す（1.2〜1.4 ドル）。grader ごとの合否を読み、t2 の trace で検証役が `make-copy.sh` を呼んだことと、`stop-tree-checked` の合否を確かめる。最終回答をこのフォルダに写し、結論と、流さなかったケース（n1・p2・r-c・t1）と理由を decisions.md に書く
- [ ] 無料の検査を全部流す（`validate`・`validate:portability`・`test:hooks`・`test:skills`・`test:sandbox`・`lint`）。コマンドと結果を書く
- [ ] 普段のセッションで、このブランチの差分に frontend-code-review をかけ、見張りの記録（`${TMPDIR}/claude-tree-guard/`）に「確かめた」が残ることを確かめる（一回限りと decisions.md に書く）。出た指摘を直す
- [ ] `.steering/skill-issues.md` の 20261114「review-verify の再現が作業ツリーに書き込んだ」に、入れた対策を 1 行添える
- [ ] tasklist.md を更新する
- [ ] pr-create で PR にする（本文に、決めたこと・前提の確かめの結果・回帰の結果を書く）
- [ ] マージの前に steering で閉じる
