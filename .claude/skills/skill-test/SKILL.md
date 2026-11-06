---
name: skill-test
description: "マスター専用。スキルの回帰テストを回す。無料の静的検査（validate・test:hooks・lint）を先に流し、課金のある実行（claude plugin eval の回帰ケース）は費用の見積もりと無料の代替を示して承認を取ってから、ユーザーに流してもらう。結果は採点役の判定をうのみにせず、最終回答を読んで確かめる。"
when_to_use: "「スキルをテストして」「回帰テストを回して」「このスキルが止まるか確かめて」など。スキル本文の作成・改善には使わない（templates から書く・普通に編集する）。"
metadata:
  version: "2.0"
---

# skill-test（マスター専用・配布しない）

スキルを変えたら、壊れていないかを確かめる。無料のものを先に、課金のものは承認の後に。

## When NOT to use

- スキルを新しく書く・直す → このスキルを使わない（`templates/SKILL.template.md` から書く）
- 新しいスキルを残すか消すかの評価（A・B・C の比較） → `eval/README.md` の手順で、課題と採点基準を先に固定してから行う

## Step 1 — 静的検査（無料・毎回）

```bash
mise exec -- pnpm run validate
mise exec -- pnpm run test:hooks
mise exec -- pnpm run lint
```

落ちたら、原因を報告して止まる。課金の実行には進まない。

## Step 2 — 回帰ケースを選び、見積もりを示して止まる

変えたスキルの回帰ケースを `eval/README.md` の「回帰テスト」の表から選ぶ。示すこと:

- 流すケースと回数（表のとおり。停止を確かめるスキルは 3 回。たまにしか破れない停止を 1 回では見逃す）
- 費用の見積もり（ケースごとの 1 実行の実費は表にある。5 時間枠ではおよそ 1 ドルあたり 6〜11%）
- 無料の代替: Step 1 だけで終える。本文の言い回しだけを直したなら、それで足りることが多い

**ここで止まる。** 承認をもらうまで、課金のある実行を始めない。

## Step 3 — ユーザーに流してもらう

`claude plugin eval` は、sandbox の中の Claude Code ではなく、通常のターミナルで流してもらう。コマンドの形:

```bash
cd eval
./prepare.sh c <group>
claude plugin eval . --case '<ケースの名前 1 つ。省略せずに書く>' --runs <表の回数> --scaffold --allow-tools Write Edit Bash \
  --no-publish --keep-temp --json results-<group>-<日付や名前>.json --ablation none --max-cost-usd <上限>
```

- `--case` は 1 回に 1 つしか効かない。複数のケースは、ケースごとに別のコマンドで流す。名前を全部書く（`s1-*` のように前方だけだと、設計と知識の両方に当たった）
- 結果のファイル名は実行ごとに変える（上書きしない）
- `--ablation none` で、スキルなしの比較を回さない（回帰テストでは要らない）

## Step 4 — 結果を確かめて報告する

- 結果の JSON を grader ごとの合否で読む（score は `ind-` も混ざるので使わない）
- 最終回答（trace の `type: result`）を `.steering/[task]/` の下に写す。trace は `/private/tmp` にあり、数日で消える
- 採点役（llm）の不合格と、怪しい合格は、最終回答を読んで確かめる。採点役の誤りは多い（厳しすぎる方向が多い）
- 停止の grader が落ちたら、引っかかったコマンドを読む。`$TMPDIR` のコピーの中の書き込みや、読むだけのコマンドで落ちることがある

報告: ケースごとの合否（人が直した採点はそう書く）・費用・落ちたものの中身。
