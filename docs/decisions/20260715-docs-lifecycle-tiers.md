# Decision: ドキュメントの鮮度管理は段階基準で運用する（当面は rule-audit の手動起動）

Date: 20260715
Status: Accepted (Amended 20260721・20260730 — 末尾の Amendments 参照)

## Context

docs/ 配下の 2 系統は AI への接続方法が異なる。knowledge（経験・パターン）は
かつて CLAUDE.md の @参照にも載せていたが、**現行は必要時に読む運用（`@` 既定なし）**と
レビュー基準への接続で行動に影響しうるため、
腐ると誤った指摘・廃止済み規約の強制として行動品質に直接跳ね返る。
decisions（ADR）は行動に配線されず、pull（決定を蒸し返す場面）でのみ読まれる。

従来、knowledge の中身の陳腐化を監査する仕組みは存在しなかった
（rule-audit の削除テストは CLAUDE.md のルールのみが対象。knowledge は
@参照整合・孤立ファイル検出の補助入力にすぎなかった）。decisions には
決定が進化したときに旧 ADR へ印を付ける運用が無く、古い決定を現行と
誤読しうる状態だった（実例: 20260612-manual-copy が deploy_skills.py 導入後も
未修正で、「スクリプトは使わない方針」と読めた）。

チーム・中大規模開発では、鮮度不明のドキュメントは (1) 一度「古い」を踏んだ
読者が docs/ 全体を信用しなくなる、(2) トピック間の新旧方針の矛盾を AI が
等しく真として読む、(3)「誰がいつまで正しいと保証しているか」に答えられない、
という形で問題化する。

## Decision

規模に応じた段階基準で運用する。今は個人段階の機構のみ実装し、
上位段階は移行条件だけ決めておく:

| 段階 | 条件 | 管理方式 |
|---|---|---|
| **個人（現在）** | knowledge ≤ 10 本程度 | rule-audit 起動時に knowledge のトピックにも削除テストを適用し、鮮度シグナル（git 最終更新日・被参照数）を機械出力する。起動は手動 |
| チーム化 | 複数人が knowledge を書く | 各ファイルに owner と最終検証日を frontmatter で持たせ、鮮度チェックを CI 化する（この ADR を改訂） |
| 中大規模 | docs が製品の一部になる | 鮮度 SLA・レビュー必須・ドキュメント専任のオーナーシップ制 |

decisions は不変の記録として剪定しない。代わりに、決定を変更・進化させるときは
旧 ADR の Status を `Superseded by [新ADR]` または `Amended`（Amendments 節追記）に
して相互リンクする（knowledge-capture の ADR 手順に明記）。

## Rationale

- knowledge は compound / knowledge-capture が書き込みで触り続ける生きた文書のため、
  使われるトピックは自然に更新される。監査が要るのは「参照はされるが古い」記述と
  「使われなくなったトピック」で、前者は削除テスト、後者は鮮度シグナルで検出できる
- owner 制・SLA の今からの導入は予防的ハードニング（[20260706-no-custom-reviewer-agent](20260706-no-custom-reviewer-agent.md)
  と同じ理由で見送り）。チーム開発はまだ仮定であり、摩擦が実証されてから段階を上げる
- 段階の移行条件を今決めておけば、チーム化時に「なぜ最初から SLA にしなかったか」に
  この ADR で答えられる（配布方式の段階基準と同じパターン）

## Consequences

- Good: rule-audit を起動しさえすれば knowledge の腐敗が検出される（無管理ではなくなる）
- Bad: 起動は手動のまま — 定期性は人間の記憶に依存する（起動ナッジの hook 化は
  無料で可能だが、摩擦の実証待ちで見送り。必要になったら SessionStart hook に追加する）
- decisions は件数が増え続けるが、不変の判例集として意図的に受け入れる

## Alternatives considered

| Alternative | Reason rejected |
|-------------|-----------------|
| owner + 最終検証日を今から全ファイルに付ける | 個人開発では owner が常に自分で情報量ゼロ。frontmatter 維持の摩擦だけ残る |
| rule-audit を cron で定期実行 | スケジュール起動はセッション実行の課金が発生する。手動運用の摩擦が実証されてから再検討 |
| decisions も削除テストで剪定する | ADR は「その時点の判断の記録」であり、古さ自体に価値がある。剪定ではなく Superseded 印で対応 |

## Amendments

### 20260721 — Superseded / Amended 運用の担当スキルを `adr` に移した

[20260721-adr-as-master-only-skill](20260721-adr-as-master-only-skill.md) により、ADR の起票と
Superseded / Amended の印付けは master-only スキル `adr` の担当になった。本 ADR の
Decision 節にある「knowledge-capture の ADR 手順に明記」は、現在は `adr` スキルの Step 4 を指す。

**核は不変**: 段階基準による鮮度管理、decisions は剪定せず不変の記録として扱うこと、
決定の変更は Superseded / Amended 印と相互リンクで表すこと — いずれも変更していない。
変わったのはその運用を実行するスキルの所在のみ。

### 20260730 — Context の @参照配線主張を現行運用に合わせた

Context 冒頭が「CLAUDE.md の @参照などに行動に配線」と**現在形**で書いていたが、
現行は knowledge を必要時に読む運用（`@` 既定なし）である。該当文を過去形＋現行運用に置換した。

**核は不変**: 段階基準・decisions の不変記録・Superseded / Amended 印 — いずれも変更していない。
変わったのは配線モデルの記述のみ。rule-audit の `@docs/...` 参照切れ検出（consumer）は残す。
