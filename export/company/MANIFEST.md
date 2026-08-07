# 持ち出しセット — 会社ワークフロー用

**この文書が配置手順の一次情報。** 他の 2 文書（HANDOVER / MIGRATION-GUIDE）と食い違ったら、ここが正。

> **配置作業をする場合は「配置先（会社）でやること」から読んでよい。** 前半（このセットの中身・除外理由）は判断のための背景で、手順ではない。
> 末尾の「変更履歴」は**過去の経緯であって現在の仕様ではない** — hook の本数・スキル数・設定値は、必ずこの上部か実物（`ls skills/` 等）で確認する。

## このセットの現在の中身（2026-08-07 時点）

| 項目 | 値 | 実物での確認方法 |
|---|---|---|
| 同梱スキル | **10**（design-doc / design-premortem / steering / impl-from-design / tdd / knowledge-capture / compound / session-retrospective / rule-audit / debug） | `ls skills/` |
| 同梱 hook | **6**（session-start-check / session-stop / guard-gated-delete / guard-env-read / guard-gated-write / post-edit-lint） | `ls claude-config/hooks/` |
| 追加インストール | **不要**。ただし `guard-gated-delete.sh` のみ **python3**（標準ライブラリ）を要求し、無ければ黙って無効化される | `python3 --version` |
| 対象スタック | Angular / TypeScript / Jasmine | — |
| `design.md` の Status | `DRAFT` / `SPIKE` / `APPROVED` の **3 値**（英語のまま扱う契約値） | — |
| コードレビュー | **同梱なし**（会社のレビュープラグインを使う） | — |
| 由来 | マスターコミット `e02a95da5e73049be07cc501e0cfd34d179b9277`。10 スキルすべて同一 | 各 SKILL.md の `metadata.source-commit` |

**検証の状態**:

- 静的検査は全通過 — 非同梱スキル名 0 件 / 個人スタック語彙 0 件 / `tdd/references/patterns.md` 不在 / スキル数 10 / hook 実体 6 本 ≡ `settings.example.json` の登録 ≡ 本文書
- 停止契約の実地検証 — **knowledge-capture は 4/4 PASS**（2026-08-07、現在の本文に対しフレッシュエージェントで実行）。session-retrospective は本文が前回検証時と完全一致のため再実行していない。その他 8 スキルは実地検証を行っていない（静的検査のみ）

**Angular 適用版であること**: マスターは React / Vitest 前提で書かれており、このセットはスタック語彙と MR 運用に置き換えてある（tdd の本文・スコープを Angular / Jasmine 向けに書き換え、React 前提のコード例を集めた `references/patterns.md` は同梱から外した — 下の「同梱しなかったもの」参照）。**スキル本文に React / Vitest / pnpm 等の個人スタック語彙は 1 件も残っていない**（機械確認済み）。

## 会社ワークフローとの対応

| 会社のワークフロー | 同梱スキル |
|---|---|
| 1. 計画 | design-doc / design-premortem / steering |
| 2. テスト計画、実装 | impl-from-design |
| 3. テスト実装 | tdd |
| 4. レビュー、テストレビュー | **同梱なし**（会社のレビュープラグインを使う） |
| 5. 知見記録 | knowledge-capture / compound |
| （横断）バグ・障害の原因調査（再現→仮説→切り分け→根本原因→修正方針） | debug |
| （横断）摩擦の起票（会社内の改善ループ用） | session-retrospective |
| （定期）ルール・知識の剪定（compound と両輪） | rule-audit |

## 同梱しなかったもの（必要なら後から追加）

- **レビュー系 8 スキル（frontend-code-review / impl-review / test-review / review-a11y / review-correctness / review-performance / review-security / review-ui）** — 会社のレビュープラグインを使う方針のため除外。方針が変わったらマスターから追加コピーする（その際は残るスキルの「コードレビューを実施する」等の一般記述をスキル名に戻すか、そのままにするか判断する）
- **feature-pipeline** — レビューフェーズを含むオーケストレーターだったため、レビュー系の除外に伴って外した。工程は各スキルを順に使う（design-doc → impl-from-design → knowledge-capture / compound）
- **tdd の `references/patterns.md`（カートリッジ）** — 中身が React / Vitest / RTL / MSW / Jotai / pnpm の 272 行で、Angular / Jasmine の本文と矛盾していた（`§hook` は React Hooks 専用で Angular に対応物が無いため、本文の §名リストからも削除した）。誤ったスタックのコード例を持ち込む害が、雛形としての価値を上回るため削除。**tdd は無くても動く**（本文の判断軸は言語非依存で、スキル側にフォールバックを明記済み）。作る場合は下の「配置先（会社）でやること」手順 4 に従う
- **pr-create / pr-feedback** — PR（MR）運用は会社の既存プロセスとの整合を確認してから。これらのスキル名への参照は本文から全廃済み（debug は 2026-07-23 に同梱へ変更）
- **e2e** — 会社では E2E テストを行っていないため除外。各スキル本文・references・設計テンプレに残っていた `e2e` スキルへの参照と Playwright の例も除去済み（「E2E は対象外」という境界の記述のみ残している）。導入することになったらマスターから追加コピーする
- **impl-tournament** — N 並列実装で課金が大きい。必要になったら個別判断
- **adr** — 設計判断を ADR 形式（Context / Decision / Rationale / Consequences / Alternatives）で起票するマスター専用スキル。会社側の決定記録の様式が分からないため同梱しない。同梱の knowledge-capture は「決定・理由・却下した代替案」の 3 点を `.steering/[task]/decisions.md` に残すところまでを担当し、様式の決定は会社側に委ねる
- **skill-deploy / skill-harvest / skill-test / empirical-prompt-tuning / security-audit** — マスター専用またはメタ運用ツール（rule-audit は 2026-07-15 に同梱へ変更 — compound で増えるルール・知識を独立運用のまま剪定できるようにするため）

## 配置先（会社）でやること

1. `.claude/skills/` に `skills/` 配下のディレクトリをそのままコピーする
2. **hooks を配置する** — `claude-config/hooks/` の **6 本**を配置先の `.claude/hooks/` にコピーする。settings.json のコマンド登録は `"$CLAUDE_PROJECT_DIR"` 起点の相対参照なので、同じ配置ならパスの書き換えは不要
   - `session-start-check.sh`（SessionStart）: 未処理フラグ・アクティブタスク・rule-audit 月次ナッジをセッション開始時に注入
   - `session-stop.sh`（Stop）: `.capture-needed` を立てて knowledge-capture の起動を促す
   - `guard-gated-delete.sh`（PreToolUse）: `CLAUDE.md` / `docs/knowledge/` / `docs/decisions/` への素の `rm` / `mv` を **deny** する。削除・移動は書き込みゲートの迂回と等価なため。**python3 に依存する**（下記）
   - `guard-env-read.sh`（PreToolUse）: deny の前置一致をすり抜ける .env 読み取りを全文検査で ask に落とす
   - `guard-gated-write.sh`（PreToolUse）: 同じ 3 パスへの **Bash 経由**の書き込み（`>` / `>>` / `tee`）を ask に落とす。permissions の ask は Edit 規則（Edit/Write 双方を覆う）にしか掛からず、`Bash(git show*)` のような前置一致 allow があると `git show X > CLAUDE.md` で迂回できるため、その穴を塞ぐ
   - `post-edit-lint.sh`（PostToolUse）: 編集ごとの lint 差し戻し（Biome / ESLint / Stylelint を自動検出）。**フェイルオープン**（lint 設定が無ければ素通し）なのでスタックを問わず置いてよい

   **PreToolUse(Bash) の 3 本は 1 つの matcher にまとめて登録する。** matcher を分けて並べると
   後段の hook が実行されない。`settings.example.json` はまとめた形になっているので、
   手動マージのときに分割し直さないこと。

   **PreToolUse の hook はセッション再起動後に効く。** 配置したセッション中は発火しない場合があるため、
   置いた直後に「効いていない」と判断しない。確認するときは Claude Code を再起動してから
   `echo test > docs/knowledge/_probe.md` を AI に実行させ、確認プロンプトが出るかを**人間が**見る
   （ask の発火は AI 側からは観測できない）。確認できたら `_probe.md` を削除する。

   **前提ツールの追加インストールは不要。ただし `guard-gated-delete.sh` だけ python3 を要求する。**
   - 6 本中 5 本（`session-start-check` / `session-stop` / `guard-env-read` / `guard-gated-write` /
     `post-edit-lint`）は `grep` / `sed` / `find` など POSIX 標準のユーティリティだけで動く。
     Claude Code は hook に JSON を標準入力で渡すが、JSON 解析器（`jq` 等）には依存しない設計にしてある
   - `guard-gated-delete.sh` は Bash コマンドを構造として取り出す必要があるため **python3 に依存する**
     （標準ライブラリのみ。`jq` 等の追加パッケージは不要）。**python3 が無い環境、または JSON 抽出に
     失敗した場合は沈黙して素通りする（フェイルオープン）** — ゲートが無効になっても警告は出ない。
     deny に倒すと通常の Bash が広く死ぬためこの設計にしている
   - **配置後に `python3 --version` が通ることを人間が確認すること。** 通らない環境では削除ゲートが
     無い前提で運用する（`rm docs/knowledge/x.md` が素通りする）
3. **settings をマージする** — `claude-config/settings.example.json` を配置先の `.claude/settings.json` に**手動マージ**する（丸ごと上書きしない）。既存の allow と deny が同じ操作で衝突したら **deny を優先**（安全側）。マスターとの差分として **npx は全面 deny** に強化済み（下の「npx 禁止」参照）。また **`CLAUDE.md` / `docs/knowledge/**` / `docs/decisions/**` への書き込みを ask** にしてある — knowledge-capture は本文のハードストップで「承認前に書き込まない」を担保しているが、締めを尽くした状態でも承認前の書き込みが 1/4 の頻度で再現した実測があるため、機械的な最後の防波堤を置いている。**これらの ask エントリは外さないことを推奨する。** ask だけでは Bash のリダイレクトで迂回できるので、`guard-gated-write.sh`（PreToolUse）と**対で**維持すること — 片方だけでは防波堤にならない
4. **tdd のカートリッジを作る（任意・配置先の AI に依頼する）** — tdd は「エンジン（本文の判断軸）＋カートリッジ（`references/patterns.md` のスタック固有例）」構成だが、**カートリッジは同梱していない**（元は React / Vitest / RTL / MSW 前提の中身で、Angular / Jasmine の本文と矛盾し、誤ったコード例を持ち込む害の方が大きいため削除した）。**無いままでも tdd は動く** — 本文の判断軸は言語非依存で、スキル側にその旨のフォールバックが書いてある。具体例を効かせたければ、配置先で AI に実際のテスト環境（Jasmine の実行基盤・TestBed の使い方・既存 spec の慣習）を調べさせてから作成を依頼する
   - 見出しは本文が参照する §名にする: `§run`（実行コマンド）/ `§config`（ランナー設定）/ `§setup`（共通セットアップ）/ `§unit` / `§component` / `§query-ladder`（クエリ優先順位）/ `§network`（ネットワークモック）/ `§state` / `§api-layer` / `§coverage`。Angular に対応物が無い節は省いてよい
   - 依頼例:「このプロジェクトの実際のテスト構成を確認して、`.claude/skills/tdd/references/patterns.md` を Jasmine / TestBed 向けに新規作成して。見出しは SKILL.md が参照する §名に合わせる。SKILL.md 本文は変更しない。npx は使わない」
5. **CLAUDE.md に発動ポリシー節を作る**（下の雛形を貼って調整）
6. **`.gitignore` に 3 行追加**: `.steering/**/.capture-needed` / `.steering/**/.codify-needed` / `.steering/**/capture_done`
7. **`.npmrc` に `ignore-scripts=true` を設定**（install 時の postinstall 実行＝サプライチェーン攻撃の主経路を既定で遮断）
8. **一度対話セッションを起動して信頼ダイアログを承認する** — 未信頼のワークスペースでは settings.json の permissions.allow が無効化される（deny / hooks は有効）
9. **スモークテスト**（各項目、期待どおりでなければ FAIL として報告する）:
   - 「どのスキルが使える？」→ 配置した 10 スキルが一覧に出る
   - 小さなタスクを依頼 → design-doc が設計提示後に**承認待ちで停止する**（勝手に実装が始まったら FAIL）
   - `.claude/hooks/` を編集 → settings の `ask` により確認が出る（hook 登録が効いていることの確認）
   - `head .env.local` の実行を依頼 → 確認（ask）に落ちる。**`cat .env` で試さない** — それは
     settings の deny だけで止まるため、hook が動いていなくても同じ結果になり検証にならない
     （`head` は deny の前置一致をすり抜けるので hook しか止められない）
   - **削除ゲート**（python3 がある環境のみ）: `docs/knowledge/_probe.md` を作ってから
     `rm docs/knowledge/_probe.md` の実行を依頼 → **拒否（deny）される**。素通りしたら
     `guard-gated-delete.sh` が効いていない（`python3 --version` を再確認する）
10. 気づいた不具合・誤発動は `.steering/[task]/skill-issues.md` に起票する（session-retrospective が拾う）。改善は**会社リポジトリ内で直接スキルを編集してよい**（下の「独立運用」参照 — このセットは還流経路を持たないため、通常の「配置先で直接編集しない」ルールは適用しない）

### npx 禁止（このセットの方針）

**npx は使わない**（未導入バイナリだとレジストリ取得→即実行が走るため）。settings.example.json で
`Bash(npx)` / `Bash(npx *)` / `Bash(npm exec *)` を deny 済み。references を npm プロジェクト向けに
再生成するときも npx へ置き換えず、**ローカル導入済みバイナリを `./node_modules/.bin/<bin>` の直接実行
または package.json の scripts（`npm run <script>`）経由で呼ぶ**よう指定する。

### マスターから同梱しなかった hook

- `validate-skill-edit.sh` — マスター専用（`scripts/validate_skills.py` に依存。スキル編集の機械検証はマスターで行う）
- `stop-typecheck.sh`（Stop: 終了宣言時の `tsc --noEmit`）— Angular では**テンプレートの型エラーを検出できない**（テンプレートの型チェックは Angular コンパイラの担当で、素の tsc は `.ts` しか見ない）ためカバー範囲が中途半端で、CI と IDE の型チェックと重複する。加えて大きめのコードベースでは実行が 20-30 秒を超え、終了のたびに待たされる。型チェックは CI に任せる方針で除外した
- `remind-config-docs.sh`（PostToolUse）— マスターの `docs/knowledge/claude-code-config.md` を読むよう促す hook。そのドキュメントを同梱していないため、配置先では存在しないファイルを指す案内になる

## CLAUDE.md 雛形（発動ポリシー節）

```markdown
## スキル発動ポリシー

- 新しいタスクを開始するときは design-doc を使う。1 セッション完結の見込みなら会話内設計・複数セッションなら .steering/（どちらにするかは design-doc がユーザーに確認する）。いずれも設計の承認までは実装しない
- 承認済み design.md からの実装は impl-from-design を使う（実装モードは TDD 推奨）
- 既存コードへのテスト追加・テストファーストの実装は tdd を使う
- 実装後のコードレビュー（実装コード・テストコードの両方）は、このスキルセットではなく会社のレビュープラグインを使う。結果を残す場合は `.steering/[task]/review-result.md` に置くと knowledge-capture / compound が入力として読む
- **MR の作成・CI 確認・マージを進めるスキルは無い**（意図的に含めていない）。`tasklist.md` の「デプロイ」節を人がチェックする
- セッションで得た知見は knowledge-capture で docs/ に保存し、ルール・スキルへの昇格は compound を使う
- 設計・アーキテクチャの決定は `.steering/[task]/decisions.md` に「決定・理由・却下した代替案」で残す。チームの決定記録様式に上げるかは人が判断する（スキルは様式を生成しない）
- セッション終盤に session-retrospective で摩擦を .steering/[task]/skill-issues.md に起票する
- worktree・ブランチ上で開始したタスクは、main へのマージ前に .steering/ のアーカイブまで済ませる（.steering/ がブランチ間で分岐すると、他のセッションからタスクが見えない・アーカイブ済みがアクティブに見える等の対応漏れが起きる）
- CLAUDE.md・docs/knowledge/ が肥大化したと感じたら rule-audit で剪定する（compound 数回ごと・月 1 目安。適用は承認制）
```

## 独立運用（還流なし）のルール

会社環境からマスターへ情報を持ち帰る経路はない（セキュリティ制約）。この配置は**一方向**（マスター → 会社のみ）であり、持ち込み後の会社コピーは**独立したフォーク**として運用する:

- **スキルの改善は会社リポジトリで直接編集する**。skill-issues.md（session-retrospective が起票）は会社内の改善ループの入力として使う（マスターへの供給ではなく、会社内で完結する自己改善の材料）
- **編集したら目印を残す**: 編集したスキルの frontmatter `metadata:` に `modified: "YYYY-MM-DD 変更概要"` を追記する。`source-commit` は消さない（持ち込み時点の基準として残す）
- **例外: スキルの停止契約は独自に書き換えない。** 「承認前に書き込まない」「提示したらここで止まる」等のハードストップは、素通り事例を何度も潰して固めた部分で、その正本はマスター側にある。不備を見つけたら本文を書き換えず `.steering/[task]/skill-issues.md` に起票する
- **マスターから再持ち込みする場合は丸ごと上書きしない**: `modified` の付いたスキルは会社側の変更を優先し、必要な差分だけ手動マージする（再持ち込みの予定が無ければこの 2 つは無視してよい — 持ち込み後は会社側で育てるのが既定）

---

## 変更履歴（経緯の参考 — 現在の仕様ではない）

> **ここから下は過去の経緯。** 各項目に書かれている hook の本数・スキル数・設定値は**その時点の値**であり、現在の値ではない。現在の値は冒頭の表か実物で確認すること。残しているのは「なぜこれを外したのか / なぜこの防御があるのか」を後から追えるようにするため。

**2026-08-07 — マスター本文の再同期**

docs / hooks だけ新しくスキル本文が古い状態を解消。同梱 10 スキルの本文をマスター `e02a95d` から再同期し、会社向け変換を再適用した。

- 会社側 `metadata.modified` が指す停止契約強化 6 件をマスターと全文突合した結果、**マスターに無い会社独自の停止契約はゼロ**（いずれもマスター由来の逆輸入で取り込み済み。debug と rule-audit はマスターの方が強い）。`modified` を全廃し `source-commit` を統一した
- この同期で新たに入った停止契約・仕組み: `design.md` の `SPIKE` Status / 契約コアと付録の境界マーカー / steering archive の knowledge-capture ハードストップ / `.capture-needed` の三択契約（今・後で・スキップ）/ rule-audit の月次ナッジ / debug のターン境界停止 / compound の 3 節追加（配置元の直接編集禁止・provenance 一般化・昇格後の既存違反ゼロ）/ knowledge-capture の `blockers.md` 入力源
- `@docs/knowledge/` 参照をプレーンなパス表記に変更（`@` は毎セッション全文が展開される固定費で、「必要なトピック作業時のみ」という見出しと矛盾するため）
- `guard-gated-delete.sh` を追加し、`rm` / `mv` による承認ゲート迂回を塞いだ
- PreToolUse(Bash) の hook 登録を 1 matcher に統合した — **matcher を分けると後段の hook が実行されない**（それまで `guard-gated-write` が実質死んでいた）
- 除去済みスクリプト `check_export_stopcontract.py` を指す実行手順を削除した

**2026-07-26 — 承認ゲートの穴を塞ぐ**

- `guard-gated-write.sh` を追加。`permissions.ask` はファイル編集ツールにしか掛からず、`allow` に `Bash(git show*)` のような前置一致ルールがあると `git show HEAD:x > CLAUDE.md` が素通りし、**ask が一度も発火しないまま承認制のファイルが書き換わる**。PreToolUse(Bash) で `>` / `>>` / `tee` を検出して ask に落とす
- `docs/decisions/` を ask に追加。glob は `*` / `**` / `**/*` の 3 形式を並べる（単一形式では直下のファイルを取りこぼす）
- **ask と hook は対で維持する**（片方だけでは防波堤にならない）。この時点では削除（`rm`）は非対象だったが、2026-08-07 に `guard-gated-delete.sh` で塞いだ。`sed -i`・任意インタプリタ経由は現在も非対象

**2026-07-23 — debug の追加と敵対レビュー対応**

- debug を同梱。会社のバグ対応テンプレートが「再現手順」「根本原因」の記入を求めるのに、調査を担うスキルが無かったため
- tdd 本文から別スタック固有の API を除去 — `queryBy*` + `.not.toBeInTheDocument()`（Testing Library）・`includeSource`（Vitest 専用）・`§hook`（React Hooks）が残っており、**Jasmine では実行できないテストを書かせる**状態だった
- テストファイル命名の片側修正を解消 — tdd は `*.spec.ts`、impl-from-design は `Foo.test.[ext]` と食い違い、**テストランナーに収集されず「1 件も実行されないまま緑」になる**危険があった。両方を「既存テストを 1 つ開いて命名規則を確認してから作る」に統一
- 福利化ループの断線を修復 — `.codify-needed` を立てる主体（レビュー系スキル）を外したまま読み手だけ残り、**compound が二度と自動提案されない**状態だった。生成を knowledge-capture の最終 Step に移設
- hook の jq 依存を全廃 — **社内端末に jq を入れさせる前提が現実的でない**と判断。`guard-env-read` は JSON を構造として解釈せず全文検査する方式に変更（フィールド名の変更で素通りしない分むしろ堅い）
- スモークテストを検証になる形に修正 — `.env` 読み取りは settings の deny だけで止まるため hook の動作確認にならなかった。`head .env.local` に変更
- マスターの運用値の持ち込みを除去 — 「CLAUDE.md は ≤200行 厳守」を「明文化された上限があればそれに従う」に条件化（会社の CLAUDE.md に根拠のない削除提案が出るのを防ぐ）
- 導線の断裂を 3 件修復 — (1) 会話内設計を選んだときの副作用を選ばせる時点で伝える (2) 実装完了時に残り工程を全部提示する（オーケストレーターを外したため導線がフラグ頼みだった）(3) デプロイ節に「担当スキルは無い」と明記（毎タスクここで詰まる構造だった）

**2026-07-22 — レビュー系の除外と自己完結化**

- レビュー系 8 スキルを除外（コードレビューは会社のレビュープラグインを使う方針）。残るスキルの名指し箇所はスキル名に依存しない記述に置換
- `feature-pipeline` を除外（レビューフェーズを失ったオーケストレーターを維持しない判断）
- `review-result.md` は残した（**生成元を問わない**）。どの手段で作られたものでも `.steering/[task]/` に置いてあれば compound / knowledge-capture が入力として読む
- `.steering/` 成果物とスキル出力の見出しを日本語化。ただし `Status:` 行のキーと値は英語のまま（前提チェックが照合する契約値）
- knowledge-capture が ADR 形式を出さなくなった — 会社が独自の決定記録様式を持つ場合に押し付けないため。決定・理由・却下した代替案の 3 点を `decisions.md` に残すところまでを担当する
- 配布モデルの記述を除去 — このセットには存在しない元リポジトリを前提にした説明をスキル本文から削除した
