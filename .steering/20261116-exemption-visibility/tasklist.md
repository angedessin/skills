# tasklist: exemption-visibility

Last updated: 20261116

design.md が APPROVED になるまで着手しない。課金のある項目（★）は、見積もりを示して承認を取ってから、通常のターミナルで流してもらう。

## 1. スクリプト

- [ ] `frontend-code-review/scripts/list-exemptions.sh` を書き、`tests/skills/run_list_exemptions.py` で、指定なしの範囲を確かめる（足した行・0 件・日付の無い行・理由の無い行と節の外の行は出ない・理由だけ変えた行は出る・消しただけの行は出ない・未追跡の免除ファイル）
- [ ] `--base` と `--worktree` を足し、テストで確かめる（分岐点との比較・閉じたタスクの免除が印つきで出る・ファイルは残って行だけ消したものは出ない）
- [ ] 分からないときと失敗のときを足し、テストで確かめる（gitignore で無視されているときは `unknown` で 0・引数の誤りとリポジトリの外は 2・`GIT=` を使う）
- [ ] 同じファイルを `pr-create/scripts/` に置き、テストに「2 つの写しがバイト単位で一致する」を足す。`package.json` の `test:skills` に `run_list_exemptions.py` を足し、`mise exec -- pnpm run test:skills` が通ることを確かめる

## 2. スキルの本文

- [ ] `frontend-code-review/SKILL.md` の Step 1 と Step 4 を直し、版を 2.2 にする（`validate` が通ることを確かめる。振る舞いは 3 の評価で確かめる）
- [ ] `pr-create/SKILL.md` の Step 3 と Step 4 を直し、版を 2.1 にする（同上）
- [ ] README の「スキルのフォルダのスクリプト」とテストのゲートの免除の説明を直し、`validate` が通ることを確かめる

## 3. 評価

- [ ] `eval/gen_review_cases.py` に `x1-exemption-added` を足す（差分に免除の追加を含むフィクスチャ。`regex` で最終回答に免除したパスと理由が出ることを見る）。`./prepare.sh c review` で生成でき、`test:skills` の `run_eval_graders.py` が通ることを確かめる
- [ ] `eval/gen_pr_cases.py` に `pr3-exemption` を足す（分岐点との間のコミットに免除の追加を含む。示した本文に免除したパスが出る・`stop-no-push`・`stop-no-pr-create`）。`./prepare.sh c pr` で生成できることを確かめる
- [ ] `eval/README.md` の回帰テストの表に 2 ケースを足す
- [ ] ★ 回帰を流す: x1・pr3・l1・pr1・pr2 を各 3 回（目安 4〜5 ドル）。結果の JSON を grader ごとの合否で読み、llm の不合格と怪しい合格は最終回答を読んで確かめる。最終回答をこのフォルダに写し、結論と、流さなかったケース（n1・p2・r-c・t1・t2）と理由を decisions.md に書く

## 4. 仕上げ

- [ ] 無料の検査を全部流す（`validate`・`validate:portability`・`test:hooks`・`test:skills`・`test:sandbox`・`lint`）。コマンドと結果を書く
- [ ] frontend-code-review でレビューし、指摘を直す
- [ ] tasklist.md を更新する
- [ ] pr-create で PR にする（本文に、決めたこと・回帰の結果・残した論点を書く）
- [ ] マージの前に steering で閉じる（`20261116-verify-tree-guard` は閉じない。main に残して次に進める）
