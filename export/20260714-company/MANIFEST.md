# 持ち出しセット — 会社ワークフロー用（20260714）

- **マスターコミット**: `3f1b595d88192f0c91a1587dc03a16bec2c65309`
- **作成日**: 2026-07-14
- **検証**: validate_skills.py 28/28 PASS（コピー元）。ローカルパス・個人情報・外部 URL の混入なし（grep 検査済み）
- 各スキルの frontmatter `metadata.source-commit` に上記ハッシュを記録済み（配置先での手動追記は不要）
- **Angular 適用版**: マスター（React / Vitest 前提）から、レビュー系 6 スキル（impl-review・review-a11y / correctness / performance / security / ui）・frontend-code-review・tdd・test-review の本文・コード例・スコープ（.tsx → .ts / .html）を Angular / Jasmine 向けに書き換え済み。書き換え後に React 語彙の残存ゼロを機械確認済み。**マスターとの diff を確認するときはこの変換分を差し引いて見る**（スキルの手順・停止契約は変えていない。変えたのはスタック語彙とコード例のみ）

## 会社ワークフローとの対応

| 会社のワークフロー | 同梱スキル |
|---|---|
| 1. 計画 | design-doc / design-premortem / steering |
| 2. テスト計画、実装 | impl-from-design |
| 3. テスト実装 | tdd |
| 4. レビュー、テストレビュー | frontend-code-review / impl-review / test-review / review-a11y / review-correctness / review-performance / review-security / review-ui |
| 5. 知見記録 | knowledge-capture / compound |
| （横断）オーケストレーター | feature-pipeline |
| （横断）摩擦の起票（還流の producer） | session-retrospective |

## 同梱しなかったもの（必要なら後から追加）

- **pr-create / pr-feedback / debug** — PR 運用・障害調査は会社の既存プロセスとの整合を確認してから。feature-pipeline は未配置フェーズをスキップして報告する縮退動作を持つため、欠けていても壊れない
- **e2e** — 会社では E2E テストを行っていないため除外。導入することになったらマスターから追加コピーする
- **impl-tournament** — N 並列実装で課金が大きい。必要になったら個別判断
- **skill-deploy / skill-harvest / skill-test / rule-audit / empirical-prompt-tuning / security-audit** — マスター専用またはメタ運用ツール

## 配置先（会社）でやること

1. `.claude/skills/` に `skills/` 配下のディレクトリをそのままコピーする
2. **hooks を配置する** — `claude-config/hooks/` の 5 本を配置先の `.claude/hooks/` にコピーする。settings.json のコマンド登録は `"$CLAUDE_PROJECT_DIR"` 起点の相対参照なので、同じ配置ならパスの書き換えは不要
   - `session-start-check.sh`（SessionStart）: 未処理フラグ・アクティブタスクをセッション開始時に注入
   - `session-stop.sh`（Stop）: `.capture-needed` を立てて knowledge-capture の起動を促す
   - `guard-env-read.sh`（PreToolUse）: deny の前置一致をすり抜ける .env 読み取りを全文検査で ask に落とす
   - `post-edit-lint.sh`（PostToolUse）: 編集ごとの lint 差し戻し（Biome / ESLint / Stylelint を自動検出）
   - `stop-typecheck.sh`（Stop）: 終了宣言時の tsc
   - post-edit-lint / stop-typecheck は**フェイルオープン**（lint 設定・tsconfig が無ければ素通し）なのでスタックを問わず置いてよい
3. **settings をマージする** — `claude-config/settings.example.json` を配置先の `.claude/settings.json` に**手動マージ**する（丸ごと上書きしない）。既存の allow と deny が同じ操作で衝突したら **deny を優先**（安全側）。マスターとの差分として **npx は全面 deny** に強化済み（下の「npx 禁止」参照）
4. **references の再生成（配置先の AI に依頼する）** — tdd / test-review の `references/patterns.md` は **Vitest / RTL / MSW 前提の example のまま**同梱している（本文は Jasmine 前提に書き換え済み）。配置先で AI に実際のテスト環境（Jasmine の実行方法・TestBed の使い方・既存テストの慣習）を確認させてから再生成を依頼する（例:「このプロジェクトの実際のテスト構成を確認して、`.claude/skills/tdd/references/patterns.md` を Jasmine / TestBed に合わせて書き直して。SKILL.md 本文は変更しない。npx は使わない」）。review-ui の `references/tokens.md` も配置先のデザイントークンで再生成する（無ければ削除してよい — 本文は縮退動作する）
5. **CLAUDE.md に発動ポリシー節を作る**（下の雛形を貼って調整）
6. **`.gitignore` に 3 行追加**: `.steering/**/.capture-needed` / `.steering/**/.codify-needed` / `.steering/**/capture_done`
7. **`.npmrc` に `ignore-scripts=true` を設定**（install 時の postinstall 実行＝サプライチェーン攻撃の主経路を既定で遮断）
8. **一度対話セッションを起動して信頼ダイアログを承認する** — 未信頼のワークスペースでは settings.json の permissions.allow が無効化される（deny / hooks は有効）
9. **スモークテスト**:
   - 「どのスキルが使える？」→ 配置したスキルが一覧に出る
   - 小さなタスクを依頼 → design-doc が設計提示後に**承認待ちで停止する**（勝手に実装が始まったら FAIL）
   - 小さな diff に「コードをレビューして」→ frontend-code-review が指摘（または指摘なし）を返す
   - `.env` の読み取りを依頼 → guard-env-read.sh が確認（ask）に落とす
10. 気づいた不具合・誤発動は `.steering/[task]/skill-issues.md` に起票する（session-retrospective が拾う）。**配置先でスキル本文を直接編集しない** — 改善点はマスターに持ち帰って反映し、再コピーで配る

### npx 禁止（このセットの方針）

**npx は使わない**（未導入バイナリだとレジストリ取得→即実行が走るため）。settings.example.json で
`Bash(npx)` / `Bash(npx *)` / `Bash(npm exec *)` を deny 済み。references を npm プロジェクト向けに
再生成するときも npx へ置き換えず、**ローカル導入済みバイナリを `./node_modules/.bin/<bin>` の直接実行
または package.json の scripts（`npm run <script>`）経由で呼ぶ**よう指定する。

### マスターから同梱しなかった hook

- `validate-skill-edit.sh` — マスター専用（`scripts/validate_skills.py` に依存。スキル編集の機械検証はマスターで行う）

## CLAUDE.md 雛形（発動ポリシー節）

```markdown
## スキル発動ポリシー

- 新しいタスクを開始するときは design-doc を使う。1 セッション完結の見込みなら会話内設計・複数セッションなら .steering/（どちらにするかは design-doc がユーザーに確認する）。いずれも設計の承認までは実装しない
- 承認済み design.md からの実装は impl-from-design を使う（実装モードは TDD 推奨）
- 既存コードへのテスト追加・テストファーストの実装は tdd を使う
- 実装後のコードレビューは frontend-code-review、テストコードのレビューは test-review を使う
- セッションで得た知見は knowledge-capture で docs/ に保存し、ルール・スキルへの昇格は compound を使う
- セッション終盤に session-retrospective で摩擦を .steering/[task]/skill-issues.md に起票する
```

## 持ち帰り（還流）の運用ルール

- 持ち帰ってよいのは**スキルそのものへの汎用的な改善点**のみ（誤発動した・手順が曖昧だった等）
- 会社のコード・業務文脈を含む内容は持ち帰らない（skill-issues.md の内容は選別してから）
- マスター側の更新をこのセットに反映する場合は、マスターで `git diff 3f1b595 -- .claude/skills/<name>` で差分を確認して再エクスポートする
