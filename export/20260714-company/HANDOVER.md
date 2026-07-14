# 引き継ぎプロンプト — スキルセット導入（会社側 AI に渡す）

以下をそのまま会社側の Claude Code セッションに貼り付けて使う。
`[セットのパス]` は持ち込んだこのディレクトリの実際のパスに置き換える。

---

このリポジトリに、外部で作成された Claude Code スキル一式を導入してください。
セットは `[セットのパス]/` にあります（`skills/` 17 個・`claude-config/`・`MANIFEST.md`）。

**まず `MANIFEST.md` を全文読んでください。** それが一次情報で、この依頼文は要約です。
食い違ったら MANIFEST が正です。

## 前提（このセットの性質）

- 対象プロジェクトは Angular / TypeScript / Jasmine。スキル本文はこのスタック向けに調整済み
- このセットは元リポジトリ（マスター）への還流経路を持たない**独立フォーク**として運用する。
  改善はこのリポジトリで直接編集してよいが、編集したスキルの frontmatter `metadata:` に
  `modified: "YYYY-MM-DD 変更概要"` を追記する（MANIFEST「独立運用（還流なし）のルール」参照）
- **npx は使用禁止**（settings で deny 済み）。ローカル導入済みバイナリは
  `./node_modules/.bin/<bin>` の直接実行か `npm run` 経由で呼ぶ
- 導入作業中に新しいパッケージのインストール・外部 URL の取得はしない

## 手順（MANIFEST「配置先（会社）でやること」に対応）

1. `skills/` 配下の 17 ディレクトリを `.claude/skills/` にコピーする
2. `claude-config/hooks/` の 5 本を `.claude/hooks/` にコピーする（settings の登録は
   `$CLAUDE_PROJECT_DIR` 起点なのでパス書き換え不要）
3. `claude-config/settings.example.json` を `.claude/settings.json` に**手動マージ**する。
   既存の settings を丸ごと上書きしない。既存 allow と deny が衝突したら deny を優先。
   **マージ結果の全文を提示して、承認を得てから書き込む**
4. references を再生成する:
   - 先に**このリポジトリの実際のテスト環境を調べる**（テストの実行コマンド・Jasmine の
     実行基盤（Karma か jest-preset-angular か等）・TestBed の使い方・既存 spec の慣習）
   - 調べた結果に合わせて `.claude/skills/tdd/references/patterns.md` と
     `.claude/skills/test-review/references/patterns.md` を書き直す（現在は Vitest 前提の
     example）。**SKILL.md 本文は変更しない**
   - `.claude/skills/review-ui/references/tokens.md` はこのプロジェクトのデザイントークン
     定義があれば再生成、無ければ削除する（本文は縮退動作する）
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
   - 「どのスキルが使える？」で 17 スキルが一覧に出ること
   - 小さなタスク依頼で design-doc が設計提示後に**承認待ちで停止する**こと
     （勝手に実装が始まったら FAIL — 結果を報告する）
   - 小さな diff への「コードをレビューして」で frontend-code-review が動くこと
   - `.env` の読み取り依頼が guard-env-read.sh により確認（ask）に落ちること

## 進め方の規律

- 各ステップで、何をどう変更するかを先に提示し、ユーザーの承認を得てから適用する
- 判断に迷ったら MANIFEST を参照し、それでも不明ならその場で停止して質問する
- 手順を飛ばさない。特に手順 4 は「実際のテスト環境を調べてから書く」の順序を守る
