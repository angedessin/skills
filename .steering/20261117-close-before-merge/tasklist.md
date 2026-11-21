# tasklist: close-before-merge

Last updated: 20261120

design.md は 20261120 に APPROVED。課金のある項目（★）は、見積もりを示して承認を取ってから、通常のターミナルで流してもらう。

## 1. hook

- [x] `session-start-check.sh` に、統合ブランチの決め方と閉じ忘れの疑いの印を足す。`tests/hooks/run_fixtures.py` の `check_session_start` に完了条件 1 のケースを足し、git の環境を固定して確かめる（`mise exec -- pnpm run test:hooks`）（20261120。SS4〜SS12 を足した。origin/HEAD が無く main がある場合は SS4 が兼ねる。mise exec -- pnpm run test:hooks 539/539）

## 2. スキルの本文

- [x] `steering/SKILL.md` の閉じるの手順 2・手順 7、再開の手順 4、状況の確認を直し、版を上げる。README の `deps:skills` の steering の行も直す（`validate` が通ることを確かめる。振る舞いは 3 の評価で確かめる）（20261120。「閉じてよい状態」の節を足し、閉じるの手順 3 で gh pr view により push を予告する形にした。版 2.2。mise exec -- pnpm run validate 11/11。振る舞いは未確認で、3 の評価で見る）
- [x] `pr-create/SKILL.md` の Step 1・Step 4・PR を作った後を直し、版を 2.2 にする。README の `deps:skills` の pr-create の行も直す（同上）（20261120。PR を作った後は Step 5 にし、閉じてよい状態の定義を写した（自己完結のため。steering と 2 か所）。mise exec -- pnpm run validate 11/11。振る舞いは 3 の評価で見る）
- [x] `design-doc/SKILL.md` の tasklist の最後の項目を直し、版を上げる。README の `deps:skills` の design-doc の行も直す（`validate` が通ることを確かめる）（20261120。版 2.1。mise exec -- pnpm run validate 11/11）
- [x] README の `deps:hooks` と SessionStart の説明を直し、`validate` が通ることを確かめる（20261120。mise exec -- pnpm run validate 11/11。validate:portability は exit 0、steering の例の日付 20261026 の指摘は main からある）

## 3. 評価

- [x] `eval/gen_pr_cases.py` に `pr4-close-after-pr`（予告の文言を `regex` で見る・`stop-no-push`・`stop-no-pr-create`）と `pr5-design-only`（予告が出ない・同じ停止）を足す。`./prepare.sh c pr` で生成できることを確かめる（20261120。pr4 は PR の前に PR の項目へチェックを付けないことも `regex` で見る。./prepare.sh c pr で生成し、fixture を手元で流して exit 0。一回限り）
- [x] `eval/gen_design_cases.py` に `s4-ready-to-close` を足す（PR の項目にチェックと番号があり、1 項目だけ残るタスク。閉じる確認を出し、何も消さず push しない）。`./prepare.sh c design` で生成できることを確かめる（20261120。残りの項目は単体テストを 1 件足すこと。./prepare.sh c design で生成し、fixture を手元で流して exit 0。一回限り）
- [x] `eval/README.md` の回帰テストの表に 3 ケースを足す（20261120）
- [x] ★ 回帰を流す: pr4・pr5・s4・pr1・pr2・pr3・s3 を各 3 回（目安 3〜5 ドル）。prepare.sh は実行中の plugin を入れ替えるので、グループを並べて流さない。結果の JSON を grader ごとの合否で読み、llm の不合格と怪しい合格は最終回答を読んで確かめる。比べる元は design.md の前提に書いたファイル。結論と、流さなかったケースとその理由を decisions.md に書く（20261121。3 回目で全部有効。pr1〜pr5・s3 は比べる元と同じ合否、pr4・pr5 は 3/3、s4 は採点 1/3・人の判定で 3/3 スキルどおり。費用は 3 回で計 10.4 ドル。decisions.md）

## 4. 仕上げ

- [x] 無料の検査を全部流す（`validate`・`validate:portability`・`test:hooks`・`test:skills`・`test:sandbox`・`lint`）。コマンドと結果を書く（20261121。validate 11/11・validate:portability exit 0（既存の例の日付の指摘だけ）・test:hooks 539/539・test:skills 全部通過・test:sandbox 0 failed・lint 通過）
- [x] frontend-code-review でレビューし、指摘を直す（20261121。18 件のうち 15 件を直し、G・H・T5 と L の一部は理由を付けて残した。review-result.md・decisions.md。test:hooks 545/545・validate 11/11・lint 通過。スキル本文の振る舞いは回帰の流し直しで見る）
- [x] tasklist.md を更新する（20261121）
- [x] pr-create で PR にする（本文に、決めたこと・回帰の結果・残した論点を書く）。PR を作った後に閉じる確認が続けて出て、承認の後に閉じるコミットが PR に載ることを確かめ、PR の本文かコメントに一回限りと書く（完了条件 8）（20261121。PR #35）
- [ ] マージの前に steering で閉じる
