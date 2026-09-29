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
Claude Code（2.1.283）もリダイレクト先を検査するが、見るのは Edit の allow / deny・保護パス・作業ディレクトリで
**ask は見ない** — acceptEdits で `git show HEAD:a > CLAUDE.md` が `Edit(./CLAUDE.md)` の ask をすり抜けて
上書きされた（20260927 headless 実測。`tee` は止まった）。組み込み検査があっても hook は外せない。
**ファイルパス規則は `Edit(path)` / `Read(path)` のみ** — `Write(path)` は受け付けられるが参照されず
起動時警告になる（`Edit` が Write / NotebookEdit 等を覆う。20260806 に死んだ Write 対を削除）。

**承認ゲートは書き込みと削除・移動で層が分かれる。** `guard-gated-write.sh` はリダイレクト・`tee`・`git mv` を
**ask**（対象は hook 冒頭の `# GATED_PATHS:` 行 = permissions.ask の Edit 対象。契約 (s) が突合）、
`guard-gated-delete.sh` は素の `rm` / `mv` で `CLAUDE.md` / `docs/knowledge/` / `docs/decisions/` を含むものを
**deny** する（意図的に 3 系統）。どちらも完全封鎖ではない（`bash -c`・`git rm`・`sed -i`・cd 後の相対パスは沈黙）。
判定仕様の正本は hook 本体とフィクスチャ（`mise exec -- pnpm run test:hooks`）で、ここに写さない。

**allow に git の読み取り系を書かない（組み込みの読み取り専用判定を上書きする）。** Claude Code には
組み込みの読み取り専用コマンド判定があり、git の読み取り形は allow 無しでもプロンプトなしで動く。
しかも `--output=<file>`・`difftool -x '<cmd>'`・`--ext-diff`・作業ツリー外のパス（`--no-index` を書かない
`git diff /dev/null ../x` も含む）は止める（default / acceptEdits で実測）。ところが `Bash(git diff*)` のような
前置一致の allow を書くと、この判定より先に allow が当たり、それらが**無音で通る**（`difftool -x 'touch pwned'` が
実行された。20260927 headless 実測）。「読み取りだから allow してよい」は逆効果で、allow が穴の原因になる。
契約 (t) が settings / `DEPLOY_PERMISSIONS` の allow に git が入るのを落とす。

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
のは additionalContext 系だけ**で、ask は必ず人間に聞く。ただし headless（`claude -p`）では ask が拒否に
落ち、ブロック理由（hook の reason を含む）がモデルに返るので、下の「headless での検証」節の手順なら AI が機械的に判定できる。

**人間確認のプローブは、hook だけが守るパスで作る（20260927）。** `.claude/` は Claude Code 組み込みの保護パスでも止まるので、
プロンプトが出ても hook の証拠にならない。`docs/knowledge/zz-probe.md` のような、hook だけが守るパスを使う。
プロンプトを拒否するとターンが中断されるので、プローブは 1 回の依頼につき 1 つにする。

**セッション中に追加した hook が効くかはイベント種別で割れる** — PreToolUse の追加分は発火せず、PostToolUse の
追加分は即時に効いた（原因は未解明）。セッション再起動後は発火する（20260725-26 実測）。

**同一 event+matcher を配列で分割しない（20260807）。** PreToolUse の `Bash` を
`guard-env-read` / `guard-gated-write` / `guard-gated-delete` の 3 エントリに分けると、
再起動後でも `/hooks` に delete が出ず deny が沈黙した（ファイルと settings の記述はある）。
**1 つの `matcher: "Bash"` エントリに hooks を並べる**（PostToolUse と同型）。
契約 (f) が同一 event+matcher の分割を検出する。deploy も同キーをマージしてから書く。

**運用ルール（変更なし）**: PreToolUse で新しいガードを足したら、**セッションを再起動してから
実効性を確認する**（下記「hook 変更はセッション開始時に読まれる」）。確認できるまでそのガードを
「機械的な防御」として数えない。

---

## 独立フォークにも防御は追随させる

会社向け持ち出しセット（`export/company` ブランチ）は **2026-09-29 に保守を終了した**。ブランチはローカルと origin に
凍結して残してあり、worktree は外した。保守手順の正本だった `export/COMPANY-MAINTENANCE.md` も、そのブランチに残っている。
今後、独立フォークや持ち出しセットを作るときは、次の教訓を使う。

- **同梱スキルの顔ぶれ・スタック語彙などの機能判断はマスターに合わせなくてよいが、hooks / settings / 停止契約の防御は
  マスターを上流として追随させる**。「独立フォークだから同期しない」は機能差分のための方針で、防御の欠陥には適用しない
  （20260726 に master で塞いだ Bash 迂回路が、持ち出し先で開いたままだった実例がある）
- 防御を変えたら、その場でフォーク側と配置先（`deployments.md`）に同じ穴が無いかを見る
- 配布加工の注意: 防御を同梱するときは、hook の理由文に含まれる非同梱スキル名を除去する（配置先で死んだ参照になる）

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

**コマンドを構造で判定する guard は、次の 3 つを取りこぼしやすい（20260929 レビューで実測）。**

- 作業ディレクトリを変えるオプション: `git -C <dir> mv a b` は、オペランドだけを見ても対象パスが現れない。`-C` の値と合成してから照合する
- 前置ラッパー: `env FOO=1 tee X` / `exec git mv ...` / `sudo tee X`。先頭トークンでコマンドを判定するなら、ラッパーと、値を取るオプション（`env -u NAME`・`sudo -u USER`）を読み飛ばす
- 大文字小文字: macOS の既定のファイルシステムは大文字小文字を区別しないので、`> CLAUDE.MD` でも実ファイルが書き換わる。パスの照合は大文字小文字を区別しない（ask なら誤検知の代償は小さい）

---

## lint 検証ループ hook の配布（post-edit-lint / stop-typecheck）

AI の編集を機械が検証して差し戻す「閉じたループ」の配布物（`post-edit-lint.sh` / `stop-typecheck.sh`）。
同送と settings 登録は `deploy_skills.py` が行い、手順は `docs/starter-kit.md`。ここには配置時の判断材料だけを置く。

**配置時の注意:**

- `post-edit-lint.sh` はフェイルオープン（lint 設定・`node_modules/.bin/` が無ければ素通し）。`stop-typecheck.sh` は jq・tsconfig・tsc が無ければ素通し（jq を使うのは入力 JSON の `stop_hook_active` 判定）。未整備プロジェクトにコピーしても編集を阻害しない（lint / tsc は品質ゲートでありセキュリティゲートではない）
- **guard 系**（`guard-env-read` / `guard-gated-write` / `guard-gated-delete`）は jq 非依存。write/env は ask、delete は deny。write / delete の JSON 抽出は python3 標準ライブラリ — python3 不在・抽出失敗時、write は全文 grep（`.claude/` 系を除く 3 系統）に縮退し、delete は沈黙する。**縮退中の write は `.claude/settings*.json` / `.claude/hooks/` と `git mv` を守らない**（6 系統中 3 系統。`.claude/` を全文で見ると transcript_path と恒常的に衝突するため）。`.claude/` 系を Bash から守るのは python3 がある環境だけ — 配置先では `python3 --version` を確認する
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
- **permission 自体の挙動を測るときは、ユーザー設定と未信頼の問題を外す**（20260927）: scratchpad の使い捨てリポジトリで
  `--setting-sources project,local`（ユーザー設定の allow / hooks を外す）を付け、allow は `--allowedTools`、ask / hooks は
  `--settings '<json>'` で与える（未信頼のワークスペースでは project の allow が警告付きで無視される）。プロンプトは
  `--` の後ろに置けば `--allowedTools` に飲み込まれない。モデルは判定に影響しないので haiku でよく、`--max-budget-usd` で上限を付ける。
  結果は必ずファイルの有無など副作用で裏取りする（モデルの自己申告だけにしない）

---

## サブエージェント定義（`.claude/agents/`）の落とし穴

- **`tools` に `Bash(git diff *)` と書いても読み取り専用にならない。** `--output=<path>` で任意ファイルへ書け、
  `git difftool -x '<cmd>'` で任意コマンドを実行でき、`git diff --no-index /dev/null <file>` で `Read` の deny を迂回して読める。
  読み取り専用の定義は `Read` / `Grep` / `Glob` のみにし、diff は呼び出し側がファイルで渡す。
  `settings.json` の allow を前置一致（`Bash(git diff*)`）で書いた場合も同じ穴になる（20260921 実測）。
  settings 側は allow から git を外せば組み込みの判定が塞ぐ（上の「allow に git の読み取り系を書かない」）
- **作成直後の定義は数ターン種別として未登録**（`Agent type '<name>' not found`。再起動不要で後から登録される）。
  フォールバックは「定義ファイルがあるか」ではなく「指定して失敗したら汎用エージェントへ落とす」まで書く
- **散文の「Haiku 相当で」「安価なモデルで」は subagent 起動に何の効果も持たない。** model / effort / tools は定義の
  frontmatter に書いたときだけ効く（ADR 20260927-subagent-roles-in-agent-definitions）
