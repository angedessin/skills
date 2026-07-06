# pr-create commands — GitHub / gh CLI + git（カートリッジ）

SKILL.md 本文の各 Step に対応する具体コマンド。別ホスト（GitLab 等）に配置する場合はこのファイルを差し替える（本文の手順はそのまま使える）。

## §0 前提チェック — 運用とリモートの判定

```bash
# リモートの有無
git remote -v

# PR ホスト（GitHub）の CLI が使えるか
command -v gh >/dev/null 2>&1 && gh auth status 2>/dev/null

# デフォルトブランチ名（origin の HEAD が指す先）
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##'
```

- リモートなし → PR 作成不可。ローカルのコミット手順のみ案内して停止。
- gh が無い / 未認証 → プッシュまで行い、Web で PR を作る手順（§4 の比較 URL）を案内。

## §1 コミット状態の確認・確定

```bash
git status --short          # 未コミットの変更
git diff                    # 未ステージ差分
git diff --staged           # ステージ済み差分
```

コミットするときは、ハーネス規約のコミットメッセージ規約に従う（種別プレフィックス + 末尾トレーラ）。トレーラの正確な文言は実行環境の指示に従うこと（ここに固定文言を焼き込まない — ドリフト防止）。

```bash
git add -A
git commit -m "<種別>: <要点>

<本文>

<ハーネス規約の末尾トレーラ>"
```

## §2 ブランチ衛生

```bash
git branch --show-current   # 現在ブランチ

# デフォルトブランチ上なら、トピックブランチを切ってから進む
git switch -c <feature-branch-name>
```

## §3 ベース差分・履歴（PR 本文の材料）

```bash
# ベースブランチを origin/main に置き換えて使う
git log --oneline origin/main..HEAD     # このブランチのコミット
git diff --stat origin/main...HEAD      # 変更ファイルの俯瞰
git diff origin/main...HEAD             # 全差分
```

## §4 プッシュと PR 作成（外向き — 本文 Step 4 の承認後にのみ実行）

```bash
# トピックブランチをプッシュ（初回は上流を設定）
git push -u origin HEAD

# gh がある場合: PR 作成
gh pr create --base <base> --head <feature-branch-name> \
  --title "<title>" --body "<body>"

# gh が無い / 未認証の場合: プッシュ後、この比較 URL を案内して Web で作成してもらう
#   https://github.com/<owner>/<repo>/compare/<base>...<feature-branch-name>?expand=1
```

PR 本文末尾のハーネス標準の生成トレーラは、実行環境（Claude Code 等）の規約に従って付す。文言はここに固定せず、実行時の指示から取る。

## §5 CI 追跡（gh がある場合）

```bash
gh pr checks            # このブランチの PR の CI 状態
gh pr view --web        # ブラウザで PR を開く
```

CI 失敗の修正はこのスキルの外（実装/レビュー担当へ差し戻す）。**マージ（gh pr merge）はこのスキルでは実行しない** — 人間の判断。
