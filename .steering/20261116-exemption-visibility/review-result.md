# review-result: exemption-visibility

## 20261117

範囲: `--base main --worktree`（未コミットを含む）。パスを `.claude/skills/frontend-code-review`・`.claude/skills/pr-create/SKILL.md`・`tests`・`eval`・`package.json`・`README.md` に絞った。11 ファイル・694 行（+684 -10）。

担当: review-bug 2・review-rules・review-test・review-verify。UI のファイルの変更が無いので review-ui-a11y は起動していない。

### 指摘（確かめられたもの）

**Medium**

1. テストが足りない — `tests/skills/run_list_exemptions.py:35-36`（対象は `list-exemptions.sh:133`・`:195` の `-c core.quotepath=false`）
   - タスクのフォルダ名が ASCII だけ。`core.quotepath=false` を外した写しでもテストは 26/26 で通る。
   - 日本語名のタスクでは、閉じたタスクの免除が `exemptions: 0` に黙って落ちる（一時リポジトリで再現。元のスクリプトは 2 件、壊した写しは 0 件）。設計がプレモータムの所見 7 として防ぐと決めた壊れ方。
   - 直し方の方向: 日本語名のタスクで「足して閉じる」を流すケースを足す。
   - 確かめ方: 写しを壊してテストを流し、通った。日本語名のタスクで再現した。

**Low**

2. バグ — `list-exemptions.sh:195`（pr-create 側の写しも同じ行）: `git log --diff-filter=D` に `--no-renames` が無い
   - 1 つのコミットで `.steering/x/` を `git rm -r` し、似た中身の `.steering/y/test-exemptions.md` を足すと、削除が改名（`R067`）と判定される。そのため x の閉じたタスクの免除が出ない。
   - 再現: 本来 4 件のところ 2 件。`--no-renames` を付けた写しでは 4 件。
   - 直し方の方向: `--no-renames` を付けて 2 つの写しを両方直し、このケースをテストに足す。
   - 補足: タスクのフォルダを `git mv` すると、前からある行が載る。これは `--no-renames` を付けても変わらない。`prev_entries` が同じパスでしか前の版を引かないのが原因。改名を閉じたタスクとみなすかは仕様で決める（指摘ではなく論点）。
3. テストが足りない — `run_list_exemptions.py:297-309`（`check_git_fails_midway`）
   - `list-exemptions.sh:174`・`:189` の `|| unknown` を消しても 26/26 で通る。今のテストでは、HEAD に免除ファイルが残る場合も、`--worktree` の場合も通っていない。
   - どう壊れうるか: `git show` が落ちると、行が黙って抜けて `exemptions: 0` になる。
   - 直し方の方向: `setup_branch` の `--base main` と、指定なしで `show` を落とすケースを足す。
   - 確かめ方: 写しを壊して流し、通った。
4. テストが足りない — `list-exemptions.sh:146`
   - 比較を「パス＋理由」に縮めても 26/26 で通る。同じパス・同じ理由のまま節だけ移した行が載るかを、どのテストも見ていない（仕様は「節・パス・理由の組」）。
   - 直し方の方向: 節だけ移すと `exemptions: 1` になるケースを足す。
   - 確かめ方: 写しを壊して流し、通った。
5. テストが足りない — `list-exemptions.sh:100`
   - `check-ignore` が 0・1 以外で終わったときに `unknown` を出す分岐を、`*) ;;` に変えても 26/26 で通る。
   - 直し方の方向: `check_git_fails_midway` の対象に `check-ignore` を足す。
   - 確かめ方: 写しを壊して流し、通った。
6. 規約 — `README.md:71`
   - `test:skills` の説明に、`run_list_exemptions.py` と、`run_eval_graders.py` の免除の採点が入っていない。
   - 確かめ方: コードを読んで確かめた。
7. 規約 — `list-exemptions.sh:181`・`eval/gen_review_cases.py:370`
   - コメントが理由ではなく、仕様（design.md:67-68 と決定済みの項目）の写しになっている。規則は「コメントは理由だけを 1 行」。
   - 確かめ方: コードを読んで確かめた。

### この差分で足したテストの免除

なし（`exemptions: 0`）

### 捨てた指摘

- 2 件。
  - 問題ではない 1 件: 直下の `.steering/test-exemptions.md` を常に見る点。design.md:47 の仕様で、LE7 も意図して確かめている。67 行のコメント「ゲートと同じ」がやや不正確なだけ。
  - 確かめられない 1 件: SKILL.md で「自明なら終わる」の行が免除の数え上げより前にある点。免除ファイルを足した差分は字義上「だけ」に当たらず、モデルの解釈次第。
- `list-exemptions.sh:185` のコメントは、理由として読めるので指摘から外した。

### 規約が無いと報告された観点

- 配るスクリプトのコメントに、マスター固有の名前（`stop-test-gate.sh`・`test:skills`）を書いてよいか。
- 同じスクリプトを 2 つのスキルに置くときの運用。

### レビューできなかったもの

- `run-tests-on-base.sh` は vitest 用で、tests: 0 だった。Python のテストは、変える前のコードで流す確認の対象外。
- `.claude/skills/pr-create/scripts/list-exemptions.sh` はパスの絞り込みの外。写しの一致は LE25 が見ている。
- `.steering/` の差分は対象外にした。
