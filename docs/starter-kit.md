# スターターキット — スキルの使い方と他プロジェクトへの配置手順

このドキュメントは 2 種類の読者を対象にする:
- **A. スキルを使う人**（これらのスキルが入ったプロジェクトに参加した / 使い始める人）→ 次の「スキルを使う人向け」節
- **B. スキルを配置する人**（このマスターリポジトリから他プロジェクトへ持っていく人）→ 「推奨構成」以降

ワークフロー全体像は [README](../README.md) の「メインワークフロー」図が一次情報。この節はその図を「使う人」目線で補足する。

---

## スキルを使う人向け（オンボーディング）

### そもそもスキルとは何か

スキルは Claude Code の**振る舞いのプリセット**。あなたが特定のフレーズで依頼すると自動で発動し、
そのタスク専用の手順・判断軸・停止ポイントに沿って Claude が動く。コマンドを暗記する必要はない —
**自然な日本語で頼めばいい**。例:

| あなたの依頼 | 発動するスキル | 何をしてくれるか |
|---|---|---|
| 「◯◯機能を作りたい」「△△を設計して」 | design-doc | 設計（Goal/Scope/設計方針）をまとめ、**承認を求めて止まる**（勝手に実装しない） |
| 「テストを先に書いて」「既存コードにテスト足して」 | tdd | Red→Green→Refactor で書く。テストリストを提示して承認を待つ |
| 「コードをレビューして」 | frontend-code-review | 変更を複数観点（正当性・セキュリティ・a11y 等）でレビューし指摘を出す |
| 「バグを調査して」「なぜ動かない？」 | debug | 再現→仮説→切り分け→根本原因。修正は承認を得てから |
| 「PR を作って」 | pr-create | ブランチ作成・PR 本文作成。**プッシュ前に承認を求めて止まる** |
| 「フロー全体を通してやって」 | feature-pipeline | 設計→実装→レビュー→PR→知見蓄積を順に回す（各境界で承認） |

各スキルが「いつ発動し・いつ発動しないか」は、そのスキルの `SKILL.md` 冒頭の description に書いてある。
迷ったら「どのスキルが使える？」と聞けばいい。

### よくある疑問（FAQ）

**Q. このワークフローを使わなくても開発できる？**
できる。**スキルは全て任意**。「この関数のバグ直して」「ここに引数足して」のような普通の依頼には、
スキルは発動せず Claude が通常どおり実装する。ワークフローは「使いたいときに乗る」もので、
強制されるレールではない。
※ ただし配置先の `CLAUDE.md` に発動ポリシー（例:「新機能は design-doc を使い、承認まで実装しない」）が
書かれている場合、そのプロジェクトの規約としてスキルの利用が期待される。使わない運用にしたいなら
CLAUDE.md のポリシー側を調整する（スキル本文は触らない）。

**Q. スキルは個別に（つまみ食いで）使える？**
使える。**各スキルは単独で完結する自己完結設計**。frontend-code-review だけ、tdd だけ、pr-create だけ、
という使い方でいい。feature-pipeline はそれらを 1 本に繋ぐ**任意の**オーケストレーターで、
必須ではない。実際、配置時も「必要なスキルだけ選んで入れる」のが基本（下の「推奨構成」参照）。
依存が要るスキル（例: impl-from-design は design.md を前提とする）は、前提が無ければ止まって案内するので、
順序を間違えても壊れない。

**Q. ワークフローの途中でやめられる？ 中断できる？**
できる。ワークフローは**主要な判断点（設計承認・指摘トリアージ・マージ・知見保存）に人間の承認ゲート**を持つ。設計を見て「今日はここまで」でも、
レビュー指摘を見て「後で対応する」でも、その場で止められる。さらに複数セッションにまたがるタスクは
状態が `.steering/[task]/` に残るので、**次のセッションで続きから再開**できる（`feature-pipeline` が
現在地を検出して途中フェーズから再開する）。承認ゲートで勝手に先へ進むことはない —
「続けて」等の曖昧な指示ではゲートをスキップしない設計になっている。

**Q. `.steering/` は git にコミットする？**
コミットを推奨する（設計・決定・タスク状態は複数セッション再開と知見還流の入力になる）。ただしランタイムフラグはコミットしない — マスターと同じく `.gitignore` に `.steering/**/.capture-needed`・`.steering/**/.codify-needed`・`.steering/**/capture_done` の 3 行を追加する。

### 使うときのコツ

- **承認を求めて止まったら、それは仕様**。設計・レビュー結果・PR 内容を人間が確認するための停止点。
  内容を見て「承認」「修正して」「後で」などを返す。
- **急ぎの小さな修正はスキルを介さず直接頼む**のが速い（typo・1 行修正に design-doc は要らない）。
- **`.steering/` は消さない**。進行中タスクの記憶なので、消すと再開できなくなる。

---

## スキルを配置する人向け

対象: このマスターリポジトリから他プロジェクトへスキルを配置する人。
配布方式は手動コピー（[ADR 20260612](decisions/20260612-manual-copy-skill-distribution.md)）— **どのスキルを持っていくかは人が選ぶ**。それ自体が誤発動を防ぐガードレール。

---

## 推奨構成

全スキルは**配布可**（他プロジェクトへコピー可）と**マスター専用**（このリポジトリの管理ツール・配布しない）に分かれる。下表の配布可否を確認して選ぶ。

| セット | スキル | 配布可否 | いつ入れるか |
|---|---|---|---|
| **最小** | design-doc / steering / impl-from-design / tdd / frontend-code-review / impl-review / test-review / knowledge-capture | 配布可 | まず試すならこれ。基本フロー（計画→実装→レビュー→知見）を一周できる最小セット。設計承認ゲートが実装を拘束する規律（impl-from-design の前提チェック）まで含む |
| **拡張 1: レビュー厚み** | review-security / review-a11y / review-performance / review-correctness / review-ui | 配布可 | frontend-code-review のフルモード（7 エージェント並列）を使う場合 |
| **拡張 2: 統合・運用** | e2e / debug / pr-create / pr-feedback | 配布可 | E2E テスト・障害調査・PR 提出と往復まで揃える場合 |
| **拡張 3: 設計品質・比較** | design-premortem / impl-tournament | 配布可 | 人間レビュー前の設計の穴出し・リスクの高いアプローチ選択の N 並列比較を使う場合（任意・impl-tournament は課金前置承認あり） |
| **メタ層** | compound / rule-audit / empirical-prompt-tuning / feature-pipeline / session-retrospective | 配布可 | 自己改善ループとオーケストレーションまで運用する場合（このマスター級の運用） |
| **拡張 4: セキュリティ** | security-audit | 配布可 | サードパーティスキルの採用前・定期の棚卸しで、セットアップ資産（スキル・hooks・settings・依存）の危険性を静的監査する場合（任意・オンデマンド・hooks 自動起動しない） |
| **マスター専用（配布しない）** | skill-test / skill-harvest / skill-deploy | **master-only** | このリポジトリ（スキルのマスター）でのみ使う管理ツール。配置先にはコピーしない |

- feature-pipeline は依存サブスキルが揃っている前提のため最小セットに含めない
- **session-retrospective は skill-harvest への供給側**。配置先に session-retrospective を併配すると、セッション摩擦が配置先の `skill-issues.md` に溜まり、マスターの skill-harvest がそれを還流できる（`.steering/**/skill-issues.md` を書くルールはマスターの CLAUDE.md にしか無いため、この併配が producer/consumer の対を成立させる）。`.steering/` 運用をしない配置先では harvest への供給は成立しない
- **skill-test / skill-harvest はマスター専用**。配置先にコピーしても意味がない（skill-test はマスターの全スキルを検証対象にし、skill-harvest はマスターから配置先を見に行くツール）
- **security-audit は配布可**。サードパーティ製 SKILL.md を採用する配置先で特に有用（採用前の静的スキャン）。ただし「検出なし」は安全証明ではなく、CLAUDE.md の「採用前に目視確認する」ルールを置換しない補助ツールとして入れる。frontend-code-review の review-security（コード diff の XSS 等）とは対象が別

## スキル間の依存関係（配置の組み合わせ判断用）

本文に散在する依存情報の要約。一次情報は各 SKILL.md — この表と食い違ったら SKILL.md が正:

| スキル | 依存先 | 欠けている場合の挙動 |
|---|---|---|
| impl-from-design | design-doc が作る `design.md`（APPROVED） | 止まって design-doc を案内する（実装に入らない） |
| impl-from-design（TDD モード） | tdd の `references/patterns.md` | パターン参照なしの縮退（本文の判断軸のみでテストを書く） |
| frontend-code-review | review-* 7 軸 / impl-review / test-review | 未配置分をスキップして報告する（縮退動作） |
| compound の自動起動 | frontend-code-review が立てる `.codify-needed` | フラグ起動が効かないだけ。明示呼び出しで使える |
| knowledge-capture の自動起動 | `session-stop.sh`（Stop hook）が立てる `.capture-needed` | フラグ起動が効かないだけ。明示呼び出しで使える |
| pr-feedback | pr-create | **対で入れる**（提出と往復は対。片方だけでは往復の入口/出口が欠ける） |
| feature-pipeline | 各フェーズのサブスキル（design-doc / impl-from-design / frontend-code-review / pr-create / pr-feedback / knowledge-capture / compound / e2e / steering） | フェーズごとにディスパッチ前に存在確認し、無いフェーズはスキップして「手動で行ってください」と報告する |
| session-retrospective | （マスター側の）skill-harvest が回収 | 単独でも動くが、還流先が無ければ `skill-issues.md` は配置先に溜まるだけ |

## フロントエンド以外・別ワークフローのプロジェクトへの導入

スキルは「本文 = スタック非依存の判断軸 / references = スタック固有の具体例」で分離されているため、フロントエンド以外にも層を選んで導入できる:

| 導入先 | 持っていけるもの |
|---|---|
| **どんなスタックでも**（バックエンド・CLI・インフラ含む） | メタワークフロー: design-doc / steering / debug / knowledge-capture / compound / rule-audit / feature-pipeline / empirical-prompt-tuning / security-audit。設計承認ゲート・障害調査・知見蓄積・剪定・セットアップ資産のセキュリティ監査はコードの種類に依存しない |
| **テストを書くプロジェクト全般** | tdd / test-review / e2e。本文は判断軸のみなので、references/patterns.md を自分のテストスタック（pytest / JUnit / Go test 等）で再生成する |
| **フロントエンド（React 以外も可）** | frontend-code-review + review-* 全 7 軸。判断軸は概ねフレームワーク中立（a11y / CWV / XSS / correctness）。compatibility とコード例を自分のフレームワークに合わせる |
| **フロントエンド以外でのレビュー** | review-correctness は言語横断で使える（境界条件・null・非同期レース・エラー握りつぶし）。review-a11y / ui / performance は対象外なので配置しない |

既存の開発ワークフロー（レビュー体制・ブランチ運用・チケット管理）があるプロジェクトでは、**スキル本文を書き換えず**、配置先 CLAUDE.md の発動ポリシー側で接続を定義する（例:「PR 作成は既存のチーム運用に従い、feature-pipeline の Phase 3.5 はスキップする」「設計レビューは design.md ではなく既存の Design Doc プロセスに読み替える」）。

## 配置手順（8 ステップ）

> **マスターで作業する場合は `skill-deploy` スキルが手順 1〜7 を駆動する**（セット選択 → dry-run 提示 → 明示承認 → `scripts/deploy_skills.py` 実行。手順 8 のスモークテストは配置先で人間が行う）。以下はその一次情報であり手動でも実行できる。**この手順・skill-deploy・deploy_skills.py は同一コミットで改訂する**（片側修正の禁止）。

1. **選ぶ** — 上の表からプロジェクトに必要なスキルを選ぶ（全部入れない。無関係なスキルは誤発動の種）
2. **コピー** — マスターのスキルは `.claude/skills/<name>/` にある。配置先の `.claude/skills/` にディレクトリごとコピーする:
   ```bash
   cp -r <マスターのパス>/.claude/skills/<name> <配置先のパス>/.claude/skills/
   ```
3. **source-commit を記録** — 各スキルの frontmatter の `metadata:` にマスターの配置時点 HEAD を追記する:
   ```yaml
   metadata:
     version: "1.0"
     source-commit: <マスターで git rev-parse HEAD した値>
   ```
   （`version` はコピー元の値を保つ — 上の例の "1.0" で上書きしない。マスター側には source-commit を書かない — 配置先にだけ意味がある情報）
4. **references を再生成** — `references/` が example と明記されているスキル（tdd / test-review / e2e / review-ui）は、配置先のスタックに合わせて中身を再生成する。対象スキルを含まない配置ではこの手順はスキップ。使わない場合は削除してよい — 本文は判断軸のみで縮退動作する
   - **マスターの references は pnpm 前提**（`pnpm test` / `pnpm run` / `pnpm exec` — exec はローカル限定実行で fetch が起きない安全なセマンティクス。pnpm v10+ は lifecycle スクリプトも既定ブロック）
   - 再生成は配置先で Claude に依頼するのが手軽。プロンプト例: 「`.claude/skills/tdd/references/patterns.md` をこのプロジェクトのテストスタック（pytest 等）に合わせて書き直して。SKILL.md 本文は変更しない」
   - **npm プロジェクト**では `pnpm test` → `npm test --`、`pnpm run X` → `npm run X --`、`pnpm exec <bin>` → `npx <bin>` に置き換える。**npx は対象が未導入だとレジストリ取得 → 即実行が走る**ため、ローカル導入済みバイナリの実行にのみ使い、`.npmrc` に `ignore-scripts=true` を設定する（手順 6 参照）
5. **CLAUDE.md に発動ポリシー節を作る** — 下の雛形から。雛形は最小セット前提なので、他のセット構成では各スキルの description の発動フレーズを元に 1 行ずつ書き換える。行動ルールは配置先で育てる（マスターの CLAUDE.md を丸ごとコピーしない）
6. **ガードレールも同送する（サプライチェーン対策）** — スキルだけコピーすると、references が指示する `npx` 実行等に対する防御が配置先に存在しない状態になる:
   - マスターの `.claude/settings.json` から **permissions（allow / ask / deny）セクション**を配置先の settings.json に取り込む（パッケージインストール deny・npx / rm -r の ask・env / 鍵ファイルの Read deny・ガードレール自己改変の ask）
   - 配置先に**既存の settings.json / permissions がある場合は手動マージ**する（丸ごと上書きしない）。方針: マスター由来の deny / ask は削らずに追加する。既存の allow とマスターの deny が同じ操作で衝突したら **deny を優先**（安全側に倒す。緩めたい場合は配置先の判断で個別に外す）
   - `.claude/hooks/guard-env-read.sh` をコピーし、settings.json の `hooks.PreToolUse` 登録も移す（deny の前置一致では防げない .env 読み取りの迂回を全文検査で ask に落とす）
   - **品質ゲート 2 本も同送する**: `post-edit-lint.sh`（編集ごとの lint 差し戻し。Biome / ESLint / Stylelint を実行時に自動検出）と `stop-typecheck.sh`（終了宣言時の tsc）。settings.json の `hooks.PostToolUse` / `hooks.Stop` 登録も移す。両方**フェイルオープン**（lint 設定・tsconfig.json が無いプロジェクトでは素通し）なのでスタックを問わず配ってよい。詳細・調整（tsc が遅い場合の外し方等）は docs/knowledge/claude-code-config.md
   - hooks のコマンド登録は `"$CLAUDE_PROJECT_DIR"` 起点の相対参照なので、`.claude/hooks/` に同じ配置でコピーすれば**パスの書き換えは不要**
   - `session-stop.sh`（Stop hook）は **knowledge-capture を配置する場合のみ**コピーする（settings.json の `hooks.Stop` 登録も同時に移す）。この hook が立てる `.capture-needed` は knowledge-capture の起動を促すフラグなので、未配置のまま同送すると「存在しないスキルの実行を促す」実行不能な指示になる
   - `settings.local.json` はコピーしない（マシン固有の承認履歴）
   - 配置先の `.npmrc` に `ignore-scripts=true` を推奨（install 時の postinstall 実行 = サプライチェーン攻撃の主経路を既定で遮断。ビルドスクリプトが必要なパッケージだけ個別に許可する運用）
   - **配置後、配置先で一度対話セッションを起動して信頼ダイアログを承認する** — 未信頼のワークスペースでは settings.json の permissions.allow が無効化される（deny / hooks は有効）。headless 運用（`claude -p`）を始める前に必須
7. **マスターの `deployments.md` に配置先を登録する** — 配置先プロジェクトの絶対パスを 1 行追記する（マスターのリポジトリルート `deployments.md`）。`deployments.md` はローカル限定で `.gitignore` 済み（絶対パス＝ユーザー名/ローカル構造を含むため git 追跡しない）。初回は雛形からコピーして作る（`cp deployments.example.md deployments.md`。`deploy_skills.py` 経由なら未存在時に自動作成される）。これで `skill-harvest`（および `check_deploy_drift.py` のレジストリモード）が、この配置先の再コピー候補・ドリフト・溜まった `skill-issues.md` を巡回できるようになる。スキル単位の記録は不要（どのスキルが入っているかは配置先の `source-commit` から発見される）
8. **スモークテスト** — 配置先で対話セッションを起動し、配置セットに応じて確認する:
   - 「どのスキルが使える？」→ 配置したスキルが一覧に出る（出ない場合は配置パス・frontmatter の破損を疑う）
   - design-doc 配置時: 小さなタスク（例:「◯◯ボタンを追加したい」）を投げ、設計の提示後に**承認待ちで停止する**こと（勝手に実装が始まったら FAIL — 配置先で直さず、事象をマスターの `skill-issues.md` 経路で報告する）
   - frontend-code-review 配置時: 小さな diff に「コードをレビューして」→ レビューが実行され指摘（または指摘なしの報告）が返ること
   - hooks / permissions 同送時: `.env` の読み取りを依頼して guard-env-read.sh が確認（ask）に落とすこと

## ドリフト確認と改善の還元

- **ドリフト確認**: マスターのリポジトリで `git diff <source-commit> -- .claude/skills/<name>` — 配置後にマスター側で入った改善が一覧できる。複数配置先をまとめて巡回するなら `skill-harvest` スキル（`deployments.md` レジストリを読む）を使う
- **改善の還元**: 配置先で直接編集しない。改善はマスターに還元し、再コピーで配る（コピー時に source-commit を更新する）。配置先に溜まった `skill-issues.md` は skill-harvest がマスターへ還流する（session-retrospective を併配していれば供給が続く）
- **配置前チェック**: マスター側で `python3 scripts/validate_skills.py` が全 PASS であることを確認してからコピーする

## CLAUDE.md 雛形（発動ポリシー節のみ）

```markdown
## スキル発動ポリシー

- 新しいタスクを開始するときは design-doc を使い、design.md が APPROVED になるまで実装しない
- 承認済み design.md からの実装は impl-from-design を使う（実装モードは TDD 推奨）
- 既存コードへのテスト追加・テストファーストの実装は tdd を使う
- 実装後のコードレビューは frontend-code-review を使う
- セッションで得た知見は knowledge-capture で docs/ に保存する
<!-- 配置したスキルに合わせて追記・削除する。行動ルール（プロジェクト固有の規約）はこの下に育てていく -->
```
