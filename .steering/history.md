# 閉じたタスク

git 管理下のタスクはフォルダを消してある。中身は git の履歴から読む:
`git log --all --full-history --diff-filter=D --oneline -- .steering/<フォルダ名>/` で消したコミットを探し、
`git show <コミット>^:.steering/<フォルダ名>/design.md` で読む。
（feature ブランチの中で作って消したフォルダは、`--full-history` が無いと見つからない。squash merge でマージしてブランチを消すと、中身は残らない）
git 管理下でないタスクは、行に書いた `.steering/archived/` の下に移してある。

- 〜2026-10-05 刷新の前のタスク（旧 `.steering/archived/` のすべて） — 刷新で作業ツリーから消した。`git show pre-renewal-20261006:.steering/archived/<フォルダ名>/<ファイル>` で読む
- 2026-11-07 20261006-skillset-renewal — スキル一式をゼロベースで刷新し、評価で 8 本に絞った（PR #21・#22。旧い形でアーカイブしていたので、パスは `.steering/archived/20261006-skillset-renewal/`）
- 2026-11-15 20261110-skill-loop-fixes — テストを必須にする Stop のゲートと、レビューで形だけのテスト・テストの抜けを拾う仕組みを足した（PR #26・#27・#28・#29。統合用ブランチ feature/skill-loop-fixes から main へ）
- 2026-11-17 20261116-exemption-visibility — 足したテストの免除をレビューの報告と PR の本文に載せる（list-exemptions.sh を frontend-code-review と pr-create に置く）（PR #31）
- 2026-11-20 20261116-verify-tree-guard — 検証役の作業ツリーを見張る hook と、写しを作る make-copy.sh を足し、検証役が写しの中で再現するようにした（frontend-code-review 2.3）（PR #33）
- 2026-11-21 20261117-close-before-merge — タスクを閉じ忘れたまま統合ブランチへマージするのを防ぐ（pr-create の予告と閉じる確認・steering の閉じてよい状態・SessionStart の閉じ忘れの印）（PR #35）
