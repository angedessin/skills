# eval

skillset-renewal のスキル評価（A・B・C の 3 条件）と、残したスキルの回帰テスト（末尾の節）。ケースの正本は `gen_<group>_cases.py`。課題と採点基準を決めた経緯は、閉じたタスク `20261006-skillset-renewal` の `eval-<group>-group.md`（design・impl・review・knowledge）にあり、git の履歴から読む（探し方は `.steering/history.md`）。

## 構成

| パス | 中身 |
|---|---|
| `evals/<group>/` | グループごとのケース（B と C で共通。1 か所だけに置く）。各ケースの tags の先頭がグループ名。`prepare.sh` が生成し、コミットしない |
| `reserve/<group>/` | 再評価用の課題。`prepare.sh` が生成し、コミットしない。C が B より悪かったときだけ、`prepare.sh` の後に `evals/<group>/` へ移して使う |
| `common-claude-md.md` | 全条件共通の CLAUDE.md。各ケースの `append_system_prompt` と一致しているかを `prepare.sh` が検査する |
| `conditions/b/<group>-skill-claude-md.md` | B にだけ足す「スキルに触れる CLAUDE.md」（設計グループだけ。タグの .steering ルール 1〜3） |
| `conditions/c/<group>/` | 評価中のグループの C（`skills/`・`agents/`）。判定が出たらマスターの `.claude/` へ移して消す |
| `hooks/` | 上の CLAUDE.md を SessionStart で注入する hook（plugin の無い A には入らない）。`hooks.json` は `prepare.sh` が毎回作り、コミットしない。review の C では、マスターの `subagent-tree-guard.sh`（検証役の作業ツリーの見張り）も複製して登録する |
| `prepare.sh` | `evals/`・`reserve/` を生成し直し、`skills/`・`agents/`・`plugin.json` をグループごとに条件 B か C に入れ替える |
| `evalcase.py` | ケースの生成の共通部品 |
| `gen_<group>_cases.py` | ケースの生成元（正本）。ケースを直すときはこれを直して `prepare.sh` を流す。判定のときの生成物は git の履歴（`79bf4d4`）にある |

## 実行（課金。sandbox を有効にした Claude Code の中ではなく、通常のターミナルから）

実行の前に、費用を見積もってユーザーの承認を取る。評価の期間中は Claude Code の自動更新を止める。

```bash
cd eval
./prepare.sh b impl
claude plugin eval . --tag impl --scaffold --allow-tools Write Edit Bash --no-publish --keep-temp --json results-impl-b.json --max-cost-usd <上限>
# A（plugin なしの baseline arm）も同時に回る

./prepare.sh c impl
claude plugin eval . --tag impl --scaffold --allow-tools Write Edit Bash --no-publish --keep-temp --json results-impl-c.json --ablation none --max-cost-usd <上限>
```

採点役のモデルは `--judge-model` で指定する（既定は haiku）。llm の採点役は `focus: trace` だと記録の最初と最後の 12 件しか読まないので、llm は最終回答とファイルだけを見て、途中の手順は機械の grader で見る。

grader の名前の頭は、集計での扱いを表す: `stop-`（停止。3 回中 1 回でも落ちたら不合格）・`how-`（止まり方）・`q`（結果の質。閾値はこの合計の満点の 10%）・`ind-`（スキルが発動したかの表示。採点しない）。`--ablation none` では `ind-` も道具の score に入るので、集計は grader ごとの合否から出す。

## 回帰テスト（残したスキル）

スキルを変えたら、そのスキルの行のケースを C（マスターの版）で流す。手順は skill-test スキル。`./prepare.sh c <group>` で準備し、`--case` にはケースの名前を全部書く（前方だけだと別のグループに当たる）。`--case` は 1 回に 1 つしか効かないので、複数のケースはケースごとに別のコマンドで流す。

| スキル | group | ケース | 回数 | 1 実行の実費（評価のとき・ドル） | 見るもの |
|---|---|---|---|---|---|
| design-doc | design | `d1-category-filter`・`d1b-category-filter-delegated`・`d2-vague-request`・`d3-small-change`・`d5-knowledge` | 3 | 0.13〜0.5 | src に書かずに止まる・聞くべきことを聞く・実装の項目にテストを含める（d1 は書く前に聞いて止まるので、設計を書き切る d1b で見る）・`docs/knowledge/` の知見を設計に反映する（d5）・小さな作業は手順に乗せない |
| steering | design | `s1-resume`・`s2-unapproved`・`s3-close-task`・`s4-ready-to-close`・`s5-close-needs-pr` | 3 | 0.1〜0.35（s4・s5 はテストを流すので 0.3 前後） | 新しい決定を正として再開する・確かめたテストのコマンドと結果を書く・DRAFT なら実装しない・閉じる前に確認して何も消さない・PR の済んだタスクの残りを終えたら、閉じる確認（索引の行と消すフォルダ）を出し、何も消さず push しない（s4）・PR の項目が未チェックなら、残りを終えても閉じる確認を出さず PR を先にするよう示す（s5）。評価の sandbox では git やテストが動かない回があり、s4 はそこでスキルどおり止まると採点役は不合格にする（最終回答を読んで判定する） |
| e2e | impl | `e1b-write-e2e-delegated`・`e2-review-e2e` | 3 | 0.3〜0.4 | 主要な流れに絞って書く・レビューでは直さない |
| frontend-code-review | review | `n1-result-count`・`p2-race`・`r-c-rm-mv-policy`・`t1-missing-test`・`t2-shallow-test`／`l1-large-diff`／`x1-exemption-added` | 1／3／3 | 0.7・0.8〜1.3・2.8・0.9・0.7／0.15〜0.19／0.8〜0.95 | 誤検知（バグなし）・仕込みバグの検出・過去の差分の検出・テストの無い変更を「テストが足りない」と報告する（t1。テストファイルが変わっていない差分でも review-test が動く）・形だけのテストを、どう壊したかと一緒に報告する（t2。変える前のコードで流すスクリプトを実行したかも `q2-ran-tests-on-base` で見る。呼んだだけでなく判定まで進み、変える前でも通ったテストが出たかを `q3-got-tests-on-base`（trace の `regex`）で見る（20261120。評価の sandbox で PATH の jq が abort しても q2 は合格していたため）。t1 はテストファイルが変わらないので呼ばないことを `q2-skips-tests-on-base` で見る。検証役がリポジトリ本体を変えなかったかを `stop-tree-checked` で見る: 見張りの hook が結果をワークスペースの `.git/tree-guard.log` に写し、`TREE-GUARD-CHECKED` があり `TREE-GUARD-DIFF` が無ければ合格。印が無い（hook が発火しない）ときも落ちる。hook の出力は trace に載らないのでファイルに写す（20261117 に Claude Code 2.1.326 の試し実行 1 回で一回限りで確かめた。版が変われば変わりうる）。検証役が動かない l1・n1 などには付けない）。agent の結果がそろってから報告する／大きい差分では agent を起動する前に、費用の目安を示して止まる（git が動いたかを trace で見る）。`stop-no-src-*` は一時ディレクトリ（mktemp・TMPDIR・/var/folders・/tmp/claude-）を指す書き込みを数えない（検証役が写しの上で再現するため。tests/skills/run_eval_graders.py）／差分で足したテストの免除を、パスと理由つきで報告に載せる（x1。`q1-exemption-shown` は最終回答にパスと理由が 80 字以内に並ぶかを `regex` で見る。`list-exemptions.sh` を実行したかも `q2-ran-list-exemptions` で見る。免除が妥当かは採点しない） |
| session-retrospective | knowledge | `s1-session-friction` | 3 | 0.2 | 摩擦を拾い、`.steering/skill-issues.md` に書く |
| pr-create | pr | `pr1-feature-branch`・`pr2-spike`・`pr3-exemption`・`pr4-close-after-pr`・`pr5-design-only` | 3 | 0.13〜0.21 | push と PR 作成の前で止まる・SPIKE では作らない・ブランチのコミットで足したテストの免除を、示した本文にパスと理由つきで載せる（pr3。`q1-exemption-shown`）・閉じてよくなるタスクでは「閉じる確認を続けて出します」と予告し、PR の前に PR の項目へチェックを付けない（pr4。予告は `regex`）・DRAFT の設計だけの PR では予告しない（pr5）。PR を作った後の振る舞いは 1 ターンでは見られない（push の前で止まるため） |

- `prepare.sh` は `skills/`・`agents/` を消して入れ替えるので、実行中のケースからスキルが消える。別のグループの準備と実行は、前のグループの実行が終わってから行う（20261116。x1 の実行中に `./prepare.sh c pr` が流れ、3 回中 2 回が無効になった。20261121 にも 2 回続けて起きた）。`prepare.sh` は実行中の `claude plugin eval` を `pgrep` で見つけると、何も消さずに exit 1 で止まる（別のプロジェクトの評価で止まるときは `PREPARE_FORCE=1`）。複数のグループは `&&` でつないだ 1 つのコマンドで流す
- design-premortem は手動専用（`disable-model-invocation`）で、プロンプトでは発動しないので回帰ケースを持たない。`p1-premortem`・`p2-self-review` は、素のモデルの穴探しを確かめるケースで、スキルの本文は通らない
- skill-test はマスターの保守用で、回帰ケースを持たない
- frontend-code-review 2.1 は、1,000 行・20 ファイルを超える差分でレビューの前に止まる。超える `r-a-hardening`・`r-b-deploy-integrity`・`f1-semicolon` は、依頼文で範囲と費用を了承している（20261110 から。それより前の結果は「コードをレビューして。」だけで流した）
- 削除したスキルのケース（impl-from-design・tdd・knowledge-capture・compound・rule-audit など）は、判定の根拠として残すだけで、回帰テストには使わない
- 結果の最終回答は `.steering/[task]/` の下に写す（trace は `/private/tmp` にあり、数日で消える）。タスクを閉じるとフォルダごと消えるので、残す結論は PR の本文にも書く
- `file_exists` の `exists: true` は、フィクスチャが置いたファイルを「無い」と判定する（2.1.319。実行中に作ったファイルは見える）。フィクスチャのファイルが残ったかは、消す・移すコマンドを打っていないか（`tool_used` の `max: 0`）で見る
- 評価の sandbox では、素の `git`（macOS の `/usr/bin/git`）が `xcode-select: Failed to locate 'git'` で rc=72 になる（2.1.310〜2.1.319）。評価が作る設定（`/private/tmp/e-*/config/settings.json`）が、`sandbox.credentials.files` で git の本体（`/Library/Developer/CommandLineTools/usr/bin/git` など）を拒否し、`denyRead` で xcrun のキャッシュのある `/var/folders/.../T` を拒否するため。評価の外の通常のセッションでは起きない。モデルが `/usr/local/bin/git` に切り替えると動くが、切り替えずに止まることもある（20261107 の s3 で 3 回中 1 回）。grader が合格でも、git を使うケースは trace で git が動いたかを見る。PATH を変えても直らない。`/usr/local/Cellar/git/.../bin/git` も同じ設定で deny になるが、実行はできて stat だけが拒まれる。そのため bash の `command -v <パス>` は「無い」と判定する（20261114。count-diff.sh は事前検査をせず、git を呼んだ結果で判定する）
