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

## lint 検証ループ hook の配布（post-edit-lint / stop-typecheck）

AI の編集を機械が検証して差し戻す「閉じたループ」の配布物（20260704-lint-verification-loop で作成・検証済み）。
このリポジトリがマスター。配置先で直接編集せず、改善はマスターに還元して再コピーで配る。

**コピーするファイル（2 本）:**

- `.claude/hooks/post-edit-lint.sh` — Edit/Write のたびに編集ファイルだけを lint。Biome（`biome.json(c)`）→ ESLint（`eslint.config.*`、Biome 不在時のみ）→ Stylelint（scss/css）を自動検出。自動修正で残る違反を exit 2 + stderr で AI に差し戻す
- `.claude/hooks/stop-typecheck.sh` — 終了宣言時に `tsc --noEmit --incremental`（`tsconfig.json` がある場合のみ）。`stop_hook_active` ガード付き

**settings.json スニペット:**

```jsonc
"hooks": {
  "PostToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [
        { "type": "command", "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-edit-lint.sh", "timeout": 30 }
      ]
    }
  ],
  "Stop": [
    {
      "hooks": [
        { "type": "command", "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/stop-typecheck.sh", "timeout": 120 }
      ]
    }
  ]
}
```

**配置時の注意:**

- 両 hook はフェイルオープン設計: jq・設定ファイル・`node_modules/.bin/` のツールが無ければ無音で素通し。未整備プロジェクトにコピーしても編集を阻害しない（lint は品質ゲートでありセキュリティゲートではないため。guard 系 hook のフェイルクローズとは方針が逆）
- 配置時に `time pnpm exec tsc --noEmit --incremental` の 2 回目（キャッシュ有効）を計測し、**20〜30 秒を超えるプロジェクトでは stop-typecheck を settings.json から外して CI に移す**（終了のたびに待たされる体感悪化がループの利益を上回る）
- `tsc --incremental` は `*.tsbuildinfo` を生成する — .gitignore に追加する
- ツール検出は `node_modules/.bin/` の存在チェック（pnpm 起動オーバーヘッドを毎編集で払わない）。依存をルート以外に置くモノレポでは検出されない
- settings.json の hook 変更はセッション開始時に読まれる — 配線後は `/hooks` で確認するかセッションを再起動してから検証する
- **Stop hook はツール呼び出しでは発火しない — 応答を終えて初めて発火する。** 検証時にセットアップ（一時ファイル作成等）の後にツール呼び出しを重ねても発火条件を満たさない。意図的に検証する場合は、セットアップを済ませたらそこで応答を終える必要がある（20260705 実測: 誤ってツール呼び出しを挟み続け、発火しないと誤診断しかけた）

---

## headless（claude -p）でのスキル・ガードレール検証

配置先のスキル読み込み・permissions・hooks は `claude -p` で安価に検証できる（モデルは haiku で十分。20260703 の初回配置検証で実施）。

- **未信頼ワークスペースでは permissions.allow が無効化される**（deny / hooks は有効）。一度対話セッションを起動して信頼ダイアログを承認するか、`~/.claude.json` の `projects[<path>].hasTrustDialogAccepted: true` を設定してから検証する
- `--allowedTools` は可変長引数で**後続のプロンプトを引数として飲み込む** — `--allowedTools=Bash` の `=` 区切りで書く
- 非対話モードでは hook の `ask` 判定は deny に落ちる。「Bash を明示 allow した上で、対象コマンドだけが拒否されること」で hook の発火を確認できる
- 対照実験を必ず入れる: allow 済みコマンド（`git log` 等）が通ることを確認して「全拒否ではなくルール駆動のブロック」だと判別する
