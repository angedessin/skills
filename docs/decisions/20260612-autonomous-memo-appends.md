# Decision: タスク内メモの追記を承認不要にし、自律実行の判断基準を定める

Date: 20260612
Status: Accepted

## Context

ワークフローの可動部品には性質の異なる2種類がある。
承認ゲート（design.md APPROVED・compound の昇格承認）は忘れると作業が止まるため劣化しない。
一方、`.steering/[task]/decisions.md`・`skill-issues.md` への手動追記は、書き忘れても
何も起きず無音で壊れる（compound / knowledge-capture への入力が痩せ細る）。
さらに compound には「昇格候補ゼロでもフラグ削除に承認を要求する」形式的な承認があった。

## Decision

- `.steering/[task]/` 配下のメモ（decisions.md・skill-issues.md・blockers.md）への追記は承認不要とする。内容の取捨選択は compound / knowledge-capture 時にまとめて行う
- compound の昇格候補ゼロ時のフラグ整理（.codify-needed 削除・codify-log.md 追記）は承認不要とする
- CLAUDE.md・SKILL.md・docs/ への書き込みは承認制を維持する
- 自律実行の判断基準: (1) git で巻き戻せる (2) 失敗に気づける (3) 影響がタスク内に閉じる — 3つ全て満たす操作のみ承認なしで実行してよい

## Rationale

- メモは間違っていても後段のレビューで捨てられる（巻き戻し可能・タスク内に閉じる）。書き込み時の承認は摩擦だけが残り、書き忘れという無音の故障を増やす
- CLAUDE.md・SKILL.md は全将来セッションの挙動を変える（条件3が No）ため、検証ハーネス（昇格の git ブランチレビュー化・参照整合の自動チェック・empirical-prompt-tuning による回帰確認）が整うまで承認制を外さない

## Consequences

- Good: 記録の取りこぼしが減り、compound / knowledge-capture への入力の質が上がる
- Good: 価値のない形式的承認が消える
- Bad: メモの質は書き込み時に担保されない（後段レビューに依存）
- 将来: ハーネス整備後に CLAUDE.md / SKILL.md 書き換えの自律化を再検討できる

## Alternatives considered

| Alternative | Reason rejected |
|-------------|-----------------|
| すべて承認制のまま維持 | 書き忘れ（無音の故障）が解消されない。承認ゲートと記録規律の問題を混同している |
| CLAUDE.md / SKILL.md 書き換えも即自律化 | 影響がタスク内に閉じず、検証ハーネスなしでは失敗に気づけない |
