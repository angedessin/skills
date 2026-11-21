# スキルの問題の記録

## 20261114 — テストのゲートがモノレポを見ない（skill-loop-fixes の PR 1 のレビュー）

- 事象: `stop-test-gate.sh` は根を git のトップレベルに決め、`$ROOT/node_modules/.bin/vitest` が無ければ素通しする。vitest をサブパッケージにだけ入れたモノレポでは、ゲートが何も言わずに効かない
- 期待: 変えたファイルから一番近い package.json の vitest で判定する（パッケージごとに related を流す）か、効いていないことを知らせる
- 今回の扱い: README に対象外と書いた。根の決め方を変えるのは別の設計が要るので、モノレポの配置先が出たら設計する

## 20261114 — review-verify の再現が作業ツリーに書き込んだ（frontend-code-review）

- 事象: 検証役が F2 を再現するとき、`mktemp -d`（既定の /var/folders/.../T）が sandbox に拒まれ、`cd "$D/r"` も失敗したまま後続のコマンドがリポジトリの根で動いた。`git init`・コミット（e938c3f）・未追跡ファイル 3 つを作った。本人が `git reset --mixed 76bcbe2` とファイルの削除で戻し、メインのセッションで HEAD・status・reflog を確かめた
- 期待: 写しや一時リポジトリでの再現は、作る・移るの失敗で止まる（`set -e` か `&&` でつなぐ、`cd` の後に `pwd` が写しの中かを確かめる）。sandbox の中では `$TMPDIR` を使う。review-verify.md の「作業ツリーを変えない」を、手順で守れる形にする
- 入れた対策（20261120。verify-tree-guard）: 写しは `make-copy.sh` が `$TMPDIR` に作り、検証役は毎回 `cd <写し> &&` で動く。`subagent-tree-guard.sh` が SubagentStart・SubagentStop で作業ツリーを比べ、違えば 1 回差し戻して親に知らせる（評価の t2 の `stop-tree-checked` で確かめる）

## 20261115 — SessionStart の hook が .steering の隠しディレクトリをタスクとして挙げた

- 事象: `.steering/.claude/.cc-writes`（空。Bash の作業ディレクトリを .steering にしたまま書いたときに Claude Code が作ったと見られる）があり、SessionStart の hook がアクティブなタスクに `.claude` を挙げた。空なのを確かめて消した
- 期待: hook は `.` で始まるディレクトリ（と archived/）をタスクに数えない。steering スキルの「タスクの見つけ方」も同じ

## 20261115 — 未了: テストのゲートの所要時間を配置先で測る（skill-loop-fixes の tasklist 10b）

- 事象: stop-test-gate.sh は実装ファイルごとに vitest を起動し、打ち切りは 150 秒（settings の timeout 180）。このリポジトリには vitest が無く、実際のプロジェクトでの時間を測っていない（PR 1 のレビューで「設計どおり」とした性能の件）
- 期待: 配置先の最初のプロジェクトで所要時間を測り、打ち切り時間と、実装ファイルごとに起動する作りを見直す

## 20261116 — design-doc を呼ぶ前に調査を始めた（design-doc）

- 事象: 「設計まで」と頼まれ、大きな作業と分かっていたのに、design-doc を呼ばずに公式ドキュメントの調査から始めた。ユーザーに「steering は不要なのか」と訂正された（分類: 訂正）
- 期待: 設計を頼まれたら、先に design-doc を呼び、その手順（段階の宣言 → 調べる → 書く前に聞く）の中で調べる。該当: CLAUDE.md の「大きな作業」

## 20261116 — 「推奨で進めて」が、論点への回答か実装の承認か決まらなかった（design-doc・design-premortem）

- 事象: プレモータムの後に「推奨で進めて」と言われた。論点への回答と読んで設計を直し、DRAFT のまま止めた。実装の承認とも読めた（分類: 曖昧さ。迷ったまま決めて進めた）
- 期待: 承認の基準をスキルの間でそろえる。steering は「承認を明言するまで」、design-doc は「承認したら」で、基準が違う（スキル評価の L5）

## 20261116 — sandbox の中の `git branch -m` が rc 128 で終わる（改名は通る）

- 事象: ブランチの改名で `error: could not lock config file .git/config` が出て rc 128。ref の改名は済んでおり、上流の設定の無いブランチでは実害が無かった。失敗と読み違えやすい
- 期待: 改名の後に `git branch --show-current` で確かめる。上流の設定のあるブランチでは設定が古い名前のまま残るはずで、そのときは通常のターミナルで流す（未確認）

## 20261116 — 未着手: スキル評価（20261115）の残りの所見

- 事象: 評価の所見のうち、タスクにしたのは M1（`20261116-exemption-visibility`）と H1（`20261116-verify-tree-guard`）だけ。レポートは追跡外（`.tmp/skill-eval-report-20261115.md`）で、このマシンにしか無い。残りをここに控える
  - H2: `gh pr create` が permissions の ask に無い。push 済みのブランチから PR だけ作る経路は、スキル本文だけが歯止め（設計は未着手。中くらいの作業の見込み）
  - M2: frontend-code-review の費用の停止に、解釈で通れる例外がある（「大きいけど全部見て」）。1,000 行以下は見積もりなしで最大 3 ドル
  - M3: 発火を採点していない。近いスキルの取り合い（「レビューに出して」は pr-create か frontend-code-review か）を測るケースが無い。条件 C の `d2-vague-request` は発火 3/6
  - M4: design-premortem の本文は評価を通っていない。20261116 に初めて実際の設計で使い、所見 10 件のうち 10 件を採った（1 件は一部を捨てた）
  - M5: design-doc の「1 問ずつ聞く」の 2 問目以降と、中くらいの作業の要約は、1 ターンの評価で測れない
  - M7: steering の「閉じる」は、確認の後の経路（索引の追記・`git rm`）を測っていない
  - M8: e2e は書いた spec を評価でも実行していない
  - L1〜L5: 時期で古くなる記述（frontend-code-review の費用の表など）・`${CLAUDE_SKILL_DIR}` を使っていない・skill-test に `test:sandbox` が無い・skill-test の写し先がタスクの無いときに決まらない・承認の基準の揺れ
  - 評価の仕組み: モデルが変わったときにベースラインを取り直す手順が無く、結果にモデル名が残らない。採点役と人の一致の記録が 1 件だけ。回帰に使う s1・d5 の grader が `focus=TRACE` のまま（`eval/README.md` は trace を避けると書いている）
  - Fable 5.2 の指針: 停止のケースを今のモデルで流し直す。レビューの agent の `effort: high` を比べ直す
  - TDD: 「新しいテストは、実装の前に落ちることを確かめる」を steering に 1 行足す案
- 期待: 改善を頼まれたときに、ここから拾う。M6（SessionStart の hook が `.` で始まるディレクトリをタスクに数える）は、上の 20261115 の記録と同じ

## 20261117 — 閉じた後に、タスクのフォルダが空のまま残った（steering）

- 事象: `git rm -r` の後も `.steering/20261116-exemption-visibility/.claude/.cc-writes`（空）が残り、フォルダが消えなかった。作業ディレクトリがタスクのフォルダにあった間に、Claude Code が作ったとみられる。残ると SessionStart の hook がアクティブなタスクとして数える
- 期待: 閉じる手順の最後に、フォルダが消えたことを `ls .steering/` で確かめ、追跡外の空のディレクトリだけなら消す

## 20261117 — PR を作った後、閉じずに止めて「なんで閉じてないの？」と聞かれた（steering）

- 事象: tasklist の最後の項目「マージの前に steering で閉じる」を、「PR のレビューが済んでから」という自分の判断で保留した。ユーザーに理由を聞かれた（分類: 訂正に近い）
- 期待: CLAUDE.md の「マージ前に閉じる」に、レビューを待つ根拠は無い。PR を作った流れで、閉じる確認まで続けて出す

## 20261117 — マージの後の `git checkout -B main origin/main` が sandbox の中で失敗する

- 事象: `error: could not lock config file .git/config` で失敗し、ブランチは切り替わらなかった。上流の設定（`.git/config`）が書けないため。`git checkout main` の後に `git merge --ff-only origin/main` を流せば、config に書かずに済んだ
- 期待: マージ後に main へ戻す手順を、sandbox の中で通る形（`checkout main` と `merge --ff-only`）にそろえる。記憶の「GitHub flow 運用」も同じ手順を書いている

## 20261117 — 課金のある試し実行で、回数の指定を落として 3 回流した（verify-tree-guard）

- 事象: 「1 回 0.7〜0.9 ドル」と見積もって渡した `claude plugin eval` のコマンドに `--runs 1` が無く、既定の 3 回で流れて 2.11 ドルかかった（見積もりの約 2.5 倍）。skill-test の手順は `--runs <表の回数>` を書いているが、skill-test を通さずにコマンドを自分で組んだ
- 期待: 課金のコマンドを渡す前に、見積もりの回数と `--runs` が一致しているかを確かめる。skill-test 以外で評価を流すときも、skill-test の雛形のコマンドから組む

## 20261118 — 検査の前後を比べるのに git stash を使い、sandbox で途中まで失敗した（verify-tree-guard）

- 事象: `validate:portability` の前後を比べるため `git stash` を流したところ、sandbox が `.claude/` の下を書かせず `unable to unlink old ...` で途中まで失敗した。stash の項目だけが残り、作業ツリーは変わらなかった（stash と差分 0 を確かめた）
- 期待: sandbox の中では、作業ツリーを動かす git（stash・checkout・reset）で前後を比べない。前の版は `git show HEAD:<パス>` か `git worktree` でなく一時ディレクトリへの `git archive` で取り出して比べる

## 20261119 — make-copy.sh は TMPDIR が無いと必ず失敗する（verify-tree-guard のレビューの指摘 7）

- 事象: sandbox を使わない配置先（Linux など）では TMPDIR が無いことが多く、検証役も親も再現できずに読みで判定する。設計どおり（sandbox の中で /tmp に落とすと拒まれ、cd の失敗の元になる）
- 期待: 雛形は sandbox を必須にしているので、今は直さない。sandbox を使わない配置先が出たら、TMPDIR が無いときだけ /tmp に落とすかを決める

## 20261120 — 評価の sandbox の中で jq が abort し、run-tests-on-base.sh が「jq が無い」で 2 を返す（verify-tree-guard の回帰で気づいた）

- 事象: Claude Code 2.1.328・2.1.329 の t2 で、モデルの Bash から呼んだ `run-tests-on-base.sh` の `jq --version` が `Abort trap: 6` で落ち、「jq が無い」で 2 を返した（2.1.326 では通っていた）。普段のセッションの sandbox では `/usr/bin/jq`（1.7.1-apple）も anaconda の jq（1.6）も動く。hook（sandbox の外）の jq も評価の中で動いた。`q2-ran-tests-on-base` は呼んだかだけを見るので合格し、変える前のコードで流した結果が報告に使われたかは評価で見えていない
- 期待: (1) 評価の中でどの jq が選ばれ、なぜ abort するかを調べる（無料。trace の PATH・`which -a jq`）(2) q2 を「呼んだ」でなく「結果（`passed-on-base:`）を得た」で見るかを決める (3) 「jq が無い」と「jq が動かない」を分けて知らせる。どれも verify-tree-guard の範囲の外
- 調べた結果（20261120。(1) の答え）: 評価の sandbox は anaconda の `bin/` だけを allowRead に入れ、`/Users` を denyRead にしている。PATH で先に当たる anaconda の jq（1.6）は `@rpath/libonig.5.dylib`（`anaconda3/lib/`）を読み込むので、dyld が読めずに SIGABRT（rc=134 = Abort trap: 6）で落ちる。ライブラリの無い場所へ写した anaconda の jq で同じ rc=134 と `Library not loaded: @rpath/libonig.5.dylib` を再現した。`/usr/bin/jq`（1.7.1-apple）は libSystem だけに依存する。2.1.326 で通った理由は、その回の sandbox の設定が残っておらず確かめられない
- 入れた対策（20261120。feature/run-tests-jq-fallback）: (2)(3) を入れた。`run-tests-on-base.sh` は PATH の jq が起動できなければ `/usr/bin/jq` を試し、`JQ=<パス>` も受け、「jq が無い」と「jq が動かない（exit と stderr の 1 行）」を分ける（frontend-code-review 2.4）。t2 に `q3-got-tests-on-base`（trace の regex で判定の出力を見る）を足した

## 20261120 — steering の「閉じる」の後に、タスクのフォルダが空のディレクトリだけで残った

- 事象: `git rm -r .steering/20261116-verify-tree-guard/` の後に、追跡していない空のディレクトリ `.claude/.cc-writes` が残り、フォルダが消えなかった（Edit ツールが書くときに作ったものと思われる）。手順 2 の `git status --short` は空のディレクトリを出さないので、確認では見えなかった。`rmdir` で消した
- 期待: 閉じるの手順 6 の後に、フォルダが残っていないかを確かめる。空のディレクトリだけなら消し、ファイルが残っていれば止まって知らせる

## 20261121 — skill-test: グループをまたぐ回帰のコマンドを 2 つのブロックで示し、同時に流された

- 事象: close-before-merge の回帰で、pr と design のコマンドを別々のブロックで示した（「pr が終わってから」と注記）。2 回続けて別のターミナルで同時に流され、`prepare.sh c design` が pr の実行中に plugin を入れ替え、pr の 14 回が無効になった（計 7.5 ドルのうち約 6 ドル分）
- 期待: skill-test の Step 3 で、複数のグループを流すときは 1 つのコマンドに `&&` でつないで示す（注記だけでは止まらない）。または prepare.sh が実行中の eval を検知して止まる

## 20261121 — steering の閉じる手順 3: 設計だけを DRAFT で統合ブランチに入れたタスクを「閉じ忘れ」と取り違える

- 事象: close-before-merge を PR #35 の後に閉じようとした。タスクのフォルダは PR #32（設計だけ・DRAFT）で main に入っているため、手順 3 の「統合ブランチの tree にある → 今のブランチの PR とは関係が無い。番号を取らず push も予告しない」に当たり、PR #35 に閉じるコミットを載せられない形になった
- 期待: hook と同じく、統合ブランチの tree に APPROVED のまま入っているときだけ閉じ忘れと見る（DRAFT で入っているのは設計だけの PR で、続きの PR が今のブランチにある）
