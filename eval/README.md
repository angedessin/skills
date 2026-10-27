# eval

skillset-renewal のスキル評価（A・B・C の 3 条件）。課題と採点基準の正本は `.steering/20261006-skillset-renewal/eval-<group>-group.md`（design・impl）。

## 構成

| パス | 中身 |
|---|---|
| `evals/<group>/` | グループごとのケース（B と C で共通。1 か所だけに置く）。各ケースの tags の先頭がグループ名 |
| `reserve/<group>/` | 再評価用の課題。C が B より悪かったときだけ `evals/<group>/` へ移して使う |
| `common-claude-md.md` | 全条件共通の CLAUDE.md。各ケースの `append_system_prompt` と一致しているかを `prepare.sh` が検査する |
| `conditions/b/<group>-skill-claude-md.md` | B にだけ足す「スキルに触れる CLAUDE.md」（設計グループだけ。タグの .steering ルール 1〜3） |
| `conditions/c/<group>/` | 評価中のグループの C（`skills/`・`agents/`）。判定が出たらマスターの `.claude/` へ移して消す |
| `hooks/` | 上の CLAUDE.md を SessionStart で注入する hook（plugin の無い A には入らない） |
| `prepare.sh` | `skills/`・`agents/`・`plugin.json` を、グループごとに条件 B か C に入れ替える |
| `evalcase.py` | ケースの生成の共通部品 |
| `gen_<group>_cases.py` | ケースの生成元。ケースを直すときはこれを直して再実行する |

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
