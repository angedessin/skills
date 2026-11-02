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
