# タスクリスト: スキルセット堅牢化

design.md: `.steering/20260725-skillset-hardening/design.md`

## 0. 変更対象の確定（実装の最初に行う）

design.md の「主要コンポーネント」は**暫定**。実装に入る前に、変更対象を表す語で全文検索して対象を機械的に洗い出し、表に挙げ漏れた箇所を潰す。

- [x] `grep -rn "@参照\|@docs/" --include="*.md" . | grep -v .steering/archived | grep -v docs/archive` で `@` の producer を全て洗い出す（`@docs/knowledge` だけの grep では `@参照` 表記を拾えない）
- [x] 洗い出した各ヒットを producer（`@` を書けと指示している）と consumer（参照切れ検出など）に仕分ける。修正対象は producer のみ
- [x] `grep -rn "9 個\|10 個\|9 スキル\|10 スキル" export/company/` でスキル数の記述箇所を洗い出す
- [x] `grep -rn "sys.argv" scripts/` で argparse 化が必要なスクリプトが check_deploy_drift.py 以外に無いか確認する
- [x] `.tmp/20260725-skillset-evaluation-8axes.md` の結論を `decisions.md` に転記する（`.tmp/` は git 追跡外のため根拠が消える）
- [x] 洗い出しの結果、design.md の表に無い箇所があれば design.md を先に更新する（実装してから直さない）

## 1. Phase 1 — export セットの出荷前検証

> 実行ディレクトリに注意: スクリプトの `MASTER_ROOT` は実行ファイルの位置から決まる。main 側の `scripts/` を使うか worktree 側を使うかで挙動が変わる。

- [x] `export/company/HANDOVER.md:9` の「9 個」→「10 個」
- [x] `export/company/MANIFEST.md` の冒頭に「スキル数の一次情報は `skills/` のディレクトリ数（機械カウント）」を明記する（13行目=10 と 54行目=9 の食い違いは、54行目が日付付き履歴節のため本文は残す）
- [x] `export/company/MIGRATION-GUIDE.md` 第2部の対応表がスキル10本と一致することを確認（全箇所 10 で整合済み・変更不要）
- [x] `scripts/check_export_stopcontract.py` を新規作成
  - [x] 停止契約領域の実質差分を report-only で報告（差分ありでも exit 0）
  - [x] **比較対象ディレクトリ不在時は exit 2 でフェイルクローズ**（main 実行時の偽グリーン防止・実測で確認）
  - [x] 比較対象パスを引数で明示指定できるようにする（`--export` / `--master`）
- [x] `README.md` の `scripts/` 資産一覧に `check_export_stopcontract.py` を追加（ツリーとインフラ節の両方）
- [x] 差分ガードを実行し、シナリオ対象を確定する → **2 本**（設計の 3 本から変更。`decisions.md` に根拠）
- [x] `.claude/skills/skill-test/SKILL.md` に export セットの検査手順を追記（`--all` が拾わない / export ブランチで `--all` を使うと master を検査して偽陽性 / 実行ディレクトリで対象が変わる / 対象選定は差分ガードに従う）。あわせて `--runs 4` の規律も Step 3 に反映（Phase 3 の項目を前倒し）
- [x] `export/company/tests/session-retrospective/scenario.md` を作成（CLAUDE.md に自律実行境界を**書かない**サンドボックス。**FAIL 想定**）
- [x] `export/company/tests/knowledge-capture/scenario.md` を作成（入力充実版・Angular / Jasmine・日本語見出し・Status は英語）
- [x] ~~`export/company/tests/compound/scenario.md`~~ — **見送り**（削除箇所が停止より後方の Step 4 内。差分ガードの実測による）
- [x] `--dry-run` で2本の構造確認（無課金）
- [x] **課金前にコスト（8 run）を提示して承認を得る**
- [x] 実走前に `session-retrospective` の停止をハードストップ化（main を先に修正 → export へ同型適用。B 案）
- [x] `--runs 4` で2本を実走 → `session-retrospective` **4/4 PASS** / `knowledge-capture` **3/4（run1 FAIL）**
- [x] agent output の tail を目視し、無出力 run が無いことを確認（全8 run で承認待ちの実体あり）
- [x] FAIL への対応 — 本文の締めは尽くされているため、`ask` 権限による機械の別防御を追加（`decisions.md` に根拠と留保）
- [x] ~~再実走~~ — 行わない。`ask` は `--permission-mode acceptEdits` のハーネスでは反映されない可能性が高く、測れないものに課金しない
- [x] `validate_skills.py <worktree>/export/company/skills` が 10/10 PASS

### 機械の別防御（FAIL 対応で追加）

- [x] `.claude/settings.json` の `ask` に `Edit/Write(./CLAUDE.md)` `Edit/Write(./docs/knowledge/**)` を追加
- [x] `export/company/claude-config/settings.example.json` にも同じ 4 行を追加（配布物側）
- [x] `README.md` の settings.json 説明を更新（片側修正の禁止）
- [x] `docs/starter-kit.md` 手順6 を更新（同上）
- [x] `export/company/MANIFEST.md` 手順3 を更新（同上）

## 2. Phase 2 — master の回帰シナリオ

- [x] Phase 1d の結果を踏まえてシナリオ設計方針を決める
- [x] **各シナリオの判定可能性を先に確認する** — `verdict()` は `before.get(k) != after[k]` で新規ファイル作成も検出することを確認（`passthrough_check.py`）
- [x] `tests/passthrough/impl-from-design/scenario.md` を作成 → **4/4 PASS**
- [x] `tests/passthrough/debug/scenario.md` を作成 → **3/4（run2 FAIL）**
- [x] `tests/passthrough/adr/scenario.md` を作成 → **3/4（run1 FAIL）**
- [x] ~~`tests/passthrough/frontend-code-review/scenario.md`~~ — **落とす**。承認語彙は2件のみで、停止は「合算 diff が空」という縮退入力ガードであって承認ゲートではない。かつ非 git サンドボックスでは意図した分岐に間接的にしか到達しない
- [x] ~~`tests/passthrough/feature-pipeline/scenario.md`~~ — **見送り**（判定不能）。ハーネス拡張を別タスクとして起票する
- [x] `--dry-run` で構造確認（無課金）
- [x] **課金前にコスト（12 run）を提示して承認を得る**
- [x] `--runs 4` で3本を実走
- [x] FAIL への対応 — 本文の改善では下がらないと判断（`decisions.md` の型別分析）。書き込み先が狭い `adr` は機械防御、広い `debug` は残存リスクとして受容
- [x] ~~再実走~~ — 行わない。n=4 では 3/4 と 4/4 に有意差を主張できず、効果を測れない

### FAIL 対応（Phase 2）

- [x] `.claude/settings.json` の `ask` に `Edit/Write(./docs/decisions/**)` を追加（`adr` の書き込み先を機械的にゲート）
- [x] `adr` の Step 3 にターン境界を追加（既定レシピとの一貫性のため。効果は未実証と明記）
- [x] `debug` の Step 5 にターン境界と「方針を書き終えた勢いで適用に流れやすい」の名指しを追加（同上）
- [x] `README.md` の settings.json 説明に `docs/decisions/**` を反映
- [x] 無回帰: `validate_skills.py` 29/29 PASS・`--portability` 混入0件・settings.json 妥当（ask 15件）

## 3. Phase 3 — 即効修正バンドル

### `@` 常時ロードの解消（producer を止める）

- [x] `CLAUDE.md:49` の `@` を外し、50行目と同じ書式に統一する
- [x] `CLAUDE.md:43` の保存先の表「（@参照で読む）」を条件付き記述に修正（**producer**）
- [x] `.claude/skills/knowledge-capture/SKILL.md` の出力テンプレをプレーンなパス表記に変更（**producer**。`@` は常時参照が要る場合の例外として注記）
- [x] `.claude/skills/compound/SKILL.md` の「`@参照` にする」を条件付きに（**producer**）
- [x] `.claude/skills/rule-audit/SKILL.md` の2箇所を条件付きに（**producer**。参照切れ検出は consumer なので変更せず）
- [x] `templates/SKILL.template.md` の冒頭コメントを強化（`@` 除去で失われる導線の代替。読まずに書くと落とす規律まで明記）
- [x] producer が残っていないことを grep で確認（残るヒットは consumer・条件付き・経緯説明のみ）

### その他

- [x] `.claude/skills/skill-test/SKILL.md` を `--runs 4`（承認ゲート系）に修正 — **Phase 1 で前倒し実施済み**
- [x] `package.json` に `validate` / `validate:portability` / `check:export` を追加
- [x] `scripts/check_deploy_drift.py` を argparse 化し、`--help` バグを解消する
- [x] argparse 化の前後で既存2経路（引数なしのレジストリ全件 / 配置先パス直指定）が動くことを確認
- [x] `scripts/validate_skills.py` に `--help` / `-h` で docstring を表示する分岐を足す（最小修正。全面 argparse 化はしない）
- [x] `validate_skills.py` の既存6経路（引数なし / `<dir>` / `--skill` / `--template` / `--purity` / `--portability`）が壊れていないことを確認
- [x] `.claude/skills/steering/SKILL.md` の status / resume に `.steering/` 不在時の動作を追記（勝手に作らない旨も明記）
- [x] `.claude/skills/frontend-code-review/SKILL.md` に `compatibility:` を追加（選定基準は design.md 参照）
- [x] `.claude/skills/impl-from-design/SKILL.md` に `compatibility:` を追加
- [x] `README.md` の資産一覧に argparse 化・npm script・差分ガードの自動発見を反映
- [x] 個別検証: `--help` 3本とも exit 0 で使用法を表示 / `@` producer が grep で消えている
- [ ] ~~`pnpm validate` が通る~~ — **pnpm のバイナリが壊れており実行不能**（`pnpm --version` も同じエラー。このタスクと無関係な環境問題。`blockers.md` に記録）。package.json の妥当性と各コマンドの直接実行は確認済み
- [x] 無回帰: `validate_skills.py` 29/29 PASS・`--portability` 混入0件・`--template` PASS

### Phase 3 で追加した改善（設計に無かったもの）

- [x] `check_export_stopcontract.py` に git worktree からの自動発見を追加 — npm script 化にあたり、持ち出しセットのパスが環境依存で `package.json` に固定で書けないため。フェイルクローズは維持（発見できなければ exit 2）

## 4. Phase 4 — 別タスクへ切り出し（20260725 に撤退条件を発動）

**本タスクでは実施しない。** Phase 1〜3 完了時点で配置先が未定だったため、design.md の撤退条件に従って分離した。以下の未チェック項目は**次タスクの起票内容**としてそのまま残す（7. に起票タスクを置いた）。

- [ ] 配置先プロジェクトを決める
- [ ] 配布するスキルセットを決める（最小に限定せず**拡張セットも候補**とし、配布先の要件に合わせて選ぶ。`session-retrospective` は必須 — 還流の producer）
- [ ] `deployments.md` のコメント行の実在しないパスを実態に修正する（記録の正確さ。機構の修復ではない）
- [ ] `skill-deploy` を起動し、dry-run 提示まで進める
- [ ] **dry-run の内容を確認し、承認してから配置を実行する**（リポジトリ外への書き込み）
- [ ] 配置先に既存の settings.json がある場合、手動マージ案を確認して人がマージする
- [ ] スモークテスト: 「どのスキルが使える？」で配置スキルが一覧に出る
- [ ] スモークテスト: 小さなタスク依頼で design-doc が承認待ちで停止する
- [ ] スモークテスト: 小さな diff に対してレビューが実行される（レビュー系を配置した場合）
- [ ] スモークテスト: `head .env.local` が ask に落ちる（`cat .env` では検証にならない）
- [ ] スモークテスト: **配置先の通常コマンド（依存インストール・テスト実行）が阻害されていない**（settings.json 新規作成時に deny が丸ごと入るため）
- [ ] スモークテスト: 対話セッションを起動して信頼ダイアログを承認する
- [ ] `check_deploy_drift.py` を実配置先に対して実行し、3分類 + hooks 差分 + skill-issues 収集が動くことを確認
- [ ] `skill-harvest` を1周させ、還流レポートが出ることを確認（配置直後は差分ゼロが正常）
- [ ] 実走で詰まった箇所を `docs/starter-kit.md` の手順に反映する
- [ ] 同じ内容を `.claude/skills/skill-deploy/SKILL.md` に反映する（starter-kit と同一コミット）
- [ ] `adr` で「配布機構を維持し実走で実証する」決定を起票する（却下案: 縮退B・還流系のみ撤去）
- [ ] 既存 ADR 20260612 との関係（補足 / 改訂 / 独立）を `adr` の近縁検出結果を見て決める
- [ ] `decisions.md` に「配置先 N 件を登録した」と記録する（`deployments.md` は git 追跡外のため証跡が残らない）
- [ ] 無回帰: `validate_skills.py` 全 PASS・`--portability` 混入0件

## 5. レビュー（**未完 — ここから再開**）

- [x] コードレビューを試行 → **並列フルモードが 3 エージェントともセッション上限で中断・所見ゼロ**。自己レビューで代替
- [x] レビュー結果を `review-result.md` に記録（Status: **OPEN**）
- [x] 自己レビューの指摘 2 件に対応（`ask` の glob 3 形式化 / `normalize()` の契約値破壊）→ コミット `1c34091`
- [x] **フレッシュエージェントで再レビュー**（範囲 `HEAD~5..HEAD`）→ **3 体とも完走。自己レビューが見落としていた High が 3 件**
- [x] High 3 件に対応: Bash 迂回を塞ぐ hook 新設 / 差分ガードの master 側フェイルクローズ / `STOP_VOCAB` の取りこぼし解消
- [x] Medium 2 件に対応: コミットに混入した検証ゴミ 2 ファイルを削除 / `design.md` の陳腐化した記述を訂正
- [x] 残り Medium 5 / Low 4 / Info 2 の対応方針を決定 → **次タスクへ送る**（理由は `review-result.md` の「Status を DEFERRED にした理由」）
- [x] `review-result.md` の Status を **DEFERRED** に更新
- [ ] （次タスクの先頭・**要セッション再起動**）hook の実効性確認 — `echo test > docs/knowledge/_probe.md` で確認が出るか。出なければ Phase 1・2 の機械防御の結論を撤回する

## 6. デプロイ

- [x] main へコミット（Phase 単位で分ける）
- [x] export worktree へ main をマージし、`export/company/` 側の整合を確認する
- [x] export ブランチでの運用ルール（`--all` を使わない・検査対象を明示指定）を `export/company/MANIFEST.md` に追記する
- [x] merge 時に `check:export`（差分ガード）を実行する運用を MANIFEST に書く

## 7. 福利化・知見保存

- [x] `knowledge-capture` で知見を保存する（案1〜4 を docs/knowledge/ へ書き込み。案5 は compound へ申し送り = skill-issues.md に起票）
- [x] `compound` でルール・スキルへの昇格を検討する（5 件昇格。`codify-log.md` に記録）
- [x] 次タスクを起票する（`.steering/` は作らずバックログとして `decisions.md` に記録。理由も同ファイル）:
  - **(a) レビュー積み残しの解消（最優先）** — 先頭に「hook の実効性確認（要セッション再起動）」。以下 `review-result.md` の DEFERRED 分: `validate_skills.py` の未知フラグ Traceback / `--verbose` の仕様不一致 / `[:120]` 切り詰めで差分が読めない / 非同梱スキル名の語境界 / `read_body()` の型注釈 / `.test.tsx` の `STACK_WORDS` 欠落 / `--master` 不在時の誤誘導文言 / 配布物の `docs/decisions/` ask 欠落 / global CLAUDE.md と `.claude/skills/**` が ask の射程外
  - **(b) 配布機構の初回実走** — Phase 4 の切り出し。配置先が決まってから。上の 4. の項目がそのまま内容
  - **(c) 構造改善** — 依存表・README セットアップ節・knowledge 剪定・ドキュメント↔実装のズレ検知
  - **(d) `passthrough_check.py` のハーネス拡張** — `## setup` 節・git init。feature-pipeline の Gate 3.5 を判定可能にする
- [x] `steering` の archive モードでこのタスクをアーカイブする

Archived: 20260725

> 未チェックで残した 23 項目は、やり残しではなく行き先が決まっているもの: Phase 4（20 件）は配置先未定のため撤退条件で切り出し、hook の実効性確認（1 件）はセッション再起動が必要、`pnpm validate`（1 件）は pnpm のバイナリ破損で実行不能。いずれも `decisions.md` のバックログまたは `blockers.md` に記録済み。
