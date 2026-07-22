# 引き継ぎプロンプト — スキルセット導入（会社側 AI に渡す）

以下をそのまま会社側の Claude Code セッションに貼り付けて使う。
`[セットのパス]` は持ち込んだこのディレクトリの実際のパスに置き換える。

---

このリポジトリに、外部で作成された Claude Code スキル一式を導入してください。
セットは `[セットのパス]/` にあります（`skills/` 9 個・`claude-config/`・`MANIFEST.md`）。

**まず `MANIFEST.md` を全文読んでください。** それが一次情報で、この依頼文は要約です。
食い違ったら MANIFEST が正です。

## 前提（このセットの性質）

- 対象プロジェクトは Angular / TypeScript / Jasmine。スキル本文はこのスタック向けに調整済み
- **コードレビューのスキルは含まれていない**。レビューはこの組織のレビュープラグインで行う前提。
  スキル本文にレビュー用スキルの名前は出てこない（「コードレビューを実施する」等の一般記述）。
  レビュー結果を `.steering/[task]/review-result.md` に置いておくと、knowledge-capture / compound
  が知見抽出の入力として読む（無ければ会話の文脈で代替するので、置かなくても動く）
- このセットは元リポジトリ（マスター）への還流経路を持たない**独立フォーク**として運用する。
  改善はこのリポジトリで直接編集してよいが、編集したスキルの frontmatter `metadata:` に
  `modified: "YYYY-MM-DD 変更概要"` を追記する（MANIFEST「独立運用（還流なし）のルール」参照）
- **npx は使用禁止**（settings で deny 済み）。ローカル導入済みバイナリは
  `./node_modules/.bin/<bin>` の直接実行か `npm run` 経由で呼ぶ
- 導入作業中に新しいパッケージのインストール・外部 URL の取得はしない
- スキルが `.steering/` に作る成果物（design.md・tasklist.md）の**セクション見出しは日本語**。
  ただし `Status:` 行のキーと値（`DRAFT` / `APPROVED`）は英語のまま扱う
  （impl-from-design の前提チェックが照合する契約値のため、日本語化・言い換えをしない）
- 設計・アーキテクチャの決定は `.steering/[task]/decisions.md` に「決定・理由・却下した代替案」
  の 3 点で記録する。**スキル側は決定記録の定型フォーマット（ADR 形式等）を生成しない** —
  この組織に決定記録の様式があれば、その 3 点を元に人が起票する

## 手順（MANIFEST「配置先（会社）でやること」に対応）

1. `skills/` 配下の 9 ディレクトリを `.claude/skills/` にコピーする
2. `claude-config/hooks/` の 4 本を `.claude/hooks/` にコピーする（settings の登録は
   `$CLAUDE_PROJECT_DIR` 起点なのでパス書き換え不要）
   - **先に `jq --version` を実行する。4 本中 3 本が jq に依存する**（MANIFEST 手順 2 の表を見る）。
     通らない場合、`session-start-check.sh` と `post-edit-lint.sh` は**無言で無効化される**ので、
     配置しても動かない。まず jq 導入の可否をユーザーに確認する
   - jq が使えない場合は `guard-env-read.sh` を配置せず settings の `PreToolUse` ブロックも
     入れない（フェイルクローズで全 Bash 呼び出しが確認プロンプトになるため）。**残り 2 本が
     黙って無効になっている状態であることを明示的に報告する**（黙って次の手順に進まない）
3. `claude-config/settings.example.json` を `.claude/settings.json` に**手動マージ**する。
   既存の settings を丸ごと上書きしない。既存 allow と deny が衝突したら deny を優先。
   **マージ結果の全文を提示して、承認を得てから書き込む**
4. tdd のカートリッジを作る（任意 — 無くても tdd は動く）:
   - 先に**このリポジトリの実際のテスト環境を調べる**（テストの実行コマンド・Jasmine の
     実行基盤（Karma か jest-preset-angular か等）・TestBed の使い方・既存 spec の慣習）
   - 調べた結果に合わせて `.claude/skills/tdd/references/patterns.md` を**新規作成**する
     （同梱していない。誤ったスタックの例を持ち込まないため意図的に外してある）。
     見出しは SKILL.md が参照する §名（§run / §config / §setup / §unit / §component /
     §query-ladder / §network / §state / §api-layer / §coverage）に合わせ、
     Angular に対応物が無い節は省く。**SKILL.md 本文は変更しない**
5. `CLAUDE.md` に発動ポリシー節を追加する（MANIFEST 末尾の雛形をベースに、この
   プロジェクトの運用に合わせて調整。**追加内容を提示して承認を得てから書き込む**）
6. `.gitignore` に次の 3 行を追加する:
   `.steering/**/.capture-needed` / `.steering/**/.codify-needed` / `.steering/**/capture_done`
7. `.npmrc` に `ignore-scripts=true` を設定する（既存の .npmrc がある場合は追記。
   ビルドに postinstall が必要なパッケージが既にあるか先に確認し、あれば個別許可の
   方法を提示する）
8. ここで一度停止し、ユーザーに対話セッションの再起動と信頼ダイアログの承認を依頼する
   （未信頼ワークスペースでは permissions.allow が無効のため）
9. スモークテストを実行する:
   - 「どのスキルが使える？」で 9 スキルが一覧に出ること
   - 小さなタスク依頼で design-doc が設計提示後に**承認待ちで停止する**こと
     （勝手に実装が始まったら FAIL — 結果を報告する）
   - guard-env-read.sh を配置した場合のみ: **`head .env.local`** の実行依頼が確認（ask）に
     落ちること。**`cat .env` では検証にならない**（settings の deny だけで止まるため、hook が
     動いていなくても同じ結果になる）。配置しなかった場合は ask にならないのが正しい

## 進め方の規律

- 各ステップで、何をどう変更するかを先に提示し、ユーザーの承認を得てから適用する
- 判断に迷ったら MANIFEST を参照し、それでも不明ならその場で停止して質問する
- 手順を飛ばさない。特に手順 4 は「実際のテスト環境を調べてから書く」の順序を守る
