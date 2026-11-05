# レビュー結果

## 20261102 — 区切り 2 の PR の前のレビュー（ブランチの差分）

**対象**: `origin/feature/skillset-renewal...HEAD` を `.claude`・`scripts`・`CLAUDE.md`・`README.md`・`docs`・`templates`・`eval/README.md`・`eval/prepare.sh`・`eval/evalcase.py` に絞り、削除だけのファイルを除く（23 ファイル・3,031 行・約 24 万バイト）。`eval/gen_*_cases.py` と評価の生成物は対象外（ユーザー承認）
**結果**: 一次の指摘を重複をまとめて 14 件。確かめられた 13 件（High 1・Medium 4・Low 8）、捨てた 1 件。修正は未着手

### High

1. 未追跡の新規ファイルへの指摘が検証で捨てられる。`.claude/skills/frontend-code-review/SKILL.md:26,41,45,47`・`.claude/agents/review-verify.md:13,25`。未追跡のパスは Step 2 にしか渡さず、patch にも入らないので、新規の `src/useFoo.ts` のバグは「変更前の問題」として捨てられ、指摘なしと報告されうる。直し方: Step 3 にも未追跡のパスを渡し、review-verify はそれを新規として扱う。読んで確かめた

### Medium

2. コミット済みの作業ブランチで「コードをレビューして」と頼むと変更なしで終わる。`frontend-code-review/SKILL.md:23-25,52-57`・`docs/user-guide.md:31`。3 コミット＋未コミット 1 行なら 1 行だけを見て、範囲が狭いことも伝わらない。直し方: ベースより進んでいれば範囲を聞き、報告に対象の範囲を書く。読んで確かめた
5. agent の起動失敗・失敗時の手順が無い。`frontend-code-review/SKILL.md:31,45,47,57`。review-verify だけが失敗すると、字義どおりなら残る指摘が 0 件になる。直し方: 代替の手順を書き、検証できなかったことを報告させる（`design-premortem/SKILL.md:31` に例がある）。読んで確かめた
6. 停止の grader が引用符つきの書き込みなどを見逃す。`eval/evalcase.py:53,60`・`eval/evals/design/d1-category-filter/graders/stop-no-src-bash.md:4`。`cat > "src/App.tsx"`・`tee "src/a.ts"`・`echo x > "$PWD/src/a.ts"`・`sed -E -i ...`・`sed --in-place ...` が一致しない。Edit・Write は別の grader が見ているので、すり抜けるのは Bash のこの形だけ。直し方: 正規表現を広げ、grader を生成し直す。再現した（正規表現を入力に当てた）
10. steering の再開がタスクのフォルダを全部読む。`.claude/skills/steering/SKILL.md:30`・`.claude/skills/skill-test/SKILL.md:56`・`eval/README.md:53`。このタスクは 63 ファイル・約 553KB（推定約 21 万トークン）で、評価の回答の写しも読む。直し方: 読むファイルを指定に戻し、回答の写しは読まない。読んで確かめた（大きさは計測）

### Low

3. 大きな patch を読み切れなくても報告の欄が無い。`.claude/agents/review-bug.md:14` と review-rules・review-test・review-ui-a11y の同じ行・`frontend-code-review/SKILL.md:57`。Read は今回の patch を 702 行で切ったが、切れたことと続きの offset を明示する。読み切らないのは、agent がそれを無視したときだけ。直し方: 分割読みと読んだ範囲の報告を agent の本文に足す。再現した
4. `--case` の説明が複数ケースの実行を明記しない。`.claude/skills/skill-test/SKILL.md:45,49`・`eval/README.md:39,43-48`。並べると最後の 1 件だけが回る（`decisions.md:515`）。直し方: 1 ケース 1 コマンドと書く。読んで確かめた（課金があるので未実行）
7. pr-create に対象タスクを特定できないときの動きが無い。`.claude/skills/pr-create/SKILL.md:20,40`。ブランチ名が合わないと SPIKE の成果が PR 案に載りうる。push の前の承認は残る。直し方: 特定できないときと Status の欠落・不正で止まる。読んで確かめた
8. APPROVED の設計に premortem をかけて直すと承認が残る。`.claude/skills/design-premortem/SKILL.md:27,51,68`・`.claude/skills/steering/SKILL.md:44`。直し方: 直すなら DRAFT に戻すかを聞く。読んで確かめた
9. validate が CLAUDE.md の不在を PASS にする。`scripts/validate_skills.py:330-337`。直し方: 不在を FAIL にする。読んで確かめた
11. 記録へのパスがアーカイブの後に切れる。`README.md:11`・`eval/README.md:3`（ほかに `eval-pilot/README.md:3`・`eval/gen_impl_cases.py:2`・`eval/gen_review_cases.py:2`）。直し方: アーカイブのときに直す項目を tasklist に足す。読んで確かめた
13. review-rules の「規約が無い」をユーザーに届ける手順が無い。`.claude/agents/review-rules.md:27`・`frontend-code-review/SKILL.md:45,52-59`・`design.md:261`。直し方: Step 4 の報告の項目に足す。読んで確かめた
14. design-premortem の回帰ケースの扱いが design.md と食い違う。`eval/README.md:50`・`design.md:71,175`。除外は `decisions.md:775` に決定があるので、design.md の更新漏れ。`decisions.md:388` の P1・P2 も表に載っていない。直し方: design.md に例外を書く。読んで確かめた

### 捨てた指摘（1 件）

- `eval/evalcase.py:87` の `heredoc()` が改行なしの内容で終端しない: 全 fixture.sh の 63 個で該当なし。起こる入力が無い

### 規約が無い（review-rules の報告）

- React・TypeScript の規約が `docs/knowledge/` に無い
- agent 定義の本文の書き方の型が無く、validate も agent を見ない
- eval のスクリプトのコメントの鮮度の規則が無い（`evalcase.py` の docstring と `eval/README.md` の記述のずれの疑い）

### レビューできなかったもの

- 読めなかった範囲は無い（一次の 3 体とも patch を全部読んだと報告）。依頼文で分割読みと範囲の報告を手で補った
- 未確認: `claude plugin eval` の実際の動き（指摘 4）。実際の grader の正規表現エンジン（指摘 6）

## 20261103 — 6〜8 章のレビュー（ブランチの差分）

**対象**: `origin/feature/skillset-renewal...HEAD`。`.steering/`・`templates/settings.template.json` を除く 15 ファイル（+779・-179）。未コミットの `tasklist.md` は対象外
**結果**: 一次の指摘を重複をまとめて 20 件。確かめられた 16 件（Medium 2・Low 14）、捨てた 3 件、確かめられない 1 件。修正は未着手

### Medium

1. sandbox の auto-allow で、hook が沈黙する Bash の書き込みが確認なしで通る。`.claude/settings.json:62-88`・雛形。`cp /tmp/x CLAUDE.md`・`sed -i '' ... CLAUDE.md`・`python3 -c "open('docs/x.md','w')"`。変更前は通常の確認に落ちていた。design.md にも decisions.md にも決定が無く、CLAUDE.md の承認制と食い違う。`rm docs/...` だけは decisions.md の決定どおり。方向: `sandbox.autoAllowBashIfSandboxed: false` か、受け入れて決定に残すか。確かめ方: hook を直接実行して沈黙を確認（cp・sed・python）。確認が出ないことは実セッションで見ていない
6. `./**/.env*` の denyRead が Bash から動かす開発ツールにも効く。Node の `statSync`・`readFileSync` は EPERM。追跡済みの `.env.example` などで `git status`・`git add` は stderr にエラーを出して rc=0、未追跡の `git add -f` は rc=128。Vite の値が黙って undefined になる点は記憶からの推論で未実行。方向: README のコピー後の確認に注意を足し、`.env` のあるアプリで確かめる。確かめ方: 一部再現

### Low

4. `guard-gated-delete.sh:19` の「.claude/ の削除・移動は sandbox が止める」が言い過ぎ。`git rm`・`git restore` は sandbox の外に出て hook も沈黙する。方向: 「素の rm / mv は」と書く。再現（git restore の hook 実行）と読み
5. 雛形の `failIfUnavailable: false` で sandbox が使えない環境では OS の層と旧 hook の ask が無くなる。README:83 と README:154 が結び付いていない。方向: README に一言。読み
7. `check_settings.py:55-56,127-134` の `check_hooks` が名前の有無だけを見る。matcher を変えても緑。self-test は `hooks={}` だけで REMOVED_HOOKS の分岐を通らない。読み
8. `check_settings.py:103` の `check_excluded` が片方向で、`"python3 *"` を足しても緑。方向: 完全一致。読み
9. `probe.py:60,65,70,121` の「読めない」検査に対照が無く、空の仮ファイルが残っていると denyRead を外しても緑。読み
10. `probe.py:40-43,133-136` は `.claude/` の既存ファイルの append だけで、新規作成・rm・mv を見ない。読み
11. `validate_skills.py` の self-test が枝を確かめていない。:254・:252-253・:255・:243-244・:234-236 を消しても緑。:251 と :252 は互いを覆う。`sorted(...)[0]` の決め打ちで、先頭のスキルが先頭の agent を使うと誤って落ちる。コピーで再現
12. `guard-gated-write.sh:144` の縮退の `docs/` がフィクスチャで固定されていない（`run_fixtures.py:179-198`）。読み
13. README:102 の `cp` の hook の一覧が表と突き合わされない。今は 5 本で一致。読み
14. `validate_skills.py` の `mentions` は `review-bugに渡す` を言及と数えず、`references/` も読まない。今は該当 0 件。再現
15. `probe.py:146` の `git write-tree` は object の書き込みを確かめられない。一時リポジトリで再現
17. `probe.py:76-78,155` は `~/.ssh`・`~/.aws` が無いと検証せず PASS と出る。読み
18. `run_fixtures.py:178` のコメント「元の 3 系統」が古い。読み
19. README:50・56・70 の説明が古い（sandbox・依存の一覧が無い）。読み

### 捨てた指摘（3 件）と確かめられない指摘（1 件）

- 2（denyRead に `*.pem` などが無い）: 公式で permission rules のパスは sandbox の設定に統合される。このセッションの実効の設定にも入っている。実行では試していない
- 3（excludedCommands の広い一致）: 事実だが、design.md・decisions.md の決定どおりで、通常の確認に乗る。脅威モデルの外
- 16（届く側が npm だけ）: 設計の確認項目に要求が無く、一覧は検査で固定している
- 20（引数なしの `git stash`・`git pull` が excludedCommands に一致するか）: 文法が手元の docs に無く、試すと作業ツリーを変えるか通信する。確かめられない

**規約が無い**: 検査スクリプトの docstring やコメントに日付付きの事実を書くときの置き場所と書式
**レビューできなかったもの**: `.env` のあるアプリでの実行、sandbox の使えない環境での実行、`rm` を含む hook の直接実行（安全確認で拒否。フィクスチャと読みで判定）。検証役の一時ディレクトリ `/tmp/claude-501/verify-*` は `rm -rf` の deny で残っている

### 修正（20261104。ユーザーが推奨を承認）

- 直した: 1・4・5・6・8・9・10・15・18・19
- 見送った: 7・11・12・13・14・17（今の実害が無く、検査の検査が中心）

## 20261104 — delete hook の作り直しの再レビュー（`c24ea67..13ee467`）

**対象**: `.claude/hooks`・`tests/hooks` の 4 ファイル
**結果**: 一次の指摘を重複をまとめて 14 件。確かめられた 13 件（High 1・Medium 6・Low 6）、確かめられない 1 件。修正は未着手
**検証の方法**: 検証役はユーザーが停止したので、本体がスクリプトで確かめた（payload を hook に渡す・壊したコピーでフィクスチャを流す）。第三者の検証ではない。「後退」は c24ea67 の hook と比べた結果

### High

1. 後退。`guard_gated.py:49` 改行を ` ; ` にしてから shlex に渡すので、コメントより後ろが消える。`# 古いファイルを消す\nrm CLAUDE.md`・`ls # 確認\nrm -f docs/knowledge/x.md` が silence（旧は deny）。`$#`・`#a` の形と write 側は旧から silence。再現

### Medium

4. 後退。グロブより後ろを捨てるので `rm -f */CLAUDE.md`・`rm -f packages/*/CLAUDE.md`・`rm {a,b}/CLAUDE.md` が silence（旧は deny）。再現
5. 後退。`$` を含む語を通すので `rm docs/knowledge/$name.md` が silence（旧は deny）。`rm $X/CLAUDE.md` も旧は deny。再現
6. 後退。`realpath` が最後の要素のリンクを解決する。`CLAUDE.md -> AGENTS.md` の `rm CLAUDE.md` が silence（旧は deny）。`node_modules/@acme/docs -> ../../docs`・`AGENTS.md -> CLAUDE.md` のリンクを消す `rm` が誤って deny。再現
8. 後退。サブシェルの `cd` が外まで残り、`(cd docs && pnpm build) && rm -f out.txt`・`X=$(cd docs && pwd)\nrm out.txt` が誤って deny。再現
9. deny の文言「git rm か人の操作」が未追跡のファイルに当てはまらない（`git rm` が rc=128）。再現
10. `run_fixtures.py` が `CLAUDE_PROJECT_DIR` を継承する。別のプロジェクトを指すと 84/116、親を指すと 91/116。root を start にする・start を getcwd にする変更でも 116/116 のまま。再現

### Low

2. `);`・`)&&`・`&&(` が区切りにならず silence。旧も silence で後退ではないが、冒頭コメントの「連鎖のすべての部分」とずれる。再現
3. `then`・`do` の直後の rm が silence。`if cd /tmp/x; then\n  rm CLAUDE.md\nfi` は誤って deny。旧も同じ。再現
7. `cd -` の分岐は `operands` が `-` を落とすので届かない。読みで確認。root がホームのときの deny は再現しなかった（理由は未確認）
11. `rm -rf docs` などは deny で動いているが、`rel == "docs"` を消しても 116/116。再現
12. `--` の分岐を消しても 116/116。`cd` の変数の判定を消しても 116/116。`rm CLAUDE.md "`（解析の失敗）は silence で旧は deny、ケースが無い。B22・B41 は判定を固定していない。再現と読み
13. `run_fixtures.py:68` の B42・B43 が delete hook の冒頭コメントの一覧に無い。確認

### 確かめられない（1 件）

- 14: worktree のセッションで `CLAUDE_PROJECT_DIR` がどこを指すか

**規約が無い**: `cd` の解決をどこまで見るかの基準。フィクスチャの ID の付け方

### 修正（20261104。ユーザーが推奨を承認）

- 直した: 1〜13。12 の解析の失敗（`rm CLAUDE.md "`）はシェルでも構文エラーになる形なので、守らない形としてフィクスチャで固定した。`$X/CLAUDE.md` も行き先が分からないので守らない形に残した（旧は deny）
- 課金の再レビューは省いた

## 20261105 — PR #21 全体のレビュー（`22da4db...d800a1e`、`.steering/` と削除を除く 48 件）

32 件を検証し、確かめられた 28 件（High 0・Medium 7・Low 21）、問題ではない 4 件（18・21・23・32）。番号は検証時のもの。

### Medium

- 1 `guard_gated.py:313,349`: ルートの `rm *.md`・`rm -f *`・`mv *.md archive/`・`mv * /tmp/x`・`rm -rf */*` が沈黙する。守らない形の一覧に無い。B56 が `rm -f *` の沈黙を固定している（再現した）
- 2 `guard-gated-write.sh:23-24`・`README.md:83`: 「cp・sed -i は通常の確認に落ちる」が acceptEdits では公式文書の記述と合わない（文書で確認。実機は未測定）
- 10 `guard_gated.py:228-229,254-268`: プロジェクトが `docs/` の下にあると素の rm・mv がすべて deny（再現した）
- 15 `eval/evalcase.py:60`: `\b` が `.claude/` に効かず `rm .claude/...` が合格し、`rm-mv-policy` で誤検知する（再現した）
- 25 `guard_gated.py:17-24`: SEPS・REDIRS・WRAPPERS・CONTROL_WORDS を削っても 226/226 のまま（再現した）
- 27 `check_settings.py:135-142`: guard を PostToolUse へ移しても check_settings・validate ともに緑（再現した）
- 29 `probe.py:176-182`: `.claude/` の rm・mv を sandbox に任せているのに unlink・rename を確かめない（コードを読んだ。実測は未）

### Low

- 3 先頭がブレースの形が沈黙（`guard_gated.py:313`）
- 4 pushd を追わない（`guard_gated.py:336`）
- 5 `xargs -I {}`・`timeout -s KILL 5`・`mv --target-directory=` が沈黙（`guard_gated.py:143,156`）
- 6 ヒアドキュメントの終端の誤認と複数の `<<`。解析失敗で後ろの実際の `rm CLAUDE.md` も沈黙（`guard_gated.py:42,47`）
- 7 ルートの大文字小文字の違いで沈黙（`guard_gated.py:213,290`）
- 8 `grep ">" docs/guide.md` が ASK（`guard_gated.py:114`）
- 9 `find -delete`・`unlink`・`rmdir` が一覧にもフィクスチャにも無い（`guard-gated-delete.sh:30`）
- 11 `.claude/worktrees/` への書き込みが絶対パスや本体からだと ASK（`guard-gated-write.sh:4`）。`$PWD` の形は再現しない
- 12 `templates/README.md:10-11` の mkdir・cp が sandbox の中で失敗する（コードを読んだ）
- 13 `README.md:164` に `.claude/` の守りへの影響が書かれていない
- 14 プロジェクト外の `.env` が sandbox で読める（`settings.json:86`。再現した。通常の確認の有無は未確認）
- 16 `prompts/adversarial-skill-review.md:10` に削除した「ツール語彙の出現数」が残る
- 17 `CLAUDE.md:34` の承認制の一覧が `.claude/` 全体より狭い
- 19 `docs/user-guide.md` の `../README.md` が配置先で別物を指す
- 20 `README.md:11`・`docs/user-guide.md:9,35`・`templates/SKILL.template.md:16` の「同点は削除」が decisions.md:346,376,383,955 と食い違う
- 22 review-test・review-ui-a11y・review-rules の「指摘しないもの」が design.md:275 の 4 項目に足りない
- 24 `README.md:119,166` の確認の記述に「一回限り」の明記が無い
- 26 session-start-check.sh・validate-skill-edit.sh に挙動のテストが無い
- 28 deny・ask の Edit 以外を両方から消しても `check_settings.py` が緑
- 30 `except Exception` を SILENT に変えても 226/226（`guard_gated.py`・`run_fixtures.py`）
- 31 probe の `~/.ssh` 不在と curl の失敗が PASS 扱い（`probe.py:103-111,136-142`）

### 問題ではないとした指摘（4 件）

- 18 README.md:129 に「案内先のスキルは無くても動く」と明記
- 21 decisions.md:786,792 はユーザー承認の決定の下にある。design.md を直していないだけで実害なし
- 23 行動の指示で、経緯の記録ではない
- 32 無言の fail-open は再現したが delete.sh:29-30 と README に明記

### レビューできなかったもの

- acceptEdits の実機の挙動（2・1 の影響）と sandbox の中の実際の rm・mv（29）
- `gen_design_cases.py`・`gen_impl_cases.py`・`gen_knowledge_cases.py` のケースのデータは通読していない
- 削除 122 件と `.steering/` の差分は対象外
