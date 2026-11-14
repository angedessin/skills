Last updated: 2026-11-14

# tasklist: skill-loop-fixes

統合用ブランチ: `feature/skill-loop-fixes`。各項目は、確かめるテストを同じ項目の中で書く（A4 の規則を自分にも当てる）。

## PR 1 — テストの必須化（ブランチ `feature/test-gate`）

- [x] 1. `vitest related` で、関係するテストが 0 件のとき・あるとき・落ちたときの終了コードと出力を、一時的なプロジェクトで確かめる。結果を decisions.md に残す（判定できなければ、判定する範囲を未コミットだけに戻す）（20261111。判定できる。終了コードは 0 件でも 0 なので、ファイルごとに json の `numTotalTestSuites` で見る。範囲は C のまま）
- [x] 2. 型検査の hook を自分の状態で判定する形に直す（A1'）。fixture を先に書いて落ちることを確かめてから直す（20261112。tsc の出力の cksum を `${TMPDIR}/claude-stop-typecheck/<session_id>` に残す。fixture TC1〜7 は直す前に TC1・3・4 が落ち、直した後 `test:hooks` 389/389。validate・test:sandbox・lint も通る）
- [x] 3. ゲートの fixture の仕組みと、テストの有無・免除・ベースとの差分・worktree・削除だけ・対象外のファイルのケースを書き、ゲートの骨格（判定 1〜4・免除のファイル）を通す（20261112。`stop-test-gate.sh` と fixture GT1〜22（偽の vitest は対応表で件数を返し、呼び出しを数える）。hook が無い状態で FAIL、書いた後 `test:hooks` 411/411。hook を 5 か所壊すと該当ケースが落ちることも確かめた（一回限り）。lint・test:sandbox は通る。validate は「配る hook が雛形に未登録」の 1 件だけ FAIL で、項目 6 の登録で直る。vitest の結果を読めないときは警告だけ（項目 4 で道具の故障として仕上げる）。実行ビットが未設定）
- [x] 4. テストの成否・打ち切り・道具の故障・同じ差分で流さない、のケースと実装（20261112。fixture GT23〜37（偽の vitest は本物と同じ形の json を書き、眠る・json 無しで終わるも真似る）。書く前に 11 件 FAIL、実装後 `test:hooks` 426/426。hook を 8 か所壊すと該当ケースが落ちることを確かめた（一回限り）。打ち切りで子のプロセスまで止めることは GT27 で pid を見て確かめる。lint・test:sandbox は通る。validate は項目 6 まで 1 件 FAIL のまま。細部は decisions.md）
- [x] 5. テストを弱めた判定・タスクの外の免除の警告、のケースと実装（20261112。fixture GT38〜52。書く前に 11 件 FAIL、実装後 `test:hooks` 441/441。hook を 7 か所壊すと該当ケースが落ちることを確かめた（一回限り。見分けられなかった 1 か所は GT46 を足して直した）。lint・test:sandbox は通る。validate は項目 6 まで 1 件 FAIL のまま。数え方は decisions.md）
- [x] 6. settings とその雛形に登録し、README（依存の一覧・hook の説明・cp の行・外す目安）を直す。`test:sandbox` を通す（20261113。Stop に timeout 180 で登録。`check_settings.py` に「Stop に 2 本あり、ゲートの timeout が hook の中の既定の打ち切り（150）より長い」検査と self-test 3 件を足し、登録前に FAIL を確かめた。validate 10/10・test:hooks 441/441（SKIP 0）・test:sandbox・lint が通る。依存の一覧は項目 3 で済み。実行ビットは sandbox で付けられず、ユーザーに依頼（`bash` 経由で呼ぶので動作には影響しない））
- [x] 7. steering の 3・4（A2）と design-doc の 4（A4）を直す。`eval/gen_design_cases.py` の s1・s2 の tasklist と `q1-right-item` を直し、A2・A4 の grader を足す（20261113。steering の 3 に完了条件をテストで確かめてコマンドと結果を書く・確かめられないときは書かない・免除のファイルに書き足す、4 に結果の 1 行を足した。design-doc の 4 に実装の項目にテストを含める・テスト不要は test-exemptions.md、5 にそのパスの報告。s1・s2 の tasklist を実装とテストを同じ項目にし、`q1-right-item` を合わせた。A2 は `s1-resume` の `q4-test-evidence`、A4 は D1_ITEMS の `tests-in-items`（d1b にも付く）。生成を一時ディレクトリで確かめた。validate・test:hooks 441/441・test:sandbox・lint が通る。採点の確かめは項目 9 の回帰ケース）
- [x] 8. validate に C3 の検査と self-test を足す（20261113。項目 10 として、導入の語で行を探し「:」の後ろを「・」で分けた条件が 3 つで、ファイルごとの目印の組（CLAUDE.md は「承認制のパス」、design-doc は「CLAUDE.md」「docs」「.claude」）にそれぞれ 1 つずつ当たるかを見る。self-test は目印 1 つずつの削除・条件の追加・行の削除の 12 通りで、落ちなかったものは 0。validate 11/11・test:hooks 441/441・test:sandbox・lint が通る）
- [x] 9. `validate`・`test:hooks`・`test:sandbox`・`lint` を流す → 回帰ケースの見積もりを示し、承認後にユーザーに流してもらう → 結果を読んで確かめる（20261113。静的検査は 4 つとも通る。回帰ケースは 3 回に分けて流し、合計 8.33 ドル。d1・d2・d3・s1〜s3 に回帰なし。採点を 2 つ直した（A4 は d1 では確かめられないので d1b へ、s1 の tasklist の採点はテストを流せず未チェックで残すのも合格に）。d1b が 3 回中 2 回だったので、design-doc に「既存のテスト・型検査だけでは項目のテストにならない」を足し、3 回とも合格。詳細は eval-20261113.md・decisions.md）
- [x] 9b. レビューの 20 件を直す（review-result.md の 20261114）。fixture を先に足して落ちることを確かめてから hook を直す。型検査はターンごとに差し戻し直す・timeout の余裕は 10 秒・拡張子は足しモノレポは README に対象外と書く（decisions.md 20261114）（20261114。fixture GT53〜78・TC3b を先に足して 10 件 FAIL を確かめ、hook を直して test:hooks 468/468。hook を 20 か所壊して全部落ちることを確かめた（一回限り）。test:sandbox に余裕 10 秒の検査。validate・lint も通る。詳細は review-result.md。直しのレビューで出た 13 件も直した（カバレッジを切る・設定の dotfile を除く・run の部分一致・fixture GT79〜91。test:hooks 481/481。13 通り壊して全部落ちた））
- [x] 10. レビュー → PR（統合用ブランチへ）（20261114。レビュー 2 回・指摘 33 件を直した。feature/skill-loop-fixes を push し、PR #26 を作った。CI は無い）
- [ ] 10b. 配置先の最初のプロジェクトで、テストのゲートの所要時間を測り、打ち切り時間（150 秒）と実装ファイルごとの起動を見直す（レビューで「設計どおり」とした性能の件）

## PR 2 — 知見を設計で読む（ブランチ `feature/design-reads-knowledge`）

- [x] 11. design-doc の 2 に `docs/knowledge/` を読む 1 行を足し、知見を置いた評価のケースを足す（20261114。ケースは d5-knowledge: d1b と同じ依頼に「選択肢の一覧は API を足さず固定で持つ」の知見と関係ない知見を置く。採点は固定で持つ・知見を根拠に挙げる・関係ない知見を持ち込まない。生成を一時ディレクトリで確かめた。validate・test:hooks 481/481・test:sandbox・lint が通る。採点の確かめは 12 の回帰ケース）
- [x] 12. 静的検査 → 回帰ケースの見積もり・承認・実行 → レビュー → PR（20261114。静的検査は validate 11/11・test:hooks 481/481・test:sandbox・lint が通る。回帰ケースは d5・d1b を 3 回ずつ、合計 2.68 ドルで全採点が合格。最終回答と design.md を読んで確かめた: d5 は 3 回とも知見を読み、選択肢を固定で持ち、知見を根拠に挙げ、日付の作業を持ち込まない。d1b は「docs/knowledge/ は無い」と書いて飛ばし、従来どおり一覧の API を推す。変える前の design-doc での比較は流していない。詳細は eval-20261114.md。レビューで確かめられた 2 件を直した: 差のつかない q3 を `ind-no-unrelated-knowledge` に、README の design-doc の実費を 0.13〜0.5 に。生成を一時ディレクトリで確かめ、静的検査 4 つが通る。feature/design-reads-knowledge を push し、PR #27 を作り、マージ済み。CI は無い）

## PR 3 — レビューまわり（ブランチ `feature/review-upkeep`）

- [x] 13. 差分を数えるスクリプトと `tests/skills/` のテスト・`test:skills` を書き、Step 1 を短くする（C1）（20261114。`scripts/count-diff.sh`（bash と git だけ。指定なし／`--base`／`--base --worktree`／`-- <パス>`）。テスト CD1〜19 は書く前に 17/17 FAIL、実装後 `test:skills` 19/19。各ケースで今の手順（shortstat＋未追跡の no-index numstat）と files・lines が一致することもテストの中で突き合わせる。写しを 12 通り壊し、等価な 1 通り以外は落ちることを確かめた（一回限り。見逃した IFS の件は CD18 を足して直した）。Step 1 の patch の書き出しに `--worktree` とパスの指定を足した。skill-test の Step 1・README に test:skills を足した。validate 11/11・test:hooks 481/481・test:sandbox・lint が通る）
- [x] 14. `review-test` の起動条件と観点、`review-verify` の 3 種類の基準を足す（A3）。テストの無い差分・形だけのテストの評価のケースを足す（20261114。Step 2 の起動条件を「テストファイルか実装ファイルの変更」にし、実装ファイルとテストファイルの定義をゲートと同じに書いた。review-test は指摘に種類（テストが足りない・形だけ・過剰・その他）を付け、review-verify は種類ごとに「確かめられた」の条件を置き換える。Step 3 で種類を付けたまま渡し、Step 4 で形だけの指摘に「どう壊したか」を書く。ケースは t1-missing-test（クリアのボタン。テストを変えない）と t2-shallow-test（価格順に並べ、順を見ないテスト）。生成を一時ディレクトリで確かめ、評価用アプリの写しで t1・t2 のテストと tsc が通り、t2 は並べ替えを逆にしても 4/4 通ることを確かめた（一回限り）。validate・test:hooks 481/481・test:skills 19/19・test:sandbox・lint が通る。報告されるかの確かめは 16 の回帰ケース）
- [x] ~~15. 報告に担当を添える（C2）~~（20261114。やめた。decisions.md）
- [x] 16. 静的検査 → 回帰ケースの見積もり・承認・実行（Step 1 の費用の目安を測り直す）→ レビュー → PR（20261114 途中。1 回目は 4.86 ドル。t1 は review-test がテストの無い差分で起動し「テストが足りない」を壊し方つきで報告した。r-c は t18 を見逃した（前の 2 回は検出。シェルの差分で今回の変更と関係が薄い）。l1 は 3 回とも費用を示して止まった。n1・p2・t2 は評価の sandbox で git が動かずスクリプトが失敗して止まった → スクリプトに `GIT` を足し、スキルに呼び直しを書いた（decisions.md）。test:skills 20/20（CD20 を足す前に落ちることを確かめた。git を呼ぶ箇所を 1 つずつ素の git に戻すと CD20 が落ちることも確かめた。一回限り）。validate・test:hooks 481/481・test:sandbox・lint が通る。流し直しでは p2 が合格、n1・t2 は bash の `command -v` が評価の sandbox で git を見つけられずまた止まった → 事前検査を外した（decisions.md）。test:skills 20/20・validate 11/11・test:hooks 481/481・test:sandbox・lint が通る。3 回目の流し直し（1.85 ドル）で n1・t2・l1 とも count-diff.sh が通り、t2 は形だけのテストを壊し方つきで報告、l1 は 3 回とも止まった。t2 の stop-no-src-bash は TMPDIR の写しへの sed -i を拾った誤検知。採点は mktemp -d を含むコマンドを数えない形に直し、費用の目安を 500 行まで 0.7〜3 ドルに直した。生成を一時ディレクトリで確かめ、test:skills 20/20・validate 11/11・test:hooks 481/481・test:sandbox・lint が通る。レビューで確かめられた 10 件のうち 9 件を直した（F12 は直せない。review-result.md）。test:skills 24/24・14/14・validate 11/11・test:hooks 481/481・test:sandbox・lint が通る。feature/review-upkeep を push し、PR #28 を作った。CI は無い）

## PR 4 — 変える前のコードで流す判定（ブランチ `feature/test-before-check`）

- [x] 17. 判定の手順（ベースのコードの用意・テストの持ち込み）を、スクリプトとテストで作る。リファクタリングの除外は 18 でスキルに書く（20261114。`scripts/run-tests-on-base.sh` と `tests/skills/run_tests_on_base.py`（偽の vitest で RB1〜23）。書く前に 19/19 FAIL、実装後 23/23。スクリプトを 19 通り壊し、見逃した 6 通りはケースを強めて全部落ちるようにした（一回限り）。評価のサンプルアプリの写しで本物の vitest（5.0.4）でも流し、t2 の形だけのテストだけを報告し、ベースに無い部品の import は落ちたと数えることを確かめた（一回限り）。test:skills 24/24・14/14・23/23・validate 11/11・test:hooks 481/481・test:sandbox・lint が通る。細部は decisions.md）
- [x] 18. frontend-code-review に組み込み、評価のケースを足す（20261114。Step 3 の検証の前に run-tests-on-base.sh を呼び、通ったテストを形だけの指摘として残す。リファクタリングでは呼ばない。新しいケースは足さず、t2 に `q2-ran-tests-on-base` を足した。生成を一時ディレクトリで確かめた。test:skills 24/24・14/14・23/23・validate 11/11・test:hooks 481/481・test:sandbox・lint が通る。報告に出るかの確かめは 19 の回帰ケース）
- [ ] 19. 静的検査 → 回帰ケースの見積もり・承認・実行 → レビュー → PR（20261114 途中。静的検査は通る。回帰ケース t2・t1・n1・p2 を 6.99 ドルで流し、全部合格（上限で飛んだ 3 件は最終回答を読んで判定）。t2 は 3 回ともスクリプトが形だけのテストを出して報告に載り、t1 は呼ばず、n1・p2 は誤った報告なし。詳細は eval-20261114-test-before.md。レビューで確かめられた 14 件を全部直した（passed-on-base は検証役に候補として渡す形に変えた。review-result.md・decisions.md）。test:skills 24/24・14/14・34/34・validate 11/11・test:hooks 481/481・test:sandbox・lint が通る。直した採点・手順での回帰ケースは流していない。残りは PR）

## 仕上げ

- [ ] 20. main に注釈付きのタグを打つ（戻り先）
- [ ] 21. steering で閉じる（history.md に 1 行）→ 統合用ブランチを main へ PR
- [ ] 22. tasklist の更新
