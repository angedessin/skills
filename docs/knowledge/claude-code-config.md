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

**この規律は deny だけでなく `ask`（承認ゲート）にも同じく適用される。** 20260725 に
「承認前の書き込みを機械で止める」目的で `Edit/Write(./CLAUDE.md)` `Edit/Write(./docs/knowledge/**)`
を ask に足したが、`allow` の `Bash(git show*)` が前置一致のため `git show X > CLAUDE.md` が
素通りした（Edit/Write を経由しないので ask が発火しない）。`.env` 保護では Bash と Read を対に
しているのに、承認ゲートでは片側だけを書いていた。**ゲートしたいパスは、そこへ書けるツール全部を
塞ぐ**（Bash 側は PreToolUse hook で書き込みリダイレクトを検出する形になる）。

**glob は形式を列挙する。** ディレクトリ配下を対象にするなら `docs/knowledge/*`（直下）・`**`・
`**/*`（入れ子）を並べる。単一形式では直下のファイルを取りこぼしうる（同じ轍を `Read(./**/*.env)`
の欠落で踏んでいる）。

**足したら実効性を実測する。** ただし **ask の発火は AI 側から観測できない**（セッションの権限
モードに上書きされうるため、プロンプトが出ないことがパターン不一致の証拠にならない）。
「書いたから効いている」と見なさない — 20260725 に、穴のあるゲートを効いていると誤認したまま
コミットした実例がある。

**セッション中に追加した hook が効くかは、イベント種別によって挙動が割れる（20260725 実測・未解明）。**
同一セッションで次の 3 つが同時に観測された:

| hook | 登録タイミング | 発火 |
|---|---|---|
| `PreToolUse(Bash)` の 1 本目（セッション開始時から存在） | 開始時 | **する** |
| `PreToolUse(Bash)` の追加分（配列 2 番目 / 独立 matcher の両方を試行） | セッション中 | **しない** |
| `PostToolUse(Edit\|Write)` の追加分 | セッション中 | **する（登録直後）** |

追加した PreToolUse hook はスクリプト単体では実ペイロードで正しく発火し、登録構造も正しかった。
つまり本体でも登録でもない要因が残っている。**PostToolUse が即座に効いた以上「設定が再読込
されない」では説明できない。** 原因未特定のため、**PreToolUse で新しいガードを足したら、
セッションを再起動してから実効性を確認する**（下記「hook 変更はセッション開始時に読まれる」）。
確認できるまでそのガードを「機械的な防御」として数えない。

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

**hook の出力は AI が消費する前提で設計する。**
lint 検証ループの実装（20260705）で確立した 2 原則:

- **無音の自動修正をしない**: hook がファイルを書き換えたら「reformatted: [file]」の 1 行を `additionalContext`（PostToolUse の JSON 出力）で AI に返す。無音の書き換えは AI のファイル状態の記憶を古くし、次の Edit の old_string 不一致（二次被害）を招く
- **人間向けの装飾出力を AI に流さない**: 進捗バー・罫線・カラー・サマリはコンテキストの浪費。診断行（ファイル:行:ルール:メッセージ）だけを grep で抽出して stderr に返す。診断行ゼロの失敗（設定エラー等）のみ生出力にフォールバック

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
