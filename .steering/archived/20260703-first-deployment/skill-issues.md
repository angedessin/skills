# skill-issues — starter-kit 初回実地検証（_test へのメタ層配置）

配置日: 2026-07-03 / 配置先: `_test/`（メタ層のみ: compound / rule-audit / empirical-prompt-tuning / feature-pipeline）/ source-commit: 508e21c

## 1. starter-kit.md の見出し「配置手順（5 ステップ）」が実際は 6 項目

- 事象: 見出しは「5 ステップ」だが番号付き項目は 1〜6。冒頭の依頼者認識も「6 手順」。
- 期待: 見出しを「6 ステップ」に修正（手順 6 のガードレール同送を追加した際の直し漏れとみられる）。

## 2. session-stop.sh の同送基準「.steering/ ワークフローを採用する場合のみ」が曖昧

- 事象: feature-pipeline は `.steering/` を使うため基準に該当しうるが、この hook の実効果は `.capture-needed` フラグ → knowledge-capture の起動促し。knowledge-capture 未配置の今回は、フラグが「実行不能な指示」（存在しないスキルの実行を促すメッセージ）になるため同送を見送った。
- 期待: 基準を「knowledge-capture を配置する場合のみコピーする」に明確化する。

## 3. CLAUDE.md 雛形が最小セット前提

- 事象: 雛形 3 行（design-doc / frontend-code-review / knowledge-capture）はすべて最小セットのスキルを参照。メタ層のみの配置では 1 行も使えず全面書き換えになった。「配置したスキルに合わせて追記・削除する」の注記はあるので実行不能ではない。
- 期待（軽微）: セット別の雛形例を用意するか、「配置スキルの description の発動フレーズから 1 行ずつ書く」と手順化する。

## 4. compound のフラグ起動導線がメタ層単独配置では死に導線

- 事象: description の「セッション開始時に .codify-needed フラグがあれば起動を促す」は、フラグを立てる側（frontend-code-review Phase 3）が未配置だと発生しない。SKILL.md 本文は `.steering/` 不在時の縮退記述があり実行自体は問題なし。
- 期待（軽微）: starter-kit の構成表かメタ層の行に「compound のフラグ自動起動は frontend-code-review 配置時のみ有効。単独では明示呼び出し」と一言添える。

## 5. 手順 4（references 再生成）が対象外スキルのみの配置だと no-op

- 事象: メタ層 4 スキルはいずれも references/ を持たず、手順 4 はスキップになった。手順書に誤りはないが、対象スキル（tdd / test-review / e2e / review-ui）を含まない配置では読んで判断する時間だけかかる。
- 期待（軽微）: 手順 4 冒頭に「対象スキルを含まない場合はスキップ」と明記。

## 6. 手順 3（source-commit 追記）が手作業

- 事象: 4 ファイルの frontmatter へ perl ワンライナーで追記した。スキル数が多い配置ではミスの余地がある。
- 期待（改善候補）: `scripts/` にコピー + source-commit 追記を行う配置スクリプトを用意する（validate → copy → 追記 → 差分表示まで）。

## 7. starter-kit にワークスペース信頼（trust dialog）の手順がない

- 事象: 配置直後の headless 実行（`claude -p`）で「this workspace has not been trusted」となり、settings.json の permissions.allow 6 件が無効化された（deny / hooks は有効だった）。対話セッションを一度起動して信頼ダイアログを承認するか、`~/.claude.json` の `projects[<path>].hasTrustDialogAccepted: true` を設定するまで allow が効かない。
- 期待: 手順 6 の後に「配置先で一度対話セッションを起動し、信頼ダイアログを承認する（headless 運用を始める前に必須）」を追記する。

## 8. 【重大】feature-pipeline 配下で design-doc の単一セッション分岐が承認ゲートを消滅させる

- 事象（_test での feature-pipeline E2E 検証で再現）: Phase 1 でディスパッチされた design-doc が自前のトリアージで「1 セッションで終わる」と判定し、`.steering/` を作らず会話内設計の分岐へ。設計方針を提示した後、**人間の承認を待たずにそのまま実装が始まった**。feature-pipeline の現在地検出・承認ゲートは `.steering/[task]/design.md` の存在と Status に依存するため、この分岐に入るとゲートが構造的に消滅する。
- 期待（契約の両側を同一コミットで修正 — skill-design-patterns「片側修正の禁止」）:
  - feature-pipeline 側: Phase 1 のディスパッチ指示に「必ず `.steering/[task]/` と design.md を作成し、APPROVED 待ちで停止する（単一セッション分岐は使わない）」を明記
  - design-doc 側: 「feature-pipeline 等のオーケストレーターから呼ばれた場合は常に .steering パスを使う」を本文に明記
  - あわせて design-doc の会話内設計分岐にも「設計提示後は明示承認を得るまで実装に入らない」のハードストップを入れる（単独利用でも同じ事故が起きうる）
- 補足: design-doc は App.tsx のコメント「機能は feature-pipeline の検証タスクで追加する」を小規模判定の根拠に使った。判定材料自体は妥当で、問題は分岐の存在をオーケストレーターが制御できないこと。
- 追加データ（2 回目の試行 — `/feature-pipeline` 明示呼び出し）: 明示呼び出しでも `.steering` なし分岐に再度入った。ただし今回は設計提示後に「Open questions への回答または承認をお願いします。実装には入りません」と**停止した**。会話内分岐の停止挙動は非決定的（1 回目は素通り・2 回目は停止）で、ハードストップが本文に無いことと整合する。

## 9. impl-from-design が起動条件（design.md APPROVED）を検証せず会話内承認で走った

- 事象（指摘 8 の 2 回目試行の続き）: design.md が存在しない状態で feature-pipeline Phase 2 が impl-from-design をディスパッチし、impl-from-design は**リダイレクトせずそのまま実装を開始**した。description には「.steering/[task]/design.md の Status が APPROVED である必要がある。design.md がない・DRAFT の場合は design-doc にリダイレクト」とあるが、会話内の「承認」発言が代用された。
- 期待: impl-from-design の本文冒頭に前提チェックを手順として明記する（「design.md を読む → 無ければ停止して design-doc へ」を Step 0 にする）。description だけに書かれた条件は実行時に守られないことが実証された（description は発動判定にしか効かない）。
- 波及: `.steering/[task]/` が無いまま Phase 2 以降が進むと、review-result.md・.codify-needed・.capture-needed・resume の検証（= feature-pipeline の中核価値）が全て成立しない。

## 10. compound の還元が配置先セッションからマスターを直接編集し、未検証の契約変更が混入した

- 事象: _test の feature-pipeline E2E 後、compound が指摘 8 相当の学びを昇格する際、_test セッションから**マスターの SKILL.md 2 本を直接編集**した（feature-pipeline に会話内フォールバック節を追加・impl-from-design に「設計を引数で受ける」フォールバックを追加）。ユーザー承認は compound のゲートで得ていたが、追加されたメカニズム（設計内容を引数渡し→検出→縮退）は**実地で一度も動いていない推測ベースの設計**で、かつ指摘 8 の期待（.steering 強制）と方向が矛盾していた。2026-07-04 に revert（文面は同ディレクトリの compound-proposal.patch に保存）。docs/knowledge/frontend-a11y-patterns.md は論点と無関係な正当なナレッジのため残置。
- 期待:
  - compound の昇格先がマスター（= 配置元リポジトリ）の場合は、直接編集ではなく**提案（patch / issue 記録）に留め、マスター側セッションでレビューして適用する**運用を compound 本文に明記する
  - 昇格案に「未検証の新メカニズム」が含まれる場合、compound はその旨を明示して承認を求める（動いた実績のあるパターンの記録と、推測の新設計を区別する）
- 還元時の方針: 指摘 8 の根本対応（feature-pipeline 配下では .steering 強制 + design-doc 会話内分岐のハードストップ）を採用し、compound-proposal.patch は代替案の記録として参照に留める。

## 11. debug が再現可能な環境で実行再現を省略し、縮退パスの但し書きも回避した

- 事象（_test での debug 検証・仕込みバグ調査）: 根本原因の特定自体は正確だったが、Step 1 の再現確認を「コードリーディングで確認済み（実行再現は省略）」として飛ばした。SKILL.md 上、コードリーディングベースへの切り替えは「**再現できない場合**」の縮退動作であり、その場合レポートに「再現未確認 — 結論の確度は下がる」と明記する契約。今回はテスト環境が完備され失敗テスト数行で再現できる状況での省略で、かつ「確認済み」という表現で確度の但し書きを回避した。
- 期待: Step 1 に「再現が可能な環境では省略しない。特に**失敗するテストとして再現を書く**（そのまま回帰テストになり、修正の検証にも使える）」を明記する。レポート様式の「再現:」欄は「実行再現済み / 未実行（コードリーディングベース・確度低）」の二択であることを強調し、中間表現を許さない。

## 12. debug が小修正を承認なしでその場適用した

- 事象（指摘 11 と同じ debug 検証セッション）: 根本原因レポート提示後、「小さい修正は**承認を得て**その場で適用」の契約に反し、ユーザーに確認せず src/TodoList.tsx の修正と回帰テスト追加を実行した（ユーザーに確認済み — 承認は求められていない）。修正内容自体は正しく、結果も全テスト緑。
- 期待: debug の修正方針ステップに「修正案を提示 → ユーザーの承認を待つ → 適用」のハードストップを手順として明記する。accept-edits モード（ツールレベルの自動承認）とスキルレベルの会話承認は別物であることも一文添える。
- メタ学習（還元時に skill-design-patterns へ昇格候補）: **承認・停止の契約は description や末尾の説明文に書いても実行時に守られない**。指摘 8（design-doc の会話内分岐が承認前に実装開始・非決定的）・指摘 9（impl-from-design が起動条件を未検証）・本件（debug が承認なし適用）の 3 例が同一パターン。守らせたい停止点は、手順の該当ステップに「ここで止まる」を明示するハードストップとして書き、検証（empirical / 実地）で停止することを確認する。

## 検証済み（2026-07-03 headless 検証の結果 — 問題なし）

- 全 19 スキルが _test セッションで読み込まれることを確認（name 全数一致）
- guard-env-read.sh: `head -1 .env`（deny 前置一致に該当しないコマンド）が hook の ask 経由でブロックされることを確認（非対話モードでは ask → deny に落ちる）
- permissions.deny: `pnpm add left-pad` がブロックされることを確認
- permissions.allow: `git log` が通ることを確認（Bash 全拒否ではなくルール駆動である対照実験）

## 検証環境の注意（手順書の問題ではない）

- `_test/` はマスターの git リポジトリ内にあるため、`git rev-parse --show-toplevel` に依存するスクリプト（session-stop.sh 等）は将来 _test 内で使うと**マスターの root を拾う**。_test を実プロジェクト相当にするなら `git init` が必要。guard-env-read.sh は `$CLAUDE_PROJECT_DIR` 依存なので問題ない。
