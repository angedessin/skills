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

---

## CLAUDE.md の @参照は毎セッション展開される

`@docs/knowledge/foo.md` 形式の参照は「必要なときに読む」ではなく、
**セッション開始時に毎回中身がコンテキストへ展開される**（skill-design-patterns.md で実測）。

- 常時読ませたい行動知識だけに `@` を付ける（コンテキスト固定費になる自覚を持つ）
- 「必要時に読む」を意図するならプレーンなパス表記にする
  （例: 「settings.json 作業時: docs/knowledge/claude-code-config.md を読む」）
- 参照切れの `@` は無害に無視される。事前に空ファイルを作る必要はないが、
  rule-audit の参照整合チェックで検出・掃除する

---

## headless（claude -p）でのスキル・ガードレール検証

配置先のスキル読み込み・permissions・hooks は `claude -p` で安価に検証できる（モデルは haiku で十分。20260703 の初回配置検証で実施）。

- **未信頼ワークスペースでは permissions.allow が無効化される**（deny / hooks は有効）。一度対話セッションを起動して信頼ダイアログを承認するか、`~/.claude.json` の `projects[<path>].hasTrustDialogAccepted: true` を設定してから検証する
- `--allowedTools` は可変長引数で**後続のプロンプトを引数として飲み込む** — `--allowedTools=Bash` の `=` 区切りで書く
- 非対話モードでは hook の `ask` 判定は deny に落ちる。「Bash を明示 allow した上で、対象コマンドだけが拒否されること」で hook の発火を確認できる
- 対照実験を必ず入れる: allow 済みコマンド（`git log` 等）が通ることを確認して「全拒否ではなくルール駆動のブロック」だと判別する
