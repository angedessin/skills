# pr-feedback commands — GitHub / gh CLI + git（カートリッジ）

SKILL.md 本文の各 Step に対応する具体コマンド。別ホスト（GitLab 等）に配置する場合はこのファイルを差し替える（本文の手順はそのまま使える）。マスターの pr-create/references/commands.md と重複するコマンドがあっても、各スキルの自己完結性を優先して各自が持つ（配布単位がスキルフォルダのため）。

## §0 前提チェック — 対象 PR の特定

```bash
# PR ホスト（GitHub）の CLI が使えるか
command -v gh >/dev/null 2>&1 && gh auth status 2>/dev/null

# リモートの有無
git remote -v

# 現在ブランチに紐づく PR（番号・状態）
gh pr view --json number,state,url 2>/dev/null

# 引数で PR 番号が渡された場合はそれを使う
gh pr view <番号> --json number,state,url
```

- gh が無い / 未認証 → 手動でコメント・CI を確認する手順を案内して停止。
- リモートなし → PR 運用ではない。pr-create の Step 0 を案内して停止。
- 紐づく PR なし → 未提出。pr-create を案内して停止。

## §1 収集 — コメント・レビュー状態・CI 失敗

```bash
# レビューコメント（全体レビュー本文 + 状態）
gh pr view <番号> --json reviews,comments

# インラインのレビューコメント（ファイル・行つき）
gh api repos/{owner}/{repo}/pulls/<番号>/comments \
  --jq '.[] | {path, line, user: .user.login, body}'

# CI チェックの一覧（失敗ジョブの特定）
gh pr checks <番号>

# 失敗ジョブのログ要点（run id は gh pr checks / gh run list から）
gh run view <run-id> --log-failed
```

取得結果がすべてゼロなら「未対応のフィードバックはありません」と報告して終了。

## §4 修正適用（差分確認）

```bash
git status --short
git diff                    # 修正差分の確認
```

frontend-code-review が無い場合のセルフチェックはこの diff を基に本文 Step 4 の観点で行う。

## §5 外向き操作（本文 Step 5 の承認後にのみ実行）

```bash
# 修正をコミット（メッセージ規約はハーネスの指示に従う。トレーラ文言は焼き込まない）
git add -A
git commit -m "<種別>: <要点>

<ハーネス規約の末尾トレーラ>"

# プッシュ（既存のトピックブランチへ）
git push

# 各レビューコメントへの返信（インラインコメントへの返信）
gh api repos/{owner}/{repo}/pulls/<番号>/comments/<comment-id>/replies \
  -f body="<返信文>"

# PR 全体へのコメント返信
gh pr comment <番号> --body "<返信文>"

# flaky / インフラ起因の CI 再実行（外向き — 承認範囲に含める）
gh run rerun <run-id> --failed
```

**マージ（gh pr merge）はこのスキルでは実行しない** — 人間の判断（pr-create と同じ契約）。
