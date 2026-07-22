# 持ち出しセット — 会社ワークフロー用

- **マスターコミット**: `e90165507d319933f2c07f9538b0a0040e67842e`
- **作成日**: 2026-07-14（最終更新: 2026-07-22 — レビュー系 8 スキルと feature-pipeline を除外し、同梱を 9 スキルに縮小。コードレビューは会社のレビュープラグインを使う方針に変更したため）
- **検証**: 同梱 9 スキル 9/9 PASS（このセット自体に直接実行・2026-07-22）。ローカルパス・個人情報・外部 URL の混入なし（grep 検査済み）
- 各スキルの frontmatter `metadata.source-commit` に上記ハッシュを記録済み（配置先での手動追記は不要）
- **Angular 適用版**: マスター（React / Vitest 前提）から、tdd の本文・スコープ（.tsx → .ts / .html）を Angular / Jasmine 向けに書き換え済み。**スキル本文に React / Vitest / pnpm 等の個人スタック語彙は 1 件も残っていない**（機械確認済み。React 前提のコード例を集めた tdd のカートリッジは同梱から外した — 下記「同梱しなかったもの」参照）。**マスターとの diff を確認するときはこの変換分を差し引いて見る**（スキルの手順・停止契約は変えていない。変えたのはスタック語彙とコード例のみ）

## 2026-07-22 更新の要点（レビュー系の除外）

- **レビュー系 8 スキルを除外** — `frontend-code-review` / `impl-review` / `test-review` / `review-a11y` / `review-correctness` / `review-performance` / `review-security` / `review-ui`。コードレビューは**会社のレビュープラグインを使う**方針に決まったため、このセットからは外した。残るスキルがこれらを名指ししていた箇所（Related skills・When NOT to use の振り先・description・tasklist テンプレ）は、スキル名に依存しない記述（「コードレビューを実施する」等）に置き換え済み
- **`feature-pipeline` を除外** — レビューフェーズを失ったオーケストレーターを維持しない判断。計画→実装→統合→知見蓄積は、各スキル（design-doc → impl-from-design → knowledge-capture / compound）を順に使う運用にする
- **`review-result.md` は残す（生成元を問わない）** — 会社のレビュープラグイン・人間のレビューなど、どの手段で作られたものでも `.steering/[task]/review-result.md` に置いてあれば `compound` / `knowledge-capture` が知見抽出の入力として読む。テンプレート（design-doc の `references/templates.md`）は旧レビュー軸に依存しない汎用形に書き換え済み。レビュー手段が独自の出力形式を持つならそちらを優先してよい
- **hook `stop-typecheck.sh` を除外（5 本 → 4 本）** — Angular ではテンプレートの型エラーを検出できず CI・IDE と重複するため。詳細は「マスターから同梱しなかった hook」参照。`guard-env-read.sh` は残すが、**`jq` 必須**の前提を配置手順に明記した（無い環境では配置しない）
- **`.codify-needed` フラグは手動で立てる前提に変更** — 従来は frontend-code-review が自動生成していた。福利化を見送るときに自分で立てておくと、次セッション開始時に `session-start-check.sh` が拾って compound を再提案する（hook 側の変更は不要）

## 2026-07-22 更新の要点（マスター取り込み分 + 自己完結化）

- **`.steering/` 成果物の見出しが日本語になった** — design.md / tasklist.md のセクション見出し（目的・スコープ・制約・完了条件・アプローチ・主要コンポーネント・データフロー・テスト方針・未解決の論点・検討した代替案 / 実装・レビュー・デプロイ・福利化・知見保存）。**`Status:` 行のキーと値（DRAFT / APPROVED）は英語のまま**維持する — impl-from-design の前提チェックが照合する契約値のため
- **スキルの出力見出しも日本語化** — 「知見保存ドラフト」（knowledge-capture）・「福利化ドラフト」（compound）など
- **knowledge-capture が ADR 形式を出さなくなった** — 設計・アーキテクチャの決定は `.steering/[task]/decisions.md` に「決定・理由・却下した代替案」の 3 点で記録する。却下案がある決定にはドラフト末尾に「チームの決定記録に上げるか検討してください」と添えるだけで、**定型フォーマット（節構成を持つ ADR 形式）は生成しない**。会社が独自の決定記録様式を持つ場合に、こちらの形式を押し付けないための変更（形式は記録先を持つ側が決める）。`docs/glossary.md`（語彙・用語集）への分岐も全削除
- **design.md を書くときの 2 規律が追加** — (1) 固有名（パス・ディレクトリ名・ブランチ名・行番号・既存の運用方針）は書く時点で実在確認する、(2) 主要コンポーネントの表は暫定として扱い、変更対象を表す語で全文検索して確定させる手順を tasklist.md の先頭に入れる。主要コンポーネントの各行には「原本を開かずに妥当性を判定できる情報」を書く
- **design-doc は v1.8**（Phase 1.5 決定インタビューの停止契約は v1.6 のまま維持）
- **未同梱スキルへの参照を全廃** — `debug` / `pr-create` / `pr-feedback` / `empirical-prompt-tuning` / `impl-tournament` / `skill-harvest` を名指ししていた箇所（When NOT to use の振り先・Related skills・description・`.steering/` ファイル一覧の生成元表記・tasklist テンプレ）を、スキル名に依存しない記述に置き換えた。**同梱 9 スキル以外のスキル名は本文に 1 つも残っていない**（機械確認済み）
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
| （横断）摩擦の起票（会社内の改善ループ用） | session-retrospective |
| （定期）ルール・知識の剪定（compound と両輪） | rule-audit |

## 同梱しなかったもの（必要なら後から追加）

- **レビュー系 8 スキル（frontend-code-review / impl-review / test-review / review-a11y / review-correctness / review-performance / review-security / review-ui）** — 会社のレビュープラグインを使う方針のため除外。方針が変わったらマスターから追加コピーする（その際は残るスキルの「コードレビューを実施する」等の一般記述をスキル名に戻すか、そのままにするか判断する）
- **feature-pipeline** — レビューフェーズを含むオーケストレーターだったため、レビュー系の除外に伴って外した。工程は各スキルを順に使う（design-doc → impl-from-design → knowledge-capture / compound）
- **tdd の `references/patterns.md`（カートリッジ）** — 中身が React / Vitest / RTL / MSW / Jotai / pnpm の 272 行で、Angular / Jasmine の本文と矛盾していた（`§hook`・`§state` は Angular に対応物すら無い）。誤ったスタックのコード例を持ち込む害が、雛形としての価値を上回るため削除。**tdd は無くても動く**（本文の判断軸は言語非依存で、スキル側にフォールバックを明記済み）。作る場合は上記「配置先でやること」の手順 4 に従う
- **pr-create / pr-feedback / debug** — PR 運用・障害調査は会社の既存プロセスとの整合を確認してから。これらのスキル名への参照は本文から全廃済み
- **e2e** — 会社では E2E テストを行っていないため除外。各スキル本文・references・設計テンプレに残っていた `e2e` スキルへの参照と Playwright の例も除去済み（「E2E は対象外」という境界の記述のみ残している）。導入することになったらマスターから追加コピーする
- **impl-tournament** — N 並列実装で課金が大きい。必要になったら個別判断
- **adr** — 設計判断を ADR 形式（Context / Decision / Rationale / Consequences / Alternatives）で起票するマスター専用スキル。会社側の決定記録の様式が分からないため同梱しない。同梱の knowledge-capture は「決定・理由・却下した代替案」の 3 点を `.steering/[task]/decisions.md` に残すところまでを担当し、様式の決定は会社側に委ねる
- **skill-deploy / skill-harvest / skill-test / empirical-prompt-tuning / security-audit** — マスター専用またはメタ運用ツール（rule-audit は 2026-07-15 に同梱へ変更 — compound で増えるルール・知識を独立運用のまま剪定できるようにするため。本文中の未同梱スキルへの参照は除去済み）

## 配置先（会社）でやること

1. `.claude/skills/` に `skills/` 配下のディレクトリをそのままコピーする
2. **hooks を配置する** — `claude-config/hooks/` の 4 本を配置先の `.claude/hooks/` にコピーする。settings.json のコマンド登録は `"$CLAUDE_PROJECT_DIR"` 起点の相対参照なので、同じ配置ならパスの書き換えは不要
   - `session-start-check.sh`（SessionStart）: 未処理フラグ・アクティブタスクをセッション開始時に注入
   - `session-stop.sh`（Stop）: `.capture-needed` を立てて knowledge-capture の起動を促す
   - `guard-env-read.sh`（PreToolUse）: deny の前置一致をすり抜ける .env 読み取りを全文検査で ask に落とす。**`jq` に依存する** — 下記の前提確認を先に行う
   - `post-edit-lint.sh`（PostToolUse）: 編集ごとの lint 差し戻し（Biome / ESLint / Stylelint を自動検出）。**フェイルオープン**（lint 設定が無ければ素通し）なのでスタックを問わず置いてよい

   **guard-env-read.sh の前提: `jq` が必要**（コマンド全文を JSON から取り出して検査するため）。配置前に `jq --version` が通ることを確認する。
   - **通る** → そのまま配置する
   - **通らない** → このフックは**配置しない**（settings.json の `PreToolUse` ブロックごと削除する）。jq が無いと検査できず**フェイルクローズで全 Bash 呼び出しが確認プロンプトになる**ため、実運用に耐えない。jq を導入できるならそれが最善（`settings.example.json` は `brew install *` を deny しているので、導入は人が手動で行う）
3. **settings をマージする** — `claude-config/settings.example.json` を配置先の `.claude/settings.json` に**手動マージ**する（丸ごと上書きしない）。既存の allow と deny が同じ操作で衝突したら **deny を優先**（安全側）。マスターとの差分として **npx は全面 deny** に強化済み（下の「npx 禁止」参照）
4. **tdd のカートリッジを作る（任意・配置先の AI に依頼する）** — tdd は「エンジン（本文の判断軸）＋カートリッジ（`references/patterns.md` のスタック固有例）」構成だが、**カートリッジは同梱していない**（元は React / Vitest / RTL / MSW 前提の中身で、Angular / Jasmine の本文と矛盾し、誤ったコード例を持ち込む害の方が大きいため削除した）。**無いままでも tdd は動く** — 本文の判断軸は言語非依存で、スキル側にその旨のフォールバックが書いてある。具体例を効かせたければ、配置先で AI に実際のテスト環境（Jasmine の実行基盤・TestBed の使い方・既存 spec の慣習）を調べさせてから作成を依頼する
   - 見出しは本文が参照する §名にする: `§run`（実行コマンド）/ `§config`（ランナー設定）/ `§setup`（共通セットアップ）/ `§unit` / `§component` / `§query-ladder`（クエリ優先順位）/ `§network`（ネットワークモック）/ `§hook` / `§state` / `§api-layer` / `§coverage`。Angular に対応物が無い節は省いてよい
   - 依頼例:「このプロジェクトの実際のテスト構成を確認して、`.claude/skills/tdd/references/patterns.md` を Jasmine / TestBed 向けに新規作成して。見出しは SKILL.md が参照する §名に合わせる。SKILL.md 本文は変更しない。npx は使わない」
5. **CLAUDE.md に発動ポリシー節を作る**（下の雛形を貼って調整）
6. **`.gitignore` に 3 行追加**: `.steering/**/.capture-needed` / `.steering/**/.codify-needed` / `.steering/**/capture_done`
7. **`.npmrc` に `ignore-scripts=true` を設定**（install 時の postinstall 実行＝サプライチェーン攻撃の主経路を既定で遮断）
8. **一度対話セッションを起動して信頼ダイアログを承認する** — 未信頼のワークスペースでは settings.json の permissions.allow が無効化される（deny / hooks は有効）
9. **スモークテスト**:
   - 「どのスキルが使える？」→ 配置したスキルが一覧に出る
   - 小さなタスクを依頼 → design-doc が設計提示後に**承認待ちで停止する**（勝手に実装が始まったら FAIL）
   - `.env` の読み取りを依頼 → guard-env-read.sh が確認（ask）に落とす
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
- マスター側でこのセットを更新する場合は、マスターで `git diff e901655 -- .claude/skills/<name>` で差分を確認して再エクスポートする（Angular 変換分・E2E 除去分の再適用を忘れない。各スキルの `source-commit` が示すコミットが差分の起点）
