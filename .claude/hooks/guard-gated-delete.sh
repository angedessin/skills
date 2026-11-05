#!/bin/bash
# PreToolUse(Bash) guard: 承認制のパスへの素の rm / mv を deny する。
#
# なぜ要るか: permissions の ask（Edit）と guard-gated-write（> / >> / tee）は
# 書き込みだけを塞ぎ、`rm -f docs/x.md` や `mv … docs/` は素通りする。
# 削除・移動はゲート迂回と等価なので deny する（ask ではない）。
#
# 脅威モデル: 敵対者ではなく「停止契約を滑った善意のエージェント」。完全封鎖ではない。
# 守る形: 連鎖（&& || ; | 改行 ( )）・制御構文（then / do など）のすべての部分の rm / mv（/bin/rm も）。
#        先頭の代入・ラッパー（env / exec / sudo 等）は読み飛ばす。コメントとヒアドキュメントの本文は見ない。
#        同じ呼び出しの `cd` は相対パスの解決に使い、サブシェルを出たら戻す。
# 対象パス: プロジェクトの中の CLAUDE.md（どの階層でも）と、ルートの docs/ の下。大文字小文字は区別しない
#          （macOS の既定の FS では `rm CLAUDE.MD` でも実ファイルが消える）。プロジェクトの外のパスは止めない。
#          ただしプロジェクトがリポジトリの一部なら、同じリポジトリの中は止める（`rm ../../CLAUDE.md`）。
#          グロブ・ブレース・変数は、手前が docs/ の下か CLAUDE.md なら止める（`docs/$f`・`*/CLAUDE.md`）。
#          リンクはリンク自体の場所で判定する（rm / mv が操作するのはリンク）。末尾の `/` と、その後のグロブは
#          リンク先も見る（`rm -rf link/` はリンクを残してリンク先の中身を消す。macOS で確認）。
#          開始時の cwd か `cd` の後の場所が同じリポジトリの worktree なら、その worktree のルートも対象にする
#          （worktree に入っても CLAUDE_PROJECT_DIR は開始時の場所のままで、cwd だけが移る）。
#          再帰の rm は、プロジェクトのルートかその親を指す形（`.`・`..`・`../proj`・`*`・`./*`・`*/`・`**`）も止める。
#   `.claude/` の素の rm / mv は sandbox の標準の書き込み禁止が止める（git rm・git restore は excludedCommands で
#   sandbox の外に出て、この hook も沈黙するので、通常の確認だけが残る）。
# 守らない形（沈黙）: `bash -c` / `eval` の中身・`git rm`・手前が分からない変数（`$X/CLAUDE.md`）・`cd -` や変数の
#          `cd` の後の相対パス・グロブが対象の名前の途中にある形（`CLAUD*`）・解析の失敗（閉じていない引用など）・
#          途中のディレクトリを再帰で消す形（`rm -rf sub` の下に CLAUDE.md がある）・
#          本体にいて別の worktree の docs/ をパスで直接指す形（`rm ../wt/docs/a.md`）や、外の worktree の
#          CLAUDE.md をパスで直接指す形・ルートを変数で指す形（`"$PWD"`・`$PWD/*`・`"$(pwd)"`）・
#          長いオプションの省略形（`rm --recur .`）・`mv` でプロジェクト自身を親から指す形（`mv ../proj /tmp/x`）・
#          python3 や guard_gated.py が無いとき（フェイルオープン。deny に倒すと通常の Bash が広く死ぬ）。
#          沈黙することはフィクスチャで固定している（guard_gated.py が無いときを除く）。
# 新しい変種の扱い: 普段の書き方で承認制のパスが実際に消える形は直す。それ以外の変種は判定を増やさず、上の一覧に足す
#          （シェルの解析で全部は防げず、沈黙しても通常の確認は残る）。
#
# 判定は guard_gated.py（guard-gated-write と共通の抽出）。tool_input.command だけを見る。

payload=$(cat)
[ -z "$payload" ] && exit 0

verdict=$(printf '%s' "$payload" | python3 "${0%/*}/guard_gated.py" delete 2>/dev/null)
if [ "$verdict" = "DENY" ]; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"CLAUDE.md / docs/ への rm / mv を検出しました（guard-gated-delete hook）。これらは承認制のパスで、削除・移動は書き込みゲートの迂回になります。消す必要があるなら、理由を示してユーザーに頼みます（追跡済みのファイルは git rm でも消せます）。"}}
EOF
fi

exit 0
