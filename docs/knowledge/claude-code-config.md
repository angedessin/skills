# Claude Code Config — settings.json / hooks の実践知識

---

## PreToolUse hook と permissions の評価順（公式 docs で確定・20260726）

一次情報: code.claude.com/docs/en/hooks

- **PreToolUse hook は permissions より先に評価される。** hook が沈黙（exit 0・出力なし）すると
  「通常の permission flow に進む」。したがって **hook は permissions の deny を救済できない**
  （`permissionDecision: "allow"` を返さない限り）
- **permissions に置く deny は「守りたい範囲の外にだけ当たる形」でなければならない。** Bash ルールは
  前置一致なので `Bash(rm -rf /*)` は `rm -rf /Users/<...>/<project>/.tmp` にも当たる。
  「プロジェクト内は通す」を hook で後から救えないため、deny の粒度を誤ると回復手段がない
- `permissionDecision` に指定できる値: `allow` / `deny` / `ask` / `defer`

## hook の入力 JSON には常にプロジェクト外の絶対パスが入る

PreToolUse の入力 JSON には共通フィールドとして `transcript_path`
（`/Users/<user>/.claude/projects/.../transcript.jsonl`）・`cwd`・`permission_mode` が入り、
Bash では `tool_input.description`（モデルが書く自然文）も入る。

**したがって全文検査でパス判定はできない** — 「プロジェクト外の絶対パスを検出する」という条件は
恒常的に真になる。パス判定は `tool_input.command` を構造抽出してから行う
（`grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | sed` で `jq` 非依存にできる。
`remind-config-docs.sh` に前例）。

**全文検査が正当なのは ask のときだけ。** 誤検知の代償が「確認 1 回」なら緩い検査で釣り合うが、
deny は回復不能なので構造抽出が要る。この不変条件は hook 本文のコメントに書いておく
（20260726 実測: 現行の全文検査 hook は発火 13/13・誤検知 0 だが、これは「`.env` を含むか」
「リダイレクト先が対象パスか」を見ているからで、パス判定を足した瞬間に成立しなくなる）。

## 配布する permissions はマスターの方針と分ける

マスターの permissions には「このリポジトリは依存を増やさない」のようなリポジトリ固有の方針が
混ざる。それを配置先に丸ごと配ると、**配置直後から `npm install` が拒否される**
（配置先に settings.json が無い場合、丸ごと新規作成されるため）。

**「配るものを列挙する」形にする。** 除外リスト方式は新ルールを足すたびに除外判断が要り、
判断し忘れが配置先を壊す方向（フェイルオープン）に倒れる。列挙方式なら足し忘れは
「配られない」方向に倒れる。両集合とマスターの突合を機械化して、分類漏れ・ドリフト・
死んだ分類を検出する。

最終的なセキュリティルールは**配布先に依存する**。配るものはベースラインとして扱い、
配置時に配布先の事情（社内方針・CI の制約・パッケージマネージャ）に合わせて調整する。
独立フォークが別ポリシーを持つのは食い違いではなく正しい差異なので、**その旨を配布物側に
明記する**（次に読む人が「漏れ」と誤認して緩めるのを防ぐ）。

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
「承認前の書き込みを機械で止める」目的で `Edit(./CLAUDE.md)` `Edit(./docs/knowledge/**)`
を ask に足したが、`allow` の `Bash(git show*)` が前置一致のため `git show X > CLAUDE.md` が
素通りした（Edit を経由しないので ask が発火しない）。`.env` 保護では Bash と Read を対に
しているのに、承認ゲートでは片側だけを書いていた。**ゲートしたいパスは、そこへ書けるツール全部を
塞ぐ**（Bash 側は PreToolUse hook で書き込みリダイレクトを検出する形になる）。
**ファイルパス規則は `Edit(path)` / `Read(path)` のみ** — `Write(path)` は受け付けられるが参照されず
起動時警告になる（`Edit` が Write / NotebookEdit 等を覆う。20260806 に死んだ Write 対を削除）。

**承認ゲートは書き込みと削除・移動で層が分かれる。** `guard-gated-write.sh` は書き込みリダイレクト
（`>` / `>>`）と `tee` を **ask**。`guard-gated-delete.sh` は素の `rm` / `mv` で対象パス
（`CLAUDE.md` / `docs/knowledge/` / `docs/decisions/`）を含むものを **deny**
（`tool_input.command` の構造抽出 — python3 stdlib。失敗・`&&` / `||` / `;` / `|` 連鎖 /
`bash -c` / `git rm` / `/bin/rm` は沈黙。改行区切りの複数単純コマンドは各行を判定し、
**deny は最大 1 JSON**（ヒットで即終了。複数行ヒット時の連結 JSON はフィクスチャの
厳密 parse と衝突する））。
permissions の粗い `rm -r*` / `rm -rf *` は別層。`sed -i` 等は脅威モデル外。
完全封鎖ではない。パスは 3 系統（ディレクトリ裸形も deny、`CLAUDE.md` は境界付き。AFTER にグロブ `*?[{`）。write と手同期。
**既知ギャップ（受容）**: heredoc 本文の行頭に `rm`/`mv`+保護パスがあると、実削除でなくても deny する
（改行ループの帰結。除外はシェルパーサ拡張＝別判断）。
検証: `mise exec -- pnpm run test:hooks`。PreToolUse の実効確認はセッション再起動後に人間が行う。
**フィクスチャ判定は壊 JSON を部分一致で deny/ask にしない** — `json.loads` 失敗は `unparseable:` に
倒して FAIL。runner 内自己テストで固定する（本番 hook からは壊 JSON を出せないため）。

**glob は形式を列挙する。** ディレクトリ配下を対象にするなら `docs/knowledge/*`（直下）・`**`・
`**/*`（入れ子）を並べる。単一形式では直下のファイルを取りこぼしうる（同じ轍を `Read(./**/*.env)`
の欠落で踏んでいる）。

**足したら実効性を実測する。** ただし **ask の発火は AI 側から観測できない**（セッションの権限
モードに上書きされうるため、プロンプトが出ないことがパターン不一致の証拠にならない）。
「書いたから効いている」と見なさない — 20260725 に、穴のあるゲートを効いていると誤認したまま
コミットした実例がある。

**観測の分担を決めてから測る。** `ask` のプロンプトは人間にしか見えず、`hook` の
`additionalContext` は AI にしか見えない。20260726 の確認は「AI がプローブを実行 → 人間に
プロンプトの有無を聞く」形にして初めて成立した。**AI が単独で「ゲートは効いている」と結論できる
のは additionalContext 系だけ**で、ask は必ず人間に聞く。

**セッション中に追加した hook が効くかは、イベント種別によって挙動が割れる（20260725 実測・未解明）。**
同一セッションで次の 3 つが同時に観測された:

| hook | 登録タイミング | 発火 |
|---|---|---|
| `PreToolUse(Bash)` の 1 本目（セッション開始時から存在） | 開始時 | **する** |
| `PreToolUse(Bash)` の追加分（配列 2 番目 / 独立 matcher の両方を試行） | セッション中 | **しない** |
| `PostToolUse(Edit\|Write)` の追加分 | セッション中 | **する（登録直後）** |

追加した PreToolUse hook はスクリプト単体では実ペイロードで正しく発火し、登録構造も正しかった。
つまり本体でも登録でもない要因が残っている。**PostToolUse が即座に効いた以上「設定が再読込
されない」では説明できない。**

**20260726 追試: セッション再起動後は発火した。** 同じ `guard-gated-write.sh` に対し
`echo test > docs/decisions/_probe.md` を実行してプロンプトが出ることを人間が確認した。あわせて
`ask` 側（`Edit(./docs/knowledge/*)`）も発火、`PostToolUse` の内容注入も両分岐で発火・
誤発火なし・セッション 1 回制限も期待どおりだった。したがって上表の「しない」は
**セッション中に追加した場合に限る現象**で、恒久的な不発ではない。原因自体は未解明のまま。

**同一 event+matcher を配列で分割しない（20260807）。** PreToolUse の `Bash` を
`guard-env-read` / `guard-gated-write` / `guard-gated-delete` の 3 エントリに分けると、
再起動後でも `/hooks` に delete が出ず deny が沈黙した（ファイルと settings の記述はある）。
**1 つの `matcher: "Bash"` エントリに hooks を並べる**（PostToolUse と同型）。
契約 (f) が同一 event+matcher の分割を検出する。deploy も同キーをマージしてから書く。

**運用ルール（変更なし）**: PreToolUse で新しいガードを足したら、**セッションを再起動してから
実効性を確認する**（下記「hook 変更はセッション開始時に読まれる」）。確認できるまでそのガードを
「機械的な防御」として数えない。

---

## 独立フォークへ防御を持ち出したときの教訓（20260726・過去形）

20260725 に master で High（セキュリティ）として塞いだ Bash 迂回路が、20260726 時点で
一方向持ち出し先（当時の `export/company`）では開いたままだった。`settings.example.json` の ask は
Edit / Write しか持たず、`guard-gated-write.sh` は同梱も登録もされていなかった。

原因は方針の適用範囲の取り違え。「master から同期・伝播しない独立フォーク」は**機能差分・スタック適応**
のための方針であり、防御の欠陥にそのまま適用してはいけなかった。にもかかわらず方針が一律に効き、
防御の修正だけを例外にする仕組みが無かった。気づいたのは偶然だった。

**現行義務（20260730 Frozen handoff 後）**: 会社向け持ち出しセットへの追随・パリティ確認は行わない
（`deployments.md` の Frozen 注記）。一般法則として残すのは次だけ — **settings.json / hooks の防御を
変えたら、その場で `deployments.md` に載っている個人配置先（還流あり）への影響を確認する。**
配置先が 0 件なら確認対象も 0。過去の持ち出し文書（HANDOVER 等）は日常改訂しない。

配布加工の注意（一般論）: 防御を同梱するときは、hook の理由文に含まれる非同梱スキル名を除去する
（残すと配置先で死んだ参照になる）。hook 本数・配置手順は同一コミットで揃える。

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

- `post-edit-lint.sh` はフェイルオープン（lint 設定・`node_modules/.bin/` が無ければ素通し）。`stop-typecheck.sh` は jq・tsconfig・tsc が無ければ素通し（jq を使うのは入力 JSON の `stop_hook_active` 判定）。未整備プロジェクトにコピーしても編集を阻害しない（lint / tsc は品質ゲートでありセキュリティゲートではない）
- **guard 系**（`guard-env-read` / `guard-gated-write` / `guard-gated-delete`）は jq 非依存。write/env は ask、delete は deny（抽出失敗は沈黙）
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
