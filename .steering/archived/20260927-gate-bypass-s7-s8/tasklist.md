# タスクリスト: gate-bypass-s7-s8

Last updated: 20260929（レビュー対応）

## 0. 変更対象の確定

- [x] 全文を検索して、主要コンポーネント表に漏れが無いか確定した（20260927。会社側の HANDOVER.md:99 / MANIFEST.md:60,73-74 を追加。export/company ブランチのルートにあるマスターのスナップショットは対象外）

## 1. 実測

- [x] git の略記・フラグなしの no-index・引数を分けた形（20260927）
- [x] 公式 docs の裏取り（組み込みの読み取り専用判定・ラッパー・ask の適用範囲・リダイレクト検査）
- [x] headless の A〜D（allow の有無・acceptEdits・リダイレクトと ask）→ 方針転換
- [x] 配置先の settings.local.json を確認した（skill-test は無し。hospital-search-mock は対象外）

## 2. マスター実装（承認制パスは個別に承認を取る）

- [x] フィクスチャを先に追加する（Red）。runner に、マーカー行からのケース自動生成・hook ディレクトリを差し替える引数・PATH を差し替えるケースを足す
- [x] `guard-gated-write.sh` を scratchpad のコピーで実装する（shlex で連鎖の全部分を判定・対象パス 6 系統・`git mv`・python3 が無いときの縮退・最大 1 JSON）。`bash -n` とフィクスチャを通してから差し替える（Green）
- [x] `guard-gated-delete.sh` のヘッダを「意図的に 3 系統」に書き換える
- [x] `.claude/settings.json` の allow から git の 4 件を削除する
- [x] `DEPLOY_PERMISSIONS` を同期し、hook の依存コメントを更新する
- [x] 契約 (s)（パス集合）と (t)（git の allow の禁止）を追加し、`tests/assets/run.py` に変異ケースを入れる。README の契約一覧と変異テストの記述を更新する
- [x] README / starter-kit（スモークテストの手順 8 を含む）/ claude-code-config を更新する（headless での測り方も）
- [x] `test:hooks` / `validate:assets` / `tests/assets/run.py` / lint を通す

## 3. 確認

- [x] headless での機械確認（hook は `--settings` で登録・acceptEdits・haiku）。結果を decisions.md に残す
- [x] 人間確認（再起動後・1 回。decisions 参照）: acceptEdits で `git show HEAD:README.md > .claude/hooks/zz-probe.txt` にプロンプトが出る（人間は拒否する）。`git diff` / `git log --oneline -3` はプロンプトなし。差分の書き出しで摩擦が出ないかも見る

## 4. export/company

- [x] settings.example.json: git の allow 4 件と、死んだ Write 規則 10 件を削除し、`_comment` を直す
- [x] hook を変換レシピどおりに同期する
- [x] HANDOVER / MANIFEST（依存・スモークテスト・変更履歴の再マージ告知）を直す
- [x] 会社側の hook に全フィクスチャを通す。静的検査 1〜6 を通し、export/company ブランチにコミットする

## 5. 配置先

- [x] 現状を取得し、差分を提示して承認を得た（hospital-search-mock はユーザー指示で対象外。decisions 参照）
- [x] skill-test に反映した（git の allow の削除・PreToolUse の 1 グループ化・write hook の差し替え・delete hook の追加）
- [x] 配置先の settings.json を JSON で読んで `Bash(git` が無いことを確かめ、`check_deploy_drift.py` で hooks が OK

## レビュー

- [x] コードレビュー（hook と scripts の差分。security の観点を含む）（20260929。frontend-code-review フル・4 エージェント。review-result.md）
- [x] レビュー指摘の修正（review-result.md を参照）（20260929。write hook の 3 件をフィクスチャ先行で修正し、export/company に同期。テスト・契約の Low を修正。delete hook の Low 2 件は BACKLOG §0.6）
- [x] ~~修正後の差分再レビュー~~ → 省略（20260929 ユーザー判断。代替はフィクスチャ 100/100・Red 10 件の確認）
- [x] ~~export/company の変更を export/company ブランチにコミットする~~ → 不要（20260929 に export/company の保守を終了。同期は破棄し worktree を撤去 — decisions 参照）

## 知見保存

- [x] knowledge-capture（組み込みの読み取り専用判定と allow の上書き・リダイレクト検査が ask を見ないこと・headless で permission を測る手順）（20260929 最終 capture。3 テーマは実装中に保存済みで重複。新規 3 件: guard の取りこぼし 3 類型・人間確認プローブの選び方・Bash なしレビュー役の High は再現してから受け取る）
- [x] `git status --short` で確認したうえで main へコミットする（アーカイブ後のコミットで実施）

## デプロイ

PR: none
CI: none
Feedback: no

Archived: 20260929
