# タスクリスト: capture-granularity

Last updated: 20260803

## 実装前（必須）

- [x] 変更対象の洗い出し: `rg -n 'knowledge-capture を実行しますか|未保存ナレッジ|capture-needed|capture_done|省略してアーカイブ|明示的に省略' --glob '!**/archived/**'` で design.md 主要コンポーネント表と突合し、漏れを表へ追加してから実装する

## 実装

- [x] `session-start-check.sh`: 注入文を三択（今 / 後で / スキップ）へ
- [x] `CLAUDE.md`: 三択の操作正本（スキップ＝`rm`・効果＝次 Stop まで／後で＝残置／今＝KC）
- [x] `knowledge-capture/SKILL.md`: フラグ起点の三択再掲（正本は CLAUDE.md と同一契約）・codify より先
- [x] `steering/SKILL.md` archive: ハードストップ＋「知見なしでアーカイブ」＋`[x]`/汎用省略非充足
- [x] `steering/references/spec.md`: 同上に同期
- [x] `docs/starter-kit.md` / `docs/user-guide.md` / `README.md`: 確認文言・スキップ寿命を現行形へ
- [x] `validate_skills.py`: capture-granularity キー共存＋空文限界コメント
- [x] `.steering/BACKLOG.md` 節 4 の「capture 粒度」行を削除（着手時済み）

## 検証

- [x] `bash -n` on 変更した hooks
- [x] `pnpm run validate`（32/32・capture-granularity PASS）
- [x] session-stop フィクスチャ: 作りたてスキップ / `capture_done` 時スキップ / **スキップ後再立て**
- [ ] 三択各枝と archive ハードストップ（機械検査外は「一回限り」）— レビュー前に一回限り手動確認可

## レビュー

- [x] frontend-code-review の実行
- [x] レビュー指摘の修正（review-result.md を参照）
- [x] 修正後の差分再レビュー（Medium 3 件解消・RESOLVED）

## 知見保存（この PR / ブランチに載せる分）

- [ ] knowledge-capture スキルの実行（PR 差分に属する知見）
- [ ] 必要なら docs/ への追記をこのブランチでコミット

## デプロイ

- [ ] PR 作成（base = `integration/20260730-reports`）
- [ ] CI グリーン確認
- [ ] マージは人間の明示指示後のみ

## 福利化

- [ ] compound スキルの実行（パターンをルール・知識に昇格）

## クローズ

- [ ] knowledge-capture（会話由来・横断の残りがあれば）
- [ ] steering archive モードでアーカイブ
