# タスクリスト: first-deployment-run

Last updated: 20260806

## 実装前（主要コンポーネントの確定）

- [x] 配置対象パス・最小 8 スキル名・`deployments.md` / BACKLOG の触る箇所を全文検索で洗い、design.md 表と突合（漏れ＝片側修正）

## 実装

- [x] 配置前ゲート: `git -C …/skill-test rev-parse --is-inside-work-tree`（失敗なら `git init` → 再検査）
- [x] マスターで `python3 scripts/validate_skills.py` 全 PASS
- [x] `skill-deploy`: 最小セット選択 → `--dry-run` 提示 → **明示承認待ちで停止**
- [x] 承認後 `deploy_skills.py` 本実行（エラー時はリトライで書き込みを重ねない）
- [x] レジストリ確認: 正規化済み有効パス = 当該パスちょうど 1
- [x] `python3 scripts/check_deploy_drift.py` が **exit 0**（当該パスが出力に含まれる）
- [x] スモーク: スキル一覧 + design-doc **明示指定**で承認停止（自動発動は対象外）— CLI で DRAFT 提示後に承認待ち停止を確認（20260806）。一覧は目視 + `ls .claude/skills`（専用 CLI サブコマンドは無し）
- [x] skill-deploy Step 4 残タスクを案内（CLAUDE.md / references 再生成はブロッカーにしない・縮退受容）
- [x] `.steering/BACKLOG.md` 節 4 から「配置1件実走」を削除（節 2(b) も完了反映）
- [x] 実走摩擦があれば契約/手順/機械検査を同一ブランチで修正（説明文のみ禁止）— Write(path) 削除 + 契約 (j) + 文書/hook 同期 + skill-test 手直し



## レビュー

- [x] マスター差分のレビュー — **ユーザーが PR 上でレビュー**（frontend-code-review はスキップ。20260806 決定）
- [x] レビュー指摘の修正 — 提出時点では無し（指摘があれば pr-feedback）

## 知見保存（この PR / ブランチに載せる分）

- [x] `decisions.md` に配置先パス・セット・有効行 1 の証跡（`deployments.md` は git 外）
- [x] knowledge-capture — PR 差分の知見は decisions / skill-issues / claude-code-config に反映済み。追加 docs なし

## デプロイ

- [ ] PR 作成（base = `integration/20260730-reports`）— **マージは人間の明示指示までしない**
- [ ] CI があればグリーン確認

## 福利化

- [ ] compound（`.codify-needed` があれば確認）— Write(path) 修正は本 PR で契約化済み。追加昇格は任意

## クローズ

- [ ] steering archive（親へのマージ前にアーカイブまで）
