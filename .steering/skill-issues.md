# スキルの問題の記録

新しい事象は「未対応」の末尾に足す。対策を入れたら「対策済み」へ 1 行で移す（日付・事象・対策の場所。中身は git の履歴に残る）。同じ事象が繰り返したら、対策済みの行に「n 回目」と足す。

## 未対応

### 20261114 — 保留: テストのゲートがモノレポを見ない（skill-loop-fixes の PR 1 のレビュー）

- 事象: `stop-test-gate.sh` は根を git のトップレベルに決め、`$ROOT/node_modules/.bin/vitest` が無ければ素通しする。vitest をサブパッケージにだけ入れたモノレポでは、ゲートが何も言わずに効かない
- 期待: 変えたファイルから一番近い package.json の vitest で判定する（パッケージごとに related を流す）か、効いていないことを知らせる
- 今回の扱い: README に対象外と書いた。根の決め方を変えるのは別の設計が要る
- 条件: モノレポの配置先が出たら設計する

### 20261115 — 保留: テストのゲートの所要時間を配置先で測る（skill-loop-fixes の tasklist 10b）

- 事象: stop-test-gate.sh は実装ファイルごとに vitest を起動し、打ち切りは 150 秒（settings の timeout 180）。このリポジトリには vitest が無く、実際のプロジェクトでの時間を測っていない（PR 1 のレビューで「設計どおり」とした性能の件）
- 期待: 打ち切り時間と、実装ファイルごとに起動する作りを見直す
- 条件: 配置先の最初のプロジェクトで所要時間を測る

### 20261119 — 保留: make-copy.sh は TMPDIR が無いと必ず失敗する（verify-tree-guard のレビューの指摘 7）

- 事象: sandbox を使わない配置先（Linux など）では TMPDIR が無いことが多く、検証役も親も再現できずに読みで判定する。設計どおり（sandbox の中で /tmp に落とすと拒まれ、cd の失敗の元になる）
- 期待: TMPDIR が無いときだけ /tmp に落とすかを決める
- 条件: 雛形は sandbox を必須にしているので今は直さない。sandbox を使わない配置先が出たら決める

### 20261118 — 検査の前後を比べるのに git stash を使い、sandbox で途中まで失敗した（verify-tree-guard）

- 事象: `validate:portability` の前後を比べるため `git stash` を流したところ、sandbox が `.claude/` の下を書かせず `unable to unlink old ...` で途中まで失敗した。stash の項目だけが残り、作業ツリーは変わらなかった（stash と差分 0 を確かめた）
- 期待: sandbox の中では、作業ツリーを動かす git（stash・checkout・reset）で前後を比べない。前の版は `git show HEAD:<パス>` か `git worktree` でなく一時ディレクトリへの `git archive` で取り出して比べる
- メモ: CLAUDE.md の「環境」の行は `.git/config` に書く git の件で、`.claude/` を書き換える git は覆っていない

### 20261116 — design-doc を呼ぶ前に調査を始めた（design-doc）

- 事象: 「設計まで」と頼まれ、大きな作業と分かっていたのに、design-doc を呼ばずに公式ドキュメントの調査から始めた。ユーザーに「steering は不要なのか」と訂正された（分類: 訂正）
- 期待: 設計を頼まれたら、先に design-doc を呼び、その手順（段階の宣言 → 調べる → 書く前に聞く）の中で調べる。該当: CLAUDE.md の「大きな作業」
- メモ: 20261121 の H2 では、軽く調べた後に design-doc を呼び、その手順の中で調べ直した

### 20261116 — 承認の基準がスキルの間でそろっていない（design-doc・design-premortem・steering。スキル評価の L5）

- 事象: プレモータムの後に「推奨で進めて」と言われた。論点への回答と読んで設計を直し、DRAFT のまま止めた。実装の承認とも読めた（分類: 曖昧さ。迷ったまま決めて進めた）
- 期待: 承認の基準をスキルの間でそろえる。steering は「承認を明言するまで」、design-doc は「承認したら」で、基準が違う
- メモ: 20261121 の H2 では「推奨で承認、実装して」と承認が明言され、迷わなかった

### 20261116 — スキル評価（20261115）の残りの所見

- 事象: 評価の所見のうち、タスクにしたのは M1・M2・H1・H2・L1 と M6 だけ。レポートは追跡外（`.tmp/skill-eval-report-20261115.md`）で、このマシンにしか無い。残りをここに控える
  - M3: 発火を採点していない。近いスキルの取り合い（「レビューに出して」は pr-create か frontend-code-review か）を測るケースが無い。条件 C の `d2-vague-request` は発火 3/6
  - M4: design-premortem の本文は評価を通っていない。20261116 に初めて実際の設計で使い、所見 10 件のうち 10 件を採った（1 件は一部を捨てた）
  - M5: design-doc の「1 問ずつ聞く」の 2 問目以降と、中くらいの作業の要約は、1 ターンの評価で測れない
  - M7: steering の「閉じる」は、確認の後の経路（索引の追記・`git rm`）を測っていない
  - M8: e2e は書いた spec を評価でも実行していない
  - L2〜L4: `${CLAUDE_SKILL_DIR}` を使っていない・skill-test に `test:sandbox` が無い・skill-test の写し先がタスクの無いときに決まらない（L5 は上の「承認の基準」の件）
  - 評価の仕組み: モデルが変わったときにベースラインを取り直す手順が無く、結果にモデル名が残らない。採点役と人の一致の記録が 1 件だけ。回帰に使う s1・d5 の grader が `focus=TRACE` のまま（`eval/README.md` は trace を避けると書いている）
  - Fable 5.2 の指針: 停止のケースを今のモデルで流し直す。レビューの agent の `effort: high` を比べ直す
  - TDD: 「新しいテストは、実装の前に落ちることを確かめる」を steering に 1 行足す案
- 期待: 改善を頼まれたときに、ここから拾う

## 対策済み

- 20261114 review-verify の再現が作業ツリーに書き込んだ（frontend-code-review）— make-copy.sh の写しと subagent-tree-guard.sh（verify-tree-guard・PR #33）
- 20261115 SessionStart の hook が .steering の隠しディレクトリをタスクに挙げた — hook が `.` で始まるディレクトリとファイルの無いフォルダを数えない・steering 2.4（PR #36・#37。評価の M6 も同じ件）
- 20261116 sandbox の中の `git branch -m` が rc 128 で終わる — CLAUDE.md の「環境」（`.git/config` に書く git は失敗する）（PR #37）
- 20261117 マージの後の `git checkout -B main origin/main` が sandbox の中で失敗する — CLAUDE.md の「環境」の `checkout -q --no-track -B main origin/main`（PR #37）。20261121 の `branch -d` の後の設定の掃除で 2 回目
- 20261117 閉じた後にタスクのフォルダが空のまま残った（steering）— steering 2.3 の閉じる手順 6・hook がファイルの無いフォルダを出さない（PR #36）。20261120 に 2 回目
- 20261117 PR を作った後、閉じずに止めた（steering）— pr-create の Step 5 と SessionStart の閉じ忘れの印（close-before-merge・PR #35）
- 20261117 課金のある試し実行で `--runs` を落として 3 回流した — 仕組みにしないと判断（1 回だけ）。もう一度起きたら `eval/run.sh` を考える（PR #37）
- 20261120 評価の sandbox の中で jq が abort し「jq が無い」で 2 を返す — run-tests-on-base.sh の `/usr/bin/jq` への切り替えと「無い」「動かない」の区別・t2 の `q3-got-tests-on-base`（run-tests-jq-fallback）
- 20261121 skill-test: グループをまたぐ回帰を同時に流された — prepare.sh が実行中の eval で止まる・skill-test 2.1 の `&&`（PR #36）
- 20261121 steering の閉じる手順 3: DRAFT で入れたタスクを閉じ忘れと取り違える — APPROVED のまま入っているときだけ閉じ忘れと見る（PR #35 の 09e2aad）
- 20261121 空白の無い ask が auto mode で確認を出さない（評価の H2）— ask を空白ありの形にし `test:sandbox` が落とす・`~/.claude/CLAUDE.md` に 1 行（PR #38）
- 20261121 frontend-code-review の費用の停止に、言い回しで通れる例外があった（評価の M2）— 例外を `--cost-ok` の印だけにし、基準以下でも目安を 1 行出す・評価の l2-phrase-not-enough・run_cost_ok.py（feature/review-cost-ok）
- 20261121 時期で古くなる記述が配るスキルの本文にあった（評価の L1）— 費用の目安を frontend-code-review/references/cost.md に移して測った年月も出す・steering の例の日付を <YYYYMMDD> に・validate:portability が年月と金額を拾う（feature/cost-table）。steering の macOS の git のメッセージは手順の本体でないので残した
