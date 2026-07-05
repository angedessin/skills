# Design: lint-verification-loop

Created: 20260704
Status: **APPROVED**
Approved: 20260705（方針: まず作って動かし、細部は使いながらカスタマイズする）

## Goal

AI の編集を機械が自動検証し、失敗を AI 自身に返して自己修正させる「閉じたループ」を hook で作る。PostToolUse で編集ファイルの format + lint 自動修正、Stop で型チェックを行い、エラーを stderr 経由で AI に差し戻す。hook スクリプトは linter 自動検出（あれば使う、無ければ素通し）で書き、このリポジトリをマスターとする配布物にする。方針文書「AI駆動フロントエンド開発 設計方針」セクション 3 の実装第一弾。

## Scope

### In scope

- `post-edit-lint.sh`（PostToolUse: Edit/Write）— 編集されたファイルのみを対象に、配置先プロジェクトの設定を自動検出して実行:
  - `biome.json` / `biome.jsonc` があれば `biome check --write`（ts/tsx/js/jsx/json/css）
  - ESLint flat config（`eslint.config.*`）があれば `eslint --fix`（ts/tsx/js/jsx。Biome と併存する場合は Biome 優先）
  - Stylelint 設定（`stylelint.config.*` / `.stylelintrc*`）があれば `.scss/.css` に `stylelint --fix`
  - どの設定も無ければ何もせず exit 0
  - 自動修正で解消しない違反は exit 2 + stderr で AI に返す
- `stop-typecheck.sh`（Stop）— `tsconfig.json` があれば `tsc --noEmit --incremental` を実行。型エラーは exit 2 + stderr で差し戻す。`stop_hook_active` が true のときは差し戻さず警告のみで通す（無限ループガード）。`tsconfig.json` が無ければ即 exit 0
- `.claude/settings.json` への配線（PostToolUse matcher: `Edit|Write`、Stop は既存 `session-stop.sh` に追加する形の配列 2 本目）
- **このリポジトリのルートを一次検証環境にする**: ルートに `package.json` + `@biomejs/biome` + `biome.json` を常設し、hook を実配線して「Claude の編集 → lint 差し戻し → 自己修正」の連携をこのリポジトリ・このセッションで実際に動かす（マスター自身が動く実例になる）
- 型チェックループの検証: 一時的な `tsconfig.json` + TS ファイルで Stop 差し戻しを確認し、検証後に撤去（このリポジトリに恒常的な TS 資産はないため）
- 配布手順の記録: コピーするファイルと settings.json スニペットを docs/knowledge/claude-code-config.md に追記

### Out of scope

- reference `biome.json`（nextjs-starter ルールの移植版）の作成 → Open questions で要否を決めてから別タスク化も可
- markuplint の CI 層への導入（配置先プロジェクト側の作業。ドキュメントに言及のみ）
- 型情報 ESLint ルール（prefer-nullish-coalescing 等）の代替 → 捨てる判断済み（20260704 の議論）
- compound スキルへの「hook 化」出口追加（別途承認待ちの独立変更）
- CI 整備・pre-commit（husky/lint-staged）— 配置先プロジェクトの責務

## Constraints

- Stack: bash hook スクリプト + jq（hook stdin の JSON パース）。既存 `guard-env-read.sh` / `session-stop.sh` と同じ流儀で書く
- パッケージ実行は `pnpm exec` 前提（グローバルインストール・`npx -y` に依存しない）。ツール未インストール時はエラーにせずスキップ（配布先で Biome 未導入でも壊れない）
- このリポジトリのルートには現状 package.json が無い → 検証のためルートに `package.json`（private）+ `biome.json` を常設する。`pnpm add` は deny 設定のため依存導入はユーザー実行（`! pnpm add -D @biomejs/biome`）
- 恒常運用: Biome は常設（このリポジトリの JSON 等も対象になる）。tsconfig は検証後撤去し、`stop-typecheck.sh` はこのリポジトリでは no-op に戻る
- PostToolUse は編集のたびに走るため、対象拡張子以外は即 exit 0。タイムアウトを明示設定（lint: 30s 目安）
- Stop hook の tsc は実測で 20〜30 秒を超える配置先では CI に移す（20260704 の議論での合意閾値）
- スキル・hook ファイルに絵文字を使わない

## Acceptance criteria

- [ ] `post-edit-lint.sh`: Biome / ESLint / Stylelint を設定ファイルの存在で自動検出し、編集ファイルのみに実行。自動修正後も残る違反を exit 2 + stderr で返す。設定もツールも無いプロジェクトでは無音で exit 0
- [ ] 自動修正でファイルが書き換わった場合は「reformatted: [file]」相当の 1 行通知を AI に返す（無音の書き換えは AI のファイル状態を古くし、次の Edit 失敗を招くため。PostToolUse の JSON 出力 `additionalContext` を第一候補、不可なら exit 2 + 短い stderr）
- [ ] lint 出力は AI 向けの簡潔な形式に固定する（「ファイル:行:ルール:メッセージ」相当・カラー無効。装飾付きの人間向け出力を stderr に流さない）
- [ ] `stop-typecheck.sh`: tsconfig 検出時のみ `tsc --noEmit --incremental` を実行。`stop_hook_active` ガードで無限ループしない。tsconfig 無しでは無音で exit 0
- [ ] `.claude/settings.json` に両 hook が配線され、既存の PreToolUse / Stop hook と共存する
- [ ] Biome 設定の無いプロジェクトにコピーしても通常の編集・終了が一切阻害されない（自動検出の no-op 動作。設定ファイル一時退避で確認）
- [ ] ルートで検証: lint 違反を含む編集 → hook が stderr で差し戻し → AI が修正 → 通過、のループがこのリポジトリ・このセッションで実際に回る（Claude と lint の連携）
- [ ] 型エラーがある状態で Stop → 差し戻し → 修正 → 通過、が確認できる（ルートに一時 tsconfig + 一時 TS ファイルで検証し、確認後撤去）
- [ ] `bash -n` 全スクリプト通過。設定 JSON は `jq` でパース確認
- [ ] 配布手順（コピー対象ファイル + settings.json スニペット）が docs/knowledge/claude-code-config.md に記録されている

## Approach

hook は「配置先に何があるか」を実行時に検出する self-contained なスクリプトにする（スキルと同じ「あれば使う、無ければ無いなりに動く」原則 — これによりマスター配布物として任意のプロジェクトにコピーできる）。PostToolUse は hook stdin の JSON から `tool_input.file_path` を取り、そのファイルだけを処理して編集ごとの遅延を最小化する。ツール選定は Biome を第一候補とする（20260704 に採用決定: ホットループの速度が本質、決定は linter 自動検出により軽い＝後から oxlint 等へ移行可能）。型チェックはクロスファイル整合が必要なため編集ごとではなく Stop（終了宣言時）に置き、「誰がエラーを直すか」をセッション内の AI に保つ。hook の出力は AI が消費する前提で設計する: 自動修正による書き換えは 1 行通知で AI のファイル状態の不整合を防ぎ、違反メッセージは装飾のない簡潔な形式に固定してコンテキスト消費を抑える。

## Key components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| post-edit-lint.sh | `.claude/hooks/post-edit-lint.sh` | 編集ファイルの format+lint 自動修正と違反の差し戻し（linter 自動検出） |
| stop-typecheck.sh | `.claude/hooks/stop-typecheck.sh` | 終了宣言時の型チェックと差し戻し（無限ループガード付き） |
| settings.json | `.claude/settings.json` | hook 配線（PostToolUse: Edit\|Write / Stop: 2本目） |
| 配布手順 | `docs/knowledge/claude-code-config.md` | コピー対象・settings スニペット・閾値ルール（tsc 20-30s 超は CI 行き）の記録 |
| 検証環境 | リポジトリルート | `package.json` + `biome.json` を常設し hook を実配線（マスター自身が動く実例） |

## Data flow

```
[PostToolUse ループ（編集ごと）]
Edit/Write 実行
  → hook stdin JSON → jq で file_path 抽出
  → 拡張子・設定ファイル検出 → 該当ツールを pnpm exec で実行（--write / --fix）
  → 違反ゼロ・書き換えなし: exit 0（無音）
  → 違反ゼロ・自動修正で書き換えあり: 「reformatted: [file]」の 1 行通知のみ
  → 違反残り: exit 2 + stderr（簡潔形式） → AI にフィードバック → AI が修正 → 再び Edit → …

[Stop ループ（終了宣言時）]
AI が終了宣言
  → stop-typecheck.sh: stop_hook_active を確認
     → true: 警告を出して通す（ループガード）
     → false: tsconfig.json あり? → tsc --noEmit --incremental
        → エラー: exit 2 + stderr → AI が修正して再度終了へ
        → クリーン: exit 0 → session-stop.sh（既存）へ
```

## Test strategy

- Unit: 該当なし（bash スクリプト。`bash -n` + 可能なら shellcheck で静的確認）
- Integration: ルートでの実地検証 — (1) Biome 違反を含むファイルを編集し差し戻しループを観察、(2) 一時 tsconfig + 型エラー入り TS で終了宣言し Stop 差し戻しを観察、(3) 設定ファイルを一時退避して no-op（設定なしプロジェクト相当）を確認
- E2E: なし

## Open questions

承認時（20260705）に「まず作ってカスタマイズ」方針で以下の通り確定:

- [x] **ルートへの Biome 導入はユーザー実行が必要** → 検証フェーズで `! pnpm add -D @biomejs/biome typescript` を依頼する
- [x] **tsc の実測値** → 配置先ごとに配置時に計測する運用で確定（20〜30 秒超なら CI 行き）
- [x] **.scss の formatter** → stylelint --fix のみで開始。prettier 検出は必要になったら hook に追加
- [x] **reference biome.json** → このタスクでは作らない。ルートには最小構成の biome.json を置き、使いながら調整する

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| ESLint 続投（starter 構成の移植） | 編集ごとの実行に構造的に遅い。Next.js を剥がすと jsx-a11y / react-hooks 等の再組み立てコストも発生（20260704 調査） |
| oxlint + oxfmt | lint は最速だが formatter の実用化が最近で成熟度が Biome に劣る。linter 自動検出設計により将来の乗り換えは軽いため、今日は Biome |
| 型チェックを PostToolUse に置く | tsc はプロジェクト単位でしか型を解決できず、単一ファイル指定ではクロスファイルエラーを拾えない。フル実行は編集ごとには遅すぎる |
| 型チェックを CI のみに置く | エラーが PR に出る時点で修正者がコンテキストを失う（ループの外に漏れる）。CI は最後の砦として残す |
| lint-staged / husky の流用 | AI の編集はコミット前に走らないためループが閉じない。人間の commit 用としては配置先で併存可 |

## Research

- 採用状況調査（20260704）: npm 週間 DL は ESLint 1.37 億 / Biome 983 万 / oxlint 約 670 万。Biome 公式 Trusted by に AWS・Google・Vercel 等（ただしチーム単位採用の可能性）。国内 2026 年は RevComm（AI 用途で Oxc）・i-plug・ANDPAD など Oxc 側の事例が増加中 → 自動検出設計で乗り換えコストを下げておく根拠
- nextjs-starter（.tmp/nextjs-starter, develop）構成: ESLint flat + typescript-eslint strict + eslint-config-next 経由の jsx-a11y/react-hooks + stylelint（SCSS/CSS Modules）+ markuplint + prettier。型情報ルール 2 本（prefer-nullish-coalescing / prefer-optional-chain）は Biome に代替なし → 捨てる判断済み
- Claude Code hook 仕様: PostToolUse は stdin JSON の `tool_input.file_path`、exit 2 の stderr が AI へのフィードバックになる。Stop hook 入力には `stop_hook_active` があり、これを見ないと差し戻し無限ループが起きる

### 既存パターン調査（20260705）

- ヘッダコメント: 各 hook はファイル冒頭に「何を・なぜ」を日本語コメントで書く（guard-env-read.sh / session-stop.sh 共通）
- jq 依存の扱い: guard-env-read はフェイルクローズ（検査できなければ ask に落とす）。lint hook は品質ゲートでありセキュリティゲートではないため、jq / ツール不在時はフェイルオープン（素通し）とする
- プロジェクトルート解決: `$CLAUDE_PROJECT_DIR` を第一候補、`git rev-parse --show-toplevel` をフォールバックにする（session-stop.sh は git 方式。CWD 非依存にする）
- ツール実体は `node_modules/.bin/` の存在チェックで検出（`pnpm exec` の起動オーバーヘッドを毎編集で払わない）
- 注意点: biome に明示パスを渡すと ignore 対象ファイルでエラーになるため `--no-errors-on-unmatched` が必要。`tsc --incremental` は `*.tsbuildinfo` を生成するため .gitignore に追加する
