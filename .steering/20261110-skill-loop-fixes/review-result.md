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
