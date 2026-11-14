# レビューの結果: skill-loop-fixes

## 20261114 — PR 1（feature/skill-loop-fixes...HEAD、.steering/ を除く。12 ファイル・912 行）

担当: バグ 2 体・規約・テスト → 検証役。指摘 27 件のうち、確かめられた 20 件を残す。

### Medium

1. **改名でテストを弱めた判定をすり抜ける／改名だけで誤って差し戻す** — `.claude/hooks/stop-test-gate.sh:118`・`:154`。`git diff --name-only` が改名を検出して新しい名前だけを返し、ベースの版が空になる。`git mv a.test.ts a.spec.ts` して expect を減らしてコミット → exit 0。`it.skip` を含むファイルを `git mv` しただけ → exit 2。直し方: `--no-renames` か `--name-status -M` で古いパスの版と比べる。（再現した）
2. **変えたテストファイルそのものは流さない** — `stop-test-gate.sh:224`。実装を変えずにテストだけを落ちる形にすると、vitest を呼ばずに exit 0 でハッシュも残る。直し方: 差分のテストファイル（残っているもの）も流して失敗の判定に入れる。（コードを読んだ）
3. **件数があって落ちたファイルが無ければ、vitest の rc≠0 でも通る** — `stop-test-gate.sh:239-259`。Unhandled Errors で exit 1・各ファイルは passed のとき、通してハッシュも残す。直し方: rc≠0 で失敗が見つからなければ、少なくともハッシュを残さず警告か差し戻し。Unhandled Errors 時の json の形は未確認。（コードを読んだ）
4. **fixture: キャッシュのハッシュから追跡済みの差分を消しても落ちない** — `tests/hooks/run_fixtures.py` GT31〜33。hook `:133` を消しても 441/441。直し方: 通った後に追跡済みの実装を書き換えて流し直すケースを足す。（再現した）

### Low

5. origin/HEAD が無く main でもない（master など）リポジトリでは、feature のコミット済みを見ない — `stop-test-gate.sh:33-49`。候補に master・`init.defaultBranch` を足す
6. 免除のパスを完全一致で照合し、`` `src/a.ts` ``・`./src/a.ts` が効かない — `stop-test-gate.sh:89-97`。前後のバッククォートと `./` を取ってから照合する
7. 根を git のトップレベルに決め打ち（モノレポで素通り）。`.mts/.cts/.mjs/.cjs/.vue/.svelte` が対象外 — `stop-test-gate.sh:26-29`・`:59`・`:101`。README に限界として書くか対応する
8. 型検査: 一度差し戻したエラーが残る限り、以後のターンでも警告だけになる — `stop-typecheck.sh:20-36`。ターンの最初の Stop（`stop_hook_active=false`）で状態を消す
9. `check_settings.py:201` の `outer <= inner` は 151 で通り、self-test も境界を見ない。差に下限（例: 10 秒）を設け、150 のケースを足す
10. README:121 の「型検査が 120 秒近くで外す」が `stop-typecheck.sh:8` の「20-30 秒を超えたら外す」と食い違う（規約）
11. `run_fixtures.py:816` の偽の vitest の形の突き合わせに「一回限り」の明記が無い（CLAUDE.md の「手作業で突合した検証項目は…『一回限り』と明記する」）
12. fixture: 日本語名のファイルが無く `core.quotepath=false` を外しても落ちない
13. fixture: jq が無いと SKIP だが runner は exit 0（「SKIP が 0 件」を機械で保証しない）— `run_fixtures.py:1278-1291`
14. fixture: origin/HEAD があり main の上にいるケースが無い（`${base#origin/}` を壊しても通る）
15. fixture: exit 0 のケースが stderr を見ない（`[ -x "$VITEST" ] || exit 0` を消しても GT2 が通る）
16. fixture: import のエラーの `message` の経路を消しても落ちない（失敗の文が欠けるだけ）
17. fixture: 実装は .ts、弱めた判定は a.test.ts だけ。fit・xtest・bench.skip・.each 混じり・expect.poll が未検査
18. fixture: 偽の vitest が引数を見ない（`--run` を落とす・出力先をプロジェクトの中に向けるのを区別できない）
19. fixture: `: >"$json"` を消しても落ちない（1 つ目が結果あり・2 つ目が故障の並びが作れない）
20. fixture: exit 2 のケースが差し戻しの種別を見ない／`stop()` の TimeoutExpired を握らない／タスクがあるときに global の免除を警告に使わない分岐のケースが無い

### 捨てた・残した指摘

- 設計どおり（3 件）: main の上での直接のコミットは未コミットだけを見る（decisions 20261111）／性能（実装ファイルごとの起動・差分全体のハッシュ。打ち切りは仮の値で、実測で見直すと論点にある）／ブランチで新しく作ったテストの expect の減少（decisions 20261112。PR 4 とレビューの分担）
- 確かめられない（2 件）: CI でない vitest が新しいスナップショットを書く（vitest が手元に無い）／exit 0 の stderr が Claude やユーザーに見えるか（Claude Code の仕様。根拠が読めない）
- 問題ではない（1 件）: GT14〜15 の書いた直後の unlink（結果が変わらない）
- 規約が無いと報告された観点: 免除のファイルの書式を何か所に書くか（今は 4 か所で一致）／検査の対象のファイルが無いときの扱い（validate の規律の「SKIP」とファイルの欠落の関係）
- レビューできなかったもの: 本物の vitest での再現（B3・スナップショット）。`.steering/` は依頼で外した

### 直した結果（20261114。tasklist 9b）

- 20 件すべてを直した。fixture を先に足し（GT53〜78・TC3b。GT3 ほか 12 件に差し戻しの種別、GT2 ほか 6 件に stderr の確かめを足した）、直す前に 10 件が落ちることを確かめてから hook を直した
- 一回限りの確かめ: hook を 20 か所 1 つずつ壊し、20 通りすべてで fixture が落ちることを確かめた（初回は 2 か所を見逃したので、GT11 の読み方と GT66 の書き方を直してやり直した）
- 静的検査: validate 11/11・test:hooks 468/468（SKIP 0）・test:sandbox・lint
- 範囲を変えたもの: 変えたテストファイルも流すようにしたので、GT11・GT38・GT40 の vitest の呼び出し回数の期待を 0 から 1 に変えた。型検査の TC3 は「ターンが変われば同じエラーでも 2」に変えた
- 直さなかったもの: モノレポ（README に対象外と書き、skill-issues.md に記録）。性能（tasklist 10b で配置先で測る）

## 20261114 — 直しのレビュー（コミット 8c77f2a、.steering/ を除く。5 ファイル・465 行）

担当: バグ 2 体・規約・テスト → 検証役。指摘 17 件のうち、確かめられた 13 件を残す。

### Medium

1. **カバレッジのしきい値を config で有効にしたプロジェクトでは、毎回差し戻す** — `stop-test-gate.sh` の judge の rc≠0 の判定。related は一部のテストしか流さないのでしきい値を割り exit 1 → 落ちたファイルが無いので「失敗で終わりました」で 2。記録も残らず毎回。この直しで持ち込んだ。直し方: vitest に `--coverage.enabled=false` を渡す。（vitest 4.0.16 のコードを読んだ。5.x は未確認）
2. **fixture: 変えたテストを流す枝の組み合わせが無い** — 消したテストを渡さない・「失敗を残す」のテストを外す・時間切れ（壊すと黙って通る）・道具の故障・渡す引数。hook の該当行を壊しても全部通る（再現した）

### Low

3. `.mjs`・`.cjs` を足したので、`.eslintrc.cjs`・`.prettierrc.mjs`・`scripts/release.mjs` を「関係するテストが無い」で差し戻す（再現した）
4. `vitest run <パス>` は部分一致なので、`src/a.test.ts` で `src/a.test.tsx` なども流れる（vitest 4.0.16 のコードを読んだ）
5. タスクの外の免除の警告で、行ごとにサブシェルを起こす（1 万回で約 5 秒。計測の外）
6. fixture: 重複を除く `ran` を確かめていない
7. fixture: 型検査の「直ったら状態を消す」「セッション別」を壊しても落ちない（TC5〜7 が stop_hook_active=false なので先に状態が消える。この直しで抜けた）
8. fixture: `init.defaultBranch` の枝が無い
9. fixture: 警告の側の免除のパスの正規化が無い
10. fixture: テストでない名前への改名・`旧 → 新` の表示・ステージしない mv が無い
11. check_settings.py: 余裕 10 秒の境界（9 秒差・10 秒差）を見ていない。self-test が hook の既定 150 に依存する
12. run_fixtures.py: SKIP を失敗にしたとき「N/M passed」の数が 1 ずれる（表示だけ）
13. コメントの更新漏れ: run_fixtures.py が閉じると消える review-result.md を参照／stop-test-gate.sh の「180 秒より短く」に 10 秒の余裕が無い

### 捨てた指摘

- 問題ではない（2 件）: vitest に集められないファイルだけを変えたとき（4.0.16 は numTotalTestSuites=0 の json を書き、hook は黙って通す。流すテストが無いので正しい）／design.md の本文に決定が写されていない（steering は「新しい決定を正とする」で、写す規則は無い）
- 設計どおり（1 件）: まとめて流したテストの時間切れで全部を「判定できていない」に並べる（decisions 20261114）
- レビューできなかったもの: 本物の vitest 5.x での再現（N1・N4 は 4.0.16 のコードで確かめた）

### 直した結果（20261114）

- 13 件すべてを直した。fixture GT79〜91 を足し、GT11・GT68・GT71・TC5〜7 を直し、直す前の hook で 4 件（GT11・68・84・87）が落ちることを確かめてから hook を直した（ほかの 9 件は振る舞いは正しく、確かめが無かった所）
- 一回限りの確かめ: 直した箇所を 13 通り 1 つずつ壊し、13 通りすべてで fixture が落ちた
- 静的検査: validate 11/11・test:hooks 481/481・test:sandbox・lint

## 20261114 — PR 2（design-doc が docs/knowledge/ を読む）

対象: `feature/skill-loop-fixes...HEAD`（`.steering/` を除く。3 ファイル・26 行）。一次レビューはバグ 2 体・規約 1 体。5 件にまとめて検証役に回し、確かめられたのは 2 件。

- Low: `eval/gen_design_cases.py:81` の `q3-no-unrelated-knowledge` は、評価用アプリに日付の項目が無いので、どの条件でもほぼ合格し差がつかない（d5 の 9 票すべて PASS・design と tasklist に日付の言及 0 件で確かめた）。方向: `ind-` にして採点から外すか、そのまま残す
- Low: `eval/README.md:43` の design-doc 行の「1 実行の実費 0.2〜0.4」が実測と合わない（d5 は 0.42〜0.48。d1b は 0.42〜0.48 で変更前から、d3 は 0.13〜0.14 で下限を割る）。方向: 0.13〜0.5 に直すか、ケースごとに書く

捨てた指摘 3 件:
- q1 の FAIL 条件が却下案まで落とす曖昧さ → 問題ではない（3 回とも一覧 API を却下案に書いて 9 票 PASS。文の素直な読みでも却下案は該当しない）
- 知見を読んだかの機械の grader が無く q2 が読まずに合格しうる → 確かめられない（知見なしの d1b は一覧 API を推すので q1 で落ちる。読み方は Bash と Read に分かれ、Read だけの grader は誤判定する）
- SKILL.md:36 の「構成」が触るファイルの定義と食い違う → 問題ではない（見出し名は自由。3 回とも前提の節に書いた）
