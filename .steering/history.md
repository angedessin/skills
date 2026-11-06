# 閉じたタスク

フォルダは消してある。中身は git の履歴から読む:
`git log --diff-filter=D --oneline -- .steering/<フォルダ名>/` で消したコミットを探し、
`git show <コミット>^:.steering/<フォルダ名>/design.md` で読む。

- 〜2026-10-05 刷新の前のタスク（旧 `.steering/archived/` のすべて） — 刷新で作業ツリーから消した。`git show pre-renewal-20261006:.steering/archived/<フォルダ名>/<ファイル>` で読む
- 2026-11-07 20261006-skillset-renewal — スキル一式をゼロベースで刷新し、評価で 8 本に絞った（PR #21・#22。旧い形でアーカイブしていたので、パスは `.steering/archived/20261006-skillset-renewal/`）
