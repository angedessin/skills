# 持ち出しセット — 会社ワークフロー用

> **同梱スキル数の一次情報は `skills/` のディレクトリ数**（`ls skills/ | wc -l` で数える）。本文中の「9 スキル」は provenance（debug 以外の 9 本が同一 source-commit）または日付付き履歴節の記述であり、現在の同梱数ではない。現在は **10 スキル**。

- **マスターコミット**: `e90165507d319933f2c07f9538b0a0040e67842e`
- **作成日**: 2026-07-14（最終更新: 2026-07-23 — debug を追加し同梱 10 スキルに。2026-07-22 にレビュー系 8 スキルと feature-pipeline を除外して 9 スキルに縮小していた）
- **検証**: 同梱 10 スキル 10/10 PASS（このセット自体に直接実行・2026-07-23）。ローカルパス・個人情報・外部 URL の混入なし（grep 検査済み）
- 各スキルの frontmatter `metadata.source-commit` にコミットハッシュを記録済み（配置先での手動追記は不要）。9 スキルは上記 `e90165` から、後から追加した debug は master HEAD `dd1bb31` から作成しており provenance が分かれる（debug の該当分岐が e90165 時点には存在せず、実際の複製元 HEAD を記録したため）
- **Angular 適用版**: マスター（React / Vitest 前提）から、tdd の本文・スコープ（.tsx → .ts / .html）を Angular / Jasmine 向けに書き換え済み。**スキル本文に React / Vitest / pnpm 等の個人スタック語彙は 1 件も残っていない**（機械確認済み。React 前提のコード例を集めた tdd のカートリッジは同梱から外した — 下記「同梱しなかったもの」参照）。**マスターとの diff を確認するときはこの変換分を差し引いて見る**（スキルの手順・停止契約は変えていない。変えたのはスタック語彙とコード例のみ）

## 2026-07-23 更新の要点（debug の追加）

- **debug を同梱**（9 → 10 スキル）。会社のバグ対応向けデザインドキュメントテンプレートは「不具合の再現手順」「根本原因」の記入を求めるが、その調査を担うスキルがセットに無かった。ユーザー確認のうえ追加した（2026-07-22 時点では「障害調査は会社の既存プロセスとの整合を確認してから」として保留していた項目）。
- **design-doc を debug に再配線**。When NOT to use・description の「バグ・障害の原因調査」を `debug` 名指しに戻した（2026-07-22 の除外時にスキル名参照を全廃していたぶんの復元）。debug 側は既に design-doc へ接続済みで、これで producer/consumer の対が成立する。
- **配布加工**: pr-feedback 分岐を MR 運用の記述に言い換え（pr-feedback は非同梱）、Related skills の `frontend-code-review` 行を削除。**同梱 10 スキル以外のスキル名は本文に 1 つも残っていない**（機械確認済み）。
- **provenance の分岐**: debug の `source-commit` は他 9 スキル（`e90165`）と異なり master HEAD `dd1bb31`。該当の pr-feedback 分岐が e90165 時点では未追加だったため、実際の複製元 HEAD を記録した。

## 2026-07-22 更新の要点（レビュー系の除外）

- **レビュー系 8 スキルを除外** — `frontend-code-review` / `impl-review` / `test-review` / `review-a11y` / `review-correctness` / `review-performance` / `review-security` / `review-ui`。コードレビューは**会社のレビュープラグインを使う**方針に決まったため、このセットからは外した。残るスキルがこれらを名指ししていた箇所（Related skills・When NOT to use の振り先・description・tasklist テンプレ）は、スキル名に依存しない記述（「コードレビューを実施する」等）に置き換え済み
- **`feature-pipeline` を除外** — レビューフェーズを失ったオーケストレーターを維持しない判断。計画→実装→統合→知見蓄積は、各スキル（design-doc → impl-from-design → knowledge-capture / compound）を順に使う運用にする
- **`review-result.md` は残す（生成元を問わない）** — 会社のレビュープラグイン・人間のレビューなど、どの手段で作られたものでも `.steering/[task]/review-result.md` に置いてあれば `compound` / `knowledge-capture` が知見抽出の入力として読む。テンプレート（design-doc の `references/templates.md`）は旧レビュー軸に依存しない汎用形に書き換え済み。レビュー手段が独自の出力形式を持つならそちらを優先してよい
- **hook `stop-typecheck.sh` を除外（5 本 → 4 本）** — Angular ではテンプレートの型エラーを検出できず CI・IDE と重複するため。詳細は「マスターから同梱しなかった hook」参照
- **`.codify-needed` フラグの生成を knowledge-capture に移した** — 従来は frontend-code-review が自動生成していたため、そのまま外すと**フラグを立てる主体が消えて福利化ループが二度と回らなくなる**（読み手だけが残る）。knowledge-capture の最終 Step に「福利化の要否を確認し、見送るならフラグを立てる」手順を追加して閉じた。hook 側の変更は不要

## 2026-07-23 更新の要点（敵対レビューでの指摘対応）

配布前に第三者視点の敵対レビューを実施し、確認された指摘を全件修正した。

- **tdd 本文から別スタック固有の API を除去** — `queryBy*` + `.not.toBeInTheDocument()`（Testing Library / jest-dom）・`includeSource`（Vitest 専用の in-source testing）・`§hook`（React Hooks）が本文に残っており、**Jasmine では実行できないテストを書かせる**状態だった。判断軸（否定アサーションの選び方・種類別の使い分け）だけを残してスタック非依存の記述に置換
- **テストファイル命名の片側修正を解消** — tdd は `*.spec.ts` を例示していたのに impl-from-design は `Foo.test.[ext]` のままで、**Angular のテストランナーに収集されず「1 件も実行されないまま緑」になる**危険があった。両方を「既存テストを 1 つ開いて命名規則を確認してから作る」に統一
- **福利化ループの断線を修復** — `.codify-needed` を立てる主体（frontend-code-review）を除外したまま読み手だけ 14 箇所残っており、**compound が二度と自動提案されない**状態だった。生成を knowledge-capture の最終 Step に移設（上記参照）
- **hook の jq 依存を全廃した** — 当初は「4 本中 3 本が jq に依存し、うち 2 本は無言で無効化される」ことを配置手順に書いて回避しようとしたが、**社内端末に jq を入れさせる前提自体が現実的でない**と判断し、依存を消した。`guard-env-read` は JSON を構造として解釈せず標準入力を全文検査する方式に変更（解析器が不要になるうえ、フィールド名の変更で素通りしない分むしろ堅い）。`session-start-check` / `post-edit-lint` は値の切り出しと出力エスケープを `grep` / `sed` で行う（BSD sed でも動くよう GNU 拡張を使わない）。**4 本とも追加インストール不要**
- **スモークテストを検証になる形に修正** — `.env` 読み取りは settings の deny だけで止まるため hook の動作確認にならなかった。deny の前置一致をすり抜ける `head .env.local` に変更し、hook 未配置時の期待結果も明記
- **マスターの運用値の持ち込みを除去** — 「CLAUDE.md は ≤200行 厳守」（compound / knowledge-capture）を「明文化された上限があればそれに従う」に条件化。会社の CLAUDE.md に対して根拠のない削除提案が出るのを防ぐ
- **design.md テンプレのドリフトを解消** — steering 側のテンプレに `## 調査結果` 節が無く、実装スキルが書き込む対象が存在しない状態だった
- **tasklist テンプレを GitLab / MR 運用に合わせた** — `gh pr create` / GitHub Actions（マスターの運用）を、MR 作成 → CI グリーン確認 → レビュー承認 → マージ に変更。**この節を進めるスキルは無い**ことをテンプレのコメントに明記した（担当が居ないまま「未チェックだからアーカイブできない」で詰まらないように）
- **非同梱スキル前提の記述を削除** — 「オーケストレーターから呼ばれた場合」の例外分岐（該当スキルは非同梱）
- **knowledge-capture の誤発動を抑制** — description の起動フレーズから「ドキュメントを更新して」を外した（README 更新等の日常語で知見保存フローが起動していた）

### ワークフロー通し確認での追加修正

工程の受け渡しを端から端まで追跡し、導線が切れる箇所を 3 件直した。

- **会話内設計を選んだときの影響を、選ばせる時点で伝えるようにした** — `.steering/` を作らない分岐を選ぶと `design.md` が存在しないため、`impl-from-design`（前提チェックで停止）と `design-premortem`（対象不在で停止）が使えなくなる。この副作用が本文に書かれておらず、**選んだ人が後で「スキルが動かない」に突き当たる**状態だった。承認後はその会話の中で実装を進めることも併せて提示する
- **実装完了時に残り工程を全部提示するようにした** — 一気通貫のオーケストレーターを外したため、`impl-from-design` の「レビューを実施してください」で導線が途切れ、その先（レビュー結果の記録・MR・knowledge-capture・アーカイブ）はフラグ頼みだった。フラグの検出は hook（`session-start-check.sh`）が担うが、hook が何らかの理由で動かないと導線ごと消えるため、フラグに依存しない案内を 1 本通した
- **デプロイ節に「担当スキルは無い」と明記した** — `steering` の archive 前提は「tasklist.md の全項目チェック済み」だが、デプロイ節を進めるスキルが無いため、**毎タスクここで引っかかる**構造だった。人が実施してチェックする節だと分かるようにした

## 2026-07-22 更新の要点（マスター取り込み分 + 自己完結化）

- **`.steering/` 成果物の見出しが日本語になった** — design.md / tasklist.md のセクション見出し（目的・スコープ・制約・完了条件・アプローチ・主要コンポーネント・データフロー・テスト方針・未解決の論点・検討した代替案 / 実装・レビュー・デプロイ・福利化・知見保存）。**`Status:` 行のキーと値（DRAFT / APPROVED）は英語のまま**維持する — impl-from-design の前提チェックが照合する契約値のため
- **スキルの出力見出しも日本語化** — 「知見保存ドラフト」（knowledge-capture）・「福利化ドラフト」（compound）など
- **knowledge-capture が ADR 形式を出さなくなった** — 設計・アーキテクチャの決定は `.steering/[task]/decisions.md` に「決定・理由・却下した代替案」の 3 点で記録する。却下案がある決定にはドラフト末尾に「チームの決定記録に上げるか検討してください」と添えるだけで、**定型フォーマット（節構成を持つ ADR 形式）は生成しない**。会社が独自の決定記録様式を持つ場合に、こちらの形式を押し付けないための変更（形式は記録先を持つ側が決める）。`docs/glossary.md`（語彙・用語集）への分岐も全削除
- **design.md を書くときの 2 規律が追加** — (1) 固有名（パス・ディレクトリ名・ブランチ名・行番号・既存の運用方針）は書く時点で実在確認する、(2) 主要コンポーネントの表は暫定として扱い、変更対象を表す語で全文検索して確定させる手順を tasklist.md の先頭に入れる。主要コンポーネントの各行には「原本を開かずに妥当性を判定できる情報」を書く
- **design-doc は v1.8**（Phase 1.5 決定インタビューの停止契約は v1.6 のまま維持）
- **未同梱スキルへの参照を全廃** — `debug` / `pr-create` / `pr-feedback` / `empirical-prompt-tuning` / `impl-tournament` / `skill-harvest` を名指ししていた箇所（When NOT to use の振り先・Related skills・description・`.steering/` ファイル一覧の生成元表記・tasklist テンプレ）を、スキル名に依存しない記述に置き換えた。**同梱 9 スキル以外のスキル名は本文に 1 つも残っていない**（機械確認済み）。※ 2026-07-23 に debug を同梱へ追加し、design-doc の「バグ・障害の原因調査」参照は `debug` 名指しに復元した（上の「2026-07-23 更新の要点」参照）
- **配布モデルの記述を除去** — 「マスターを直接編集しない」「skill-harvest でマスターへ還流する」等、このセットには存在しない元リポジトリを前提にした説明をスキル本文から削除した（運用ルールは本 MANIFEST 側にのみ置く）
- **`tasklist.md` の見出し参照を日本語化に追随** — compound の「`tasklist.md` の Compound チェックボックス」→「「福利化」チェックボックス」（マスター側では未追随の片側修正が残っている箇所）

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
- **tdd の `references/patterns.md`（カートリッジ）** — 中身が React / Vitest / RTL / MSW / Jotai / pnpm の 272 行で、Angular / Jasmine の本文と矛盾していた（`§hook` は React Hooks 専用で Angular に対応物が無いため、本文の §名リストからも削除した）。誤ったスタックのコード例を持ち込む害が、雛形としての価値を上回るため削除。**tdd は無くても動く**（本文の判断軸は言語非依存で、スキル側にフォールバックを明記済み）。作る場合は上記「配置先でやること」の手順 4 に従う
- **pr-create / pr-feedback** — PR（MR）運用は会社の既存プロセスとの整合を確認してから。これらのスキル名への参照は本文から全廃済み（debug は 2026-07-23 に同梱へ変更 — 上の「2026-07-23 更新の要点」参照）
- **e2e** — 会社では E2E テストを行っていないため除外。各スキル本文・references・設計テンプレに残っていた `e2e` スキルへの参照と Playwright の例も除去済み（「E2E は対象外」という境界の記述のみ残している）。導入することになったらマスターから追加コピーする
- **impl-tournament** — N 並列実装で課金が大きい。必要になったら個別判断
- **adr** — 設計判断を ADR 形式（Context / Decision / Rationale / Consequences / Alternatives）で起票するマスター専用スキル。会社側の決定記録の様式が分からないため同梱しない。同梱の knowledge-capture は「決定・理由・却下した代替案」の 3 点を `.steering/[task]/decisions.md` に残すところまでを担当し、様式の決定は会社側に委ねる
- **skill-deploy / skill-harvest / skill-test / empirical-prompt-tuning / security-audit** — マスター専用またはメタ運用ツール（rule-audit は 2026-07-15 に同梱へ変更 — compound で増えるルール・知識を独立運用のまま剪定できるようにするため。本文中の未同梱スキルへの参照は除去済み）

## 配置先（会社）でやること

1. `.claude/skills/` に `skills/` 配下のディレクトリをそのままコピーする
2. **hooks を配置する** — `claude-config/hooks/` の 4 本を配置先の `.claude/hooks/` にコピーする。settings.json のコマンド登録は `"$CLAUDE_PROJECT_DIR"` 起点の相対参照なので、同じ配置ならパスの書き換えは不要
   - `session-start-check.sh`（SessionStart）: 未処理フラグ・アクティブタスクをセッション開始時に注入
   - `session-stop.sh`（Stop）: `.capture-needed` を立てて knowledge-capture の起動を促す
   - `guard-env-read.sh`（PreToolUse）: deny の前置一致をすり抜ける .env 読み取りを全文検査で ask に落とす
   - `post-edit-lint.sh`（PostToolUse）: 編集ごとの lint 差し戻し（Biome / ESLint / Stylelint を自動検出）。**フェイルオープン**（lint 設定が無ければ素通し）なのでスタックを問わず置いてよい

   **前提ツールの追加インストールは不要。** 4 本とも `grep` / `sed` / `find` など POSIX 標準の
   ユーティリティだけで動く。Claude Code は hook に JSON を標準入力で渡すが、JSON 解析器
   （`jq` 等）には依存しない設計にしてある — `guard-env-read` は構造を解釈せず全文を検査し、
   他の 2 本は必要な値の切り出しと出力のエスケープを標準ユーティリティで行う。
3. **settings をマージする** — `claude-config/settings.example.json` を配置先の `.claude/settings.json` に**手動マージ**する（丸ごと上書きしない）。既存の allow と deny が同じ操作で衝突したら **deny を優先**（安全側）。マスターとの差分として **npx は全面 deny** に強化済み（下の「npx 禁止」参照）。また **`CLAUDE.md` と `docs/knowledge/**` への書き込みを ask** にしてある — knowledge-capture は本文のハードストップで「承認前に書き込まない」を担保しているが、締めを尽くした状態でも承認前の書き込みが 1/4 の頻度で再現した実測があるため、機械的な最後の防波堤を置いている。**この 2 行は外さないことを推奨する**
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
10. 気づいた不具合・誤発動は `.steering/[task]/skill-issues.md` に起票する（session-retrospective が拾う）。改善は**会社リポジトリ内で直接スキルを編集してよい**（下の「独立運用」参照 — このセットは還流経路を持たないため、通常の「配置先で直接編集しない」ルールは適用しない）

### npx 禁止（このセットの方針）

**npx は使わない**（未導入バイナリだとレジストリ取得→即実行が走るため）。settings.example.json で
`Bash(npx)` / `Bash(npx *)` / `Bash(npm exec *)` を deny 済み。references を npm プロジェクト向けに
再生成するときも npx へ置き換えず、**ローカル導入済みバイナリを `./node_modules/.bin/<bin>` の直接実行
または package.json の scripts（`npm run <script>`）経由で呼ぶ**よう指定する。

### マスターから同梱しなかった hook

- `validate-skill-edit.sh` — マスター専用（`scripts/validate_skills.py` に依存。スキル編集の機械検証はマスターで行う）
- `stop-typecheck.sh`（Stop: 終了宣言時の `tsc --noEmit`）— Angular では**テンプレートの型エラーを検出できない**（テンプレートの型チェックは Angular コンパイラの担当で、素の tsc は `.ts` しか見ない）ためカバー範囲が中途半端で、CI と IDE の型チェックと重複する。加えて大きめのコードベースでは実行が 20-30 秒を超え、終了のたびに待たされる。型チェックは CI に任せる方針で除外した

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
- **マスターから再持ち込みする場合は丸ごと上書きしない**: `modified` の付いたスキルは会社側の変更を優先し、必要な差分だけ手動マージする（再持ち込みの予定が無ければこの 2 つは無視してよい — 持ち込み後は会社側で育てるのが既定）
### このセットの検査を回すときの運用ルール（20260725 追加）

- **素通り検査は `--all` を使わない。** `passthrough_check.py --all` の走査対象は `tests/passthrough/` 固定で、このセット専用のシナリオ（`export/company/tests/`）を**永久に拾わない**。さらにこのブランチには master 側の `.claude/skills/` と `tests/passthrough/` もそのまま存在するため、`--all` は**master のスキルを検査して PASS を返す**。持ち出しセットを 1 本も見ていないのに「検査済み」に見える
- **シナリオは明示指定で回す**: `python3 scripts/passthrough_check.py export/company/tests/<skill>/scenario.md --runs 4`（承認ゲート系は 4 回以上）
- **実行はこのブランチ（worktree）側の `scripts/` から行う**。スクリプトはルートを実行ファイルの位置から決めるため、main 側の `scripts/` を使うと `export/company/` を解決できない
- **master をマージしたら停止契約の差分ガードを回す**: `python3 scripts/check_export_stopcontract.py`（引数なしで worktree を自動発見）。master 側の停止契約の改善が持ち出し側に伝播していない箇所が「実質差分」として出る。出力の件数をそのままシナリオ選定に使わず、差分の中身を見て判断する

### このセット（`export/company/`）自体の育成方針（2026-07-23 決定）

上の 4 点は**配置後の会社コピー**の運用。ここは**このリポジトリで持つ持ち出しセットそのもの**を今後どう育てるか。

- **`export/company/skills/` を直接編集して育てる。マスター（`.claude/skills/`）を upstream として追跡しない。** 会社のコードベースが見えず、こちらで作れるのは汎用の大枠までなので、マスター同期に手間をかけても得るものが少ない（完全独立フォーク方針）。
- `source-commit` は出所の履歴として残すだけ。**定期的な再エクスポート・マスター差分の取り込みはしない。** 2026-07-23 の「影響範囲」欄の伝播が、マスター起点の最後の同期。以後マスター側の改善はこのセットに自動では入らない。
- 例外的に、マスターの特定スキルを一度だけ持ち込みたい場合（例: 新スキルが欲しくなった）は `git diff <source-commit> -- .claude/skills/<name>` で差分を見て手動で取り込み、Angular 変換分・E2E 除去分を再適用する。これは一回きりの操作で、継続同期ではない。
