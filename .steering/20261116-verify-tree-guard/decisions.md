# decisions: verify-tree-guard

## 20261117 — 公式の hooks のページで確かめたこと（前提の 2・5・6。https://code.claude.com/docs/en/hooks を同日に取得）

- 前提 5（差し戻しの上限）: Stop・SubagentStop には「8 回続けて続行させたら、次の block を無視して終える」上限がある。数はツールを呼ぶたびに 0 に戻る（`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` で変えられる）。こちらの「agent ごとに 1 回」の方が厳しいので、設計は変えない
- 前提 6（`SubagentStart` の入力）: 共通の欄（`session_id`・`cwd`・`transcript_path` など）に加えて `agent_id`・`agent_type` が来る。`SubagentStop` も同じ共通の欄と `agent_id` を持つ。`session_id` が評価の実行でそろうかは、0 の試し実行で確かめる
- 前提 2（`PostToolUse(Agent)` の時点）:
  - 前景の Agent は、終わった後に来る。`tool_response` に `status: "completed"` と `agentId` がある
  - 背景の Agent（と、途中で背景に回ったもの）は、背景に回った時点で来る。`status: "async_launched"` と `agentId` があり、使用量の欄は無い
  - 背景の agent が終わったときに、親の側で `PostToolUse(Agent)` がもう一度来るとは書かれていない。報告は subagent の `SubagentHandback` ツールで届き、その呼び出しは subagent が止まる前に起きる
- SubagentStop は、Claude Code の内部の agent（提案・`/btw`）でも走り、そのとき `agent_type` は空。matcher で名前を指定すれば当たらないので、見張りへの影響は無い
- SubagentStart の exit 2 の stderr は、subagent 側の transcript に通知として出るだけ（Claude は読まない）。`start` が失敗を知らせる手段にはならない

### 採った分岐

- `report` を置くイベント: 「`PostToolUse(Agent)` と親の `Stop` の両方」（design.md の b の 2 つ目）。前景なら `PostToolUse(Agent)` で知らせられるが、背景で起動したときは `PostToolUse(Agent)` が起動の直後に来て、その時点では記録が無い。レビューのスキルが検証役を前景で呼ぶとは限らないので、親の `Stop` でも拾う
  - そのため、c の「`Stop` の分岐を採った場合」（返答と `review-result.md` に追記する）と、構成の「`check_settings.py` の self-test を名前で探す形に直す」は実装する
- `PostToolUse(Agent)` で `status` が `async_launched` なら、記録を読まずに終える（まだ終わっていない）

## 20261117 — sandbox の中の複製の試作（前提の 8。無料）

`.tmp/copy-probe.*/src/` に `a.ts`・`sub/.env.local`・`key.pem` を置き、このセッションの sandbox の中から `$TMPDIR` へ複製した。

- `cp -cR`: `.env.local` と `key.pem` で `Operation not permitted`、rc=1。ほかのファイルは写る（失敗しても続ける）。プレモータム 20261117 の採った穴 2 が実際に起きることを確かめた。`*.pem` も sandbox の denyRead に入っている
- `rsync -a --exclude='.env*' --exclude='*.env' --exclude='*.pem' --exclude='*.key' --exclude='.git'`（macOS は openrsync）: rc=0。写しに `a.ts` と `sub/` だけが残る
- 時間: このリポジトリの `node_modules`（134M・173 ファイル）で `cp -cR` 0.05 秒、`rsync` 0.78 秒。rsync は clonefile を使わないので、ファイルの多い配置先では遅くなる。大きな配置先では測っていない

### 決めたこと（design.md の a の「複製は、macOS は `cp -cR`、それ以外は `cp -a --reflink=auto`」を置き換える）

- 複製は `rsync -a` と除外の指定で行う。`cp` では除外ができず、sandbox の中で必ず rc≠0 になるため
  - 却下: `cp -cR` の後に写しから除外の型を消す — sandbox の中では cp が失敗で終わり、本物の失敗と区別できない。sandbox の外では秘密が一度 `$TMPDIR` に写る
  - 却下: `node_modules` だけ `cp -cR` — パッケージの中に `*.pem`（試験用の証明書）を持つものがあり、同じく失敗する
- rsync が無ければ、スクリプトの失敗（0 以外・パスを出さない）にする。検証役は読みで判定する
- 遅さは、tasklist の 4 の普段のセッションでの確かめで時間を測り、打ち切り（既定 60 秒）に当たるなら見直す
- 除外したファイルの件数（`excluded:`）は、rsync の出力からでなく、`find` で同じ型を数えて出す（openrsync と GNU rsync で出力の形が違うため）

## 20261117 — 評価の中の hook の試し実行（前提の 1・2・3・4・6・7。課金）

`eval/hooks/probe.sh`（一回限り。終えて消し、`hooks.json` を戻した）を `SubagentStart`・`SubagentStop`・`PostToolUse(Agent)`・`Stop` に matcher なしで登録し、`t2-shallow-test` を流した。結果は `eval/results-review-c-t2-probe-20261117.json`（追跡外）と `/tmp/claude-hook-probe/`。Claude Code 2.1.326。

- `--runs 1` を付け忘れ、3 回流れて 2.11 ドル（見積もりは 1 回 0.7〜0.9 ドル）。`.steering/skill-issues.md` に記録した。3 回分そろったので、下は 3 回の結果
- 前提 1（発火）: 成り立つ。4 つのイベントがすべて発火した。`agent_type` は `eval-c:review-verify` など plugin の名前つき
- 前提 2（`PostToolUse(Agent)` の時点）: review-verify は 3 回とも前景（`run_in_background: false`）で起動され、`SubagentStop` の後に `status: "completed"` と `agentId` つきで来た。一次レビューの 4〜5 体は、3 回中 2 回が背景で起動され（`async_launched`）、終わったときの `PostToolUse(Agent)` は来なかった
- 前提 3（trace に載るか）: 成り立たない。trace に hook の記録があるのは `SessionStart` だけで、`additionalContext`・stderr の印は 3 回とも見つからなかった（`ind-probe-ctx`・`ind-probe-stderr` が不合格）
- 前提 4（`$TMPDIR`）: 成り立つ。モデルの Bash の `$TMPDIR` は `/private/tmp/e-*/tmp/claude-501` で、`mktemp` と写しの作成（`verify.*/app`）が通った。hook の `$TMPDIR` は `/private/tmp/e-*/tmp`（sandbox の外）
- 前提 6（入力のキーと session）: 成り立つ。`SubagentStart` に `agent_id`・`agent_type`・`cwd` がある。1 回の実行の中で 4 つのイベントの `session_id` がそろい、`SubagentStart` と `SubagentStop`・`PostToolUse` の `agentId` が一致した。`cwd` は親も subagent もワークスペースの根（`/private/tmp/e-*/home/cwd`）
- 前提 7（`.git/` の下を regex で読めるか）: 成り立つ。`.git/hook-probe.log` を見る `ind-probe-gitdir` が 3 回とも合格
- ついでに見えたこと: t2 の本来の grader は、3 回とも `q1-found-bug` 以外合格。3 回目の `q1-found-bug` は費用の上限で採点が飛ばされた（`skipped: cost ceiling`）

### 採った分岐

- 評価（design.md の d）は行う。印は trace でなく、ワークスペースの `.git/` の下に写して、ファイルの `regex` で見る（3 が否・7 が可）。写すかどうかは `hooks.json` のコマンドの引数で切り替える
- `report` は、決めたとおり `PostToolUse(Agent)` と親の `Stop` の両方に置く。review-verify は評価では前景だったが、スキルの本文は前景を求めておらず、背景で起動されたときは `PostToolUse(Agent)` が起動の直後に来るため
- `report` のフィクスチャの入力は、実際の入力（`/tmp/claude-hook-probe/` の JSON）の形に合わせる。`PostToolUse` の `tool_response.agentId`・`status`、`SubagentStop` の `agent_id`・`stop_hook_active`

## 20261119 — 回帰（課金。t2 を 1 回・l1 を 3 回・x1 を 1 回）

`./prepare.sh c review`（見張りあり）の後に、通常のターミナルで流した。Claude Code 2.1.328。費用は合計 2.24 ドル（t2 0.90・l1 0.59・x1 0.75。見積もりは 2〜2.35 ドル）。結果は `eval/results-review-c-{t2,l1,x1}-guard-20261119.json`（追跡外）、最終回答は `eval-20261119/` に写した。

- t2: 全 grader 合格（`q1-found-bug`・`q2-ran-tests-on-base`・`stop-no-src-*`・`stop-tree-checked`）。検証役の記録（subagent の transcript）で、`GIT=/usr/local/bin/git bash .../make-copy.sh` で写しを作り、その後の Bash 3 回はすべて `cd .../review-copy.*/tree && ...` で始まり、写しの中でソートを逆にして・外してテストを流したことを確かめた。最終回答に見張りの警告は無い（違いが無かったので正しい）
- l1: 3 回とも全 grader 合格（agent を起動せずに費用を示して止まる）
- x1: 全 grader 合格（免除のパスと理由が報告に載る）。Step 4 の構成を変えた影響は無かった
- 流さなかったケースと理由: n1・p2・r-c・t1。今回の変更は検証役の写しの作り方・見張りの知らせ・報告の警告の位置で、指摘を見つける一次レビューの手順は変えていない。検証役が動く経路は t2 で、報告の構成は x1 で、止まり方は l1 で見た
- 気づいたこと（今回の変更とは別）: t2 で `run-tests-on-base.sh` が「jq が無い」で 2 を返した（20261117 の試し実行の 2.1.326 では通っていた）。q2 は「呼んだか」を見るので合格し、検証役は写しで壊して確かめた。評価の sandbox の道具の見え方が変わった疑いがある。調べていない

## 20261119 — レビュー（review-result.md）の指摘への対応（ユーザー: 推奨どおり、8 も直す）

design.md の次の箇所を、この決定で置き換える。

- **差し戻されたときに検証役が戻してよいもの（指摘 1）:** 「自分が作った・変えたものを戻す（restore・reset --mixed）」をやめ、「自分が新しく作った未追跡のファイルを消すことだけ」にする。restore・reset は索引や HEAD の版に戻すので、開始前からあったユーザーの未コミットの変更まで消す（検証役が一時リポジトリで再現した）。追跡ファイルの書き換え・ステージ・コミット・ref は戻さず、親に「違いが残った」として知らせ、ユーザーが決める
  - 却下: start で中身を退避して元へ戻す — 退避の量と、戻す操作の正しさを新たに確かめる必要があり、見張りが「防ぐ」仕組みに寄ってしまう
- **知らせる単位（指摘 3）:** report は「結果が変わるたびに 1 回」知らせる。差し戻した直後（differs）も「まだ止まり直していない」として知らせ、中断などで 2 回目の終了が来なくても違いが親に届くようにする。終了時に状態を読めないときは unchecked でなく unreadable とし、「控えが無い」と取り違えない
- **取れないパス（指摘 4・6）:** 入れ子のリポジトリ・サブモジュール（ディレクトリ）は HEAD と `status --porcelain` のハッシュ、リンクは指す先、ふつうのファイルはまとめて `--stdin-paths` でハッシュにする。数が合わなければ状態を読めないとする
- **再開と止まり直し（指摘 8。設計の「start は控えを上書きしない」を変える）:** 前の実行が same・returned で終わっていれば、再開の start で控え直す（その間の親やユーザーの書き込みを数えない）。違いが残っていれば控え直さない。start なしに止まり直したとき（背景の作業の終わりなど。20261119 のレビューで、親が書いた review-result.md が違いに出た）は差し戻さず、late-diff として親に 1 回知らせる。評価の .git/tree-guard.log には TREE-GUARD-LATE と書き、DIFF には数えない
- **excluded の件数（指摘 5）:** 当たったディレクトリも 1 件と数え、その下には入らない
- **記録だけにしたもの:** 指摘 6 の大きさ（まとめてハッシュにしたので、git の起動は数回になった。時間は測っていない）と 7（TMPDIR が無いと make-copy.sh は失敗する。設計どおり）は `.steering/skill-issues.md` に残す
