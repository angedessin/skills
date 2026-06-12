# Claude Code Config — settings.json / hooks の実践知識

---

## deny ルールはツールごとに独立評価される

`Bash(...)` の deny は Bash ツールにしか効かない。秘匿ファイル保護は
**ファイルにアクセスできる全ツール分**（Bash / Read、必要なら Edit / Write）のルールを揃える。

```jsonc
// ❌ Bad: Bash だけ deny — Read ツールでは .env が読める
"deny": [
  "Bash(cat .env*)"
]

// ✅ Good: ツールごとに対で deny する
"deny": [
  "Bash(cat .env*)",
  "Read(./.env*)",
  "Read(./**/.env*)"
]
```

**glob はプレフィックス形とサフィックス形の両方を列挙する。**
`.env*` は `.env.local` にマッチするが、`prod.env` のようなサフィックス形には
マッチしない（実際にレビューで `Read(./**/*.env)` の欠落が検出された）。

```jsonc
// ✅ 両形を揃える
"Read(./.env*)",  "Read(./**/.env*)",   // .env, .env.local, ...
"Read(./*.env)",  "Read(./**/*.env)"    // prod.env, staging.env, ...
```

---

## hook スクリプトの堅牢化

**起動パスは `$CLAUDE_PROJECT_DIR` で絶対参照にする。**
相対パスは hook 実行時の CWD に依存し、サブディレクトリでのセッション等で silent fail する。

```jsonc
// ❌ Bad: CWD 依存
"command": "bash .claude/hooks/session-stop.sh"

// ✅ Good
"command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-stop.sh"
```

**成功メッセージはコマンドの成否と連結する。**
副作用（フラグ作成など）の成否を確認せずにメッセージを出すと、
失敗時に「やったつもり」の通知だけが残り、後続セッションのリマインドが消失する。

```bash
# ❌ Bad: touch が失敗してもリマインド成功と表示される
touch "$flag"
echo "次回セッションで knowledge-capture をリマインドします"

# ✅ Good: 成功した場合のみメッセージ
touch "$flag" && echo "次回セッションで knowledge-capture をリマインドします"
```

---

※ このファイルは開発が進むにつれ knowledge-capture / compound スキルによって更新される。
