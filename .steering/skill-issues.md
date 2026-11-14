# スキルの問題の記録

## 20261114 — テストのゲートがモノレポを見ない（skill-loop-fixes の PR 1 のレビュー）

- 事象: `stop-test-gate.sh` は根を git のトップレベルに決め、`$ROOT/node_modules/.bin/vitest` が無ければ素通しする。vitest をサブパッケージにだけ入れたモノレポでは、ゲートが何も言わずに効かない
- 期待: 変えたファイルから一番近い package.json の vitest で判定する（パッケージごとに related を流す）か、効いていないことを知らせる
- 今回の扱い: README に対象外と書いた。根の決め方を変えるのは別の設計が要るので、モノレポの配置先が出たら設計する

## 20261114 — review-verify の再現が作業ツリーに書き込んだ（frontend-code-review）

- 事象: 検証役が F2 を再現するとき、`mktemp -d`（既定の /var/folders/.../T）が sandbox に拒まれ、`cd "$D/r"` も失敗したまま後続のコマンドがリポジトリの根で動いた。`git init`・コミット（e938c3f）・未追跡ファイル 3 つを作った。本人が `git reset --mixed 76bcbe2` とファイルの削除で戻し、メインのセッションで HEAD・status・reflog を確かめた
- 期待: 写しや一時リポジトリでの再現は、作る・移るの失敗で止まる（`set -e` か `&&` でつなぐ、`cd` の後に `pwd` が写しの中かを確かめる）。sandbox の中では `$TMPDIR` を使う。review-verify.md の「作業ツリーを変えない」を、手順で守れる形にする

## 20261115 — SessionStart の hook が .steering の隠しディレクトリをタスクとして挙げた

- 事象: `.steering/.claude/.cc-writes`（空。Bash の作業ディレクトリを .steering にしたまま書いたときに Claude Code が作ったと見られる）があり、SessionStart の hook がアクティブなタスクに `.claude` を挙げた。空なのを確かめて消した
- 期待: hook は `.` で始まるディレクトリ（と archived/）をタスクに数えない。steering スキルの「タスクの見つけ方」も同じ
