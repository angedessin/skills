# eval

skillset-renewal のスキル評価（A・B・C の 3 条件）と、残したスキルの回帰テスト（末尾の節）。課題と採点基準の正本は `.steering/archived/20261006-skillset-renewal/eval-<group>-group.md`（design・impl・review・knowledge）。

## 構成

| パス | 中身 |
|---|---|
| `evals/<group>/` | グループごとのケース（B と C で共通。1 か所だけに置く）。各ケースの tags の先頭がグループ名。`prepare.sh` が生成し、コミットしない |
| `reserve/<group>/` | 再評価用の課題。`prepare.sh` が生成し、コミットしない。C が B より悪かったときだけ、`prepare.sh` の後に `evals/<group>/` へ移して使う |
| `common-claude-md.md` | 全条件共通の CLAUDE.md。各ケースの `append_system_prompt` と一致しているかを `prepare.sh` が検査する |
| `conditions/b/<group>-skill-claude-md.md` | B にだけ足す「スキルに触れる CLAUDE.md」（設計グループだけ。タグの .steering ルール 1〜3） |
| `conditions/c/<group>/` | 評価中のグループの C（`skills/`・`agents/`）。判定が出たらマスターの `.claude/` へ移して消す |
| `hooks/` | 上の CLAUDE.md を SessionStart で注入する hook（plugin の無い A には入らない） |
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
| design-doc | design | `d1-category-filter`・`d2-vague-request`・`d3-small-change` | 3 | 0.2〜0.4 | src に書かずに止まる・聞くべきことを聞く・小さな作業は手順に乗せない |
| steering | design | `s1-resume`・`s2-unapproved` | 3 | 0.1〜0.35 | 新しい決定を正として再開する・DRAFT なら実装しない |
| e2e | impl | `e1b-write-e2e-delegated`・`e2-review-e2e` | 3 | 0.3〜0.4 | 主要な流れに絞って書く・レビューでは直さない |
| frontend-code-review | review | `n1-result-count`・`p2-race`・`r-c-rm-mv-policy` | 1 | 0.8・0.8・2.5 | 誤検知（バグなし）・仕込みバグの検出・過去の差分の検出。agent の結果がそろってから報告する |
| session-retrospective | knowledge | `s1-session-friction` | 3 | 0.2 | 摩擦を拾い、タスクのフォルダの skill-issues.md に書く |
| pr-create | pr | `pr1-feature-branch`・`pr2-spike` | 3 | 0.12〜0.18 | push と PR 作成の前で止まる・SPIKE では作らない |

- design-premortem は手動専用（`disable-model-invocation`）で、プロンプトでは発動しないので回帰ケースを持たない。`p1-premortem`・`p2-self-review` は、素のモデルの穴探しを確かめるケースで、スキルの本文は通らない
- skill-test はマスターの保守用で、回帰ケースを持たない
- 削除したスキルのケース（impl-from-design・tdd・knowledge-capture・compound・rule-audit など）は、判定の根拠として残すだけで、回帰テストには使わない
- 結果の最終回答は `.steering/[task]/` の下に写す（trace は `/private/tmp` にあり、数日で消える）
- Claude Code 2.1.318 の評価の sandbox では git が動かないことがある（xcrun のキャッシュが作れない）。grader が合格でも、git を使うケースは trace で git が動いたかを見る
