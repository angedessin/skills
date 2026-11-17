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
