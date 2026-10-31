# レビューの指摘のラベル付け（誤検知）

Created: 20261031

正解（T1〜T21）にも仕込みにも当たらない指摘を、人が「本物 / 誤検知 / 保留」に分ける。対象は最終回答に書かれた指摘だけ（B の R-a は Low 以下を review-result.md にだけ書いたので、表に入れていない。中身は `review-responses/r-a-B-review-result.md`）。最終回答の全文は `review-responses/` にある。

- **本物**: この差分が持ち込んだ問題で、直す価値がある
- **誤検知**: 前提が違う・変更前からある・好み・設計の意図どおり
- **保留**: 本物か判断がつかない（理由を書く）

複数の条件が同じ指摘を出したものは 1 行にまとめ、「出した条件」に並べる。

## 失った分（ラベル付けできない）

B・A の N1・N2・R-b は、最終回答を含む trace（`/private/tmp/e-*/`）が消えていて、指摘の中身が残っていない。結果の json と report.html には最終回答が入っていない。

## R-a（B・A・C。正解 T1〜T8 以外）

| # | 指摘 | 出した条件 | 重要度（出した側） | ラベル | メモ |
|---|---|---|---|---|---|
| a1 | skill-test の課金の見積が `× 2 回` のままで、`--runs 4` を反映していない（design.md:133 の修正が入っていない） | B・C | High（B）・Medium（C） | | |
| a2 | allow の `git diff*`・`git log*`・`git show*` に `--output=` を付けると確認なしで書き込める | B | High | | T1（Bash のリダイレクトで ask を迂回）と同じ系統の別経路 |
| a3 | `git diff*` が前方一致で `git difftool -x <cmd>` にも当たり、任意のコマンドを実行できる | B | High | | 変更前からある allow かどうかを確かめる |
| a4 | design.md に無い変更（ask の追加・ターン境界・Step の再構成）を、design.md を更新せずに入れた | B | Medium | | |
| a5 | 「既知差分として登録する」と決めたのに、スクリプトに登録の仕組みが無い | B | Medium | | |
| a6 | `docs/starter-kit.md:88` の配置手順に `docs/decisions/**` の ask が無い | B・A | Medium | | C の検証役は「adr は配布しないので書かないのが正しい」として捨てた |
| a7 | `check_deploy_drift.py` が SKILL.md の無いスキル（SKIP）を「ドリフトなし」と数える | B | Medium | | B は再現済み |
| a8 | ask のパスの `./` がカレントディレクトリ基準なら、サブディレクトリから起動したときに効かない | B | Medium | | B 自身が未確認と書いている |
| a9 | ルートに未追跡の `gitshow-write-test.txt`・`gitdiff-write-test.txt` が残っている | B・A | その他・細かいもの | | |
| a10 | `--master` の既定が、export worktree から実行すると古い master のコピーを指す | A | 先に直すべき | | C の検証役は「案内しているのは素通り検査の実行場所で、このスクリプトではない」として捨てた |
| a11 | 改行コードが CRLF だと frontmatter を取り除けない | A | 先に直すべき | | |
| a12 | rule-audit の監査入力が `@参照` しか見ず、素のパスで書いた参照と片側だけ揃っていない（SKILL.md:41・56） | A・C | 先に直すべき（A）・Low（C） | | |
| a13 | `check_deploy_drift.py` で `--target ""`（`$DEPLOY` が未設定）が全配置先のモードになる | A | CLI の堅牢性 | | |
| a14 | argparse に移して `--help` から `__doc__` の説明が消えた | A | CLI の堅牢性 | | |
| a15 | `read_body` の戻り値の型注釈が実際と違う・中身の無い f-string | A | 細かいもの | | |
| a16 | `tests/passthrough/debug/scenario.md:5` の `judge_glob: src/**/*.ts` がテストファイルにも当たり、スキルどおり再現テストを書くと FAIL になる。decisions の「debug 3/4」の結論に誤った FAIL が混ざりうる | C | Medium | | 判定処理で再現 |
| a17 | `tests/passthrough/impl-from-design/scenario.md:5` の判定対象が `src/**` だけで、design.md の Status を勝手に APPROVED にしても PASS | C | Medium | | 再現 |
| a18 | 同シナリオのコメントは design.md が無い分岐の回帰テストと書くが、実際は DRAFT の分岐を通る | C | Medium | | |
| a19 | `tests/passthrough/debug/scenario.md:101` の症状の書き方が逆（判定に影響なし） | C | Low | | |
| a20 | README の「CLAUDE.md・docs/ への書き込みは承認制」が、実際の ask（CLAUDE.md・docs/knowledge・docs/decisions の Edit/Write）より広い | C | Low | | |
| a21 | skillset-hardening の tasklist の「0. 変更対象の確定」が、済んだのに未チェック | C | Low | | |
| a22 | adr のシナリオで、当てはまる決定が 2 件あり聞き返しても PASS。判定対象が `docs/decisions` だけで別の場所に書いても PASS | C | Low | | 後半は再現 |

## R-c（B・A・C。正解 T15〜T19 以外）

| # | 指摘 | 出した条件 | 重要度（出した側） | ラベル | メモ |
|---|---|---|---|---|---|
| c1 | フィクスチャのランナーが、JSON のパースに失敗すると部分一致に切り替わり、壊れた出力でも pass する。`hookEventName` も見ていない | B・C | Medium | | C は hook の出力から `}` を消しても 20/20 PASS を再現 |
| c2 | フィクスチャ B16 は command が `ls` で、先頭の語だけで沈黙するので、全文を検査しないことの回帰テストになっていない | B・C | Medium | | C は hook を全文 grep に書き換えても PASS を再現 |
| c3 | フィクスチャに、クォート付き・ディレクトリごと・部分一致・壊れた入力のケースが無い | B・A・C | Medium（B）・テスト（A）・Low（C） | | 正解の穴を塞ぐテストの欠落。指摘としては本物になりやすい |
| c10 | `\rm`・`sudo rm`・`FOO=1 rm`・`command rm` の前置き付きの形が素通りする | C | Low | | design の「守らない形」に載せるかの判断 |
| c11 | 大文字小文字を区別しない macOS で `rm claude.md` が CLAUDE.md を消し、hook は沈黙する | C | Low | | 既存の書き込みガードも同じ線引きと C 自身が書いている |
| c12 | `tool_input.description` を含むテストケースが無い（hook は正しく動く） | C | Low | | |
| c13 | 書き込みガードの回帰テストが 2 件だけ（`>>`・`tee` が無い）。その hook はこの差分で変わっていない | C | Low | | 変更前からの問題に近い |
| c14 | テストの置き場所が design.md:83（`tests/hooks/guard-gated-delete/`）と違う。tasklist に「相当」と記録済み | C | Low | | 記録済みの差 |
| c4 | README・starter-kit・claude-code-config の「複合は沈黙」と実装が合わない | B | Medium | | T17 の文書側 |
| c5 | 先頭の 1 語しか見ないので、`ls; rm CLAUDE.md` のように `;`・`&&` の後ろの rm を見逃す。フィクスチャ B11 がこれを正しいとして固定している | A | 重大 | | B は design が「複合は沈黙」と決めていると書いている。設計の意図どおりなら誤検知 |
| c6 | `deploy_skills.py:12` の docstring の、一緒に送る hook の一覧が古い | A | 整合性 | | |
| c7 | 対象のパスの定義が write hook・delete hook・Edit の ask の 3 か所に分かれている | A | 保守性 | | 提案寄り |
| c8 | hook のヘッダーに「sh 組み込みと grep/sed だけ」とあるが、awk・head も使っている | A | 整合性 | | |
| c9 | Bash 用の PreToolUse が 3 つに分かれていて、呼び出しごとにプロセスが 3 つ起動する | A | 保守性 | | 提案寄り |

## R-b（C だけ。正解 T9〜T14 以外。B・A の最終回答は消えた）

| # | 指摘 | 重要度 | ラベル | メモ |
|---|---|---|---|---|
| b1 | (f) が FAIL の間は、関係ない assets の編集もすべて差し戻され、design の「main で直す → export へ merge」の手順だと merge まで編集が止まる | Medium | | 再現済み |
| b2 | `MASTER_ONLY_HOOKS` を消すと ImportError で exit 2 になり素通し。SyntaxError・JSON の破損では Traceback が「契約違反」の見出しで差し戻される | Low | | |
| b3 | hook が PASS 行とサマリまで AI に返している（`docs/knowledge/claude-code-config.md:139` の「診断行だけを返す」に反する） | Low | | 規則を引用している |
| b4 | README.md:219 の説明が古い（assets モードが書かれていない） | Low | | |
| b5 | README などのパス判定が `$PROJECT_ROOT/...` との厳密一致で、`/tmp` と `/private/tmp` の違いや末尾の `/` で漏れる | Low | | T14 と同じ 4 件目の前半。T14 は後半 |

## N1（C だけ。バグなし）

| # | 指摘 | 重要度 | ラベル | メモ |
|---|---|---|---|---|
| n1-1 | 件数の表示に `role="status"`・`aria-live` が無く、スクリーンリーダーに伝わらない | Medium | | |
| n1-2 | 0 件のときに件数が出ないことのテストが無い | Low〜Medium | | 実装を書き換えてすり抜けを再現 |
| n1-3 | 件数のテストが「2 件」の 1 通りだけ | Low〜Medium | | 同上 |
| n1-4 | Fragment の中のインデントが揃っていない | Low | | 好み。agent の「指摘しないもの」に当たる |

## N2（C だけ。バグなし）

| # | 指摘 | 重要度 | ラベル | メモ |
|---|---|---|---|---|
| n2-1 | 一覧に価格が出ているかをどのテストも確かめていない | Low | | 確認の抜けは変更前から。書き換えた行の確認 |
| n2-2 | 区切りが 2 つ以上入る値（1234567）のテストが無い | Low | | |
| n2-3 | `"ja-JP"` の指定が外れても、多くの言語設定でテストが通る | Low | | |
