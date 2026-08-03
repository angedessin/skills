# タスクリスト: capture-granularity

Last updated: 20260803

## 実装前（必須）

- [x] 変更対象の洗い出し: `rg -n 'knowledge-capture を実行しますか|未保存ナレッジ|capture-needed|capture_done|省略してアーカイブ|明示的に省略' --glob '!**/archived/**'` で design.md 主要コンポーネント表と突合し、漏れを表へ追加してから実装する

## 実装

- [x] `session-start-check.sh`: 注入文を三択（今 / 後で / スキップ）へ
- [x] `knowledge-capture/SKILL.md`: フラグ起点の三択再掲（SessionStart 操作定義は hook 注入文と同一）・codify より先
- [x] `CLAUDE.md`: 三択の任意再掲（スキップ＝`rm`・効果＝次 Stop まで／後で＝残置／今＝KC）
- [x] `steering/SKILL.md` archive: ハードストップ＋「知見なしでアーカイブ」＋`[x]`/汎用省略非充足
- [x] `steering/references/spec.md`: 同上に同期
- [x] `docs/starter-kit.md` / `docs/user-guide.md` / `README.md`: 確認文言・スキップ寿命を現行形へ
- [x] `validate_skills.py`: capture-granularity キー共存＋空文限界コメント
- [x] `.steering/BACKLOG.md` 節 4 の「capture 粒度」行を削除（着手時済み）

## 検証

- [x] `bash -n` on 変更した hooks
- [x] `pnpm run validate`（32/32・capture-granularity PASS）
- [x] session-stop フィクスチャ: 作りたてスキップ / `capture_done` 時スキップ / **スキップ後再立て**
- [x] 三択各枝と archive ハードストップ — 一回限り: validate キー共存 + stop フィクスチャ + PR レビューで代替（実セッション三択は未実測）

## レビュー

- [x] frontend-code-review の実行
- [x] レビュー指摘の修正（review-result.md を参照）
- [x] 修正後の差分再レビュー（Medium 3 件解消・RESOLVED）

## 知見保存（この PR / ブランチに載せる分）

- [x] knowledge-capture — 追加 docs なし（decisions / SKILL / validate で足りる）。`capture_done`
- [x] docs 追加なし

## デプロイ

- [x] PR 作成（base = `integration/20260730-reports`） https://github.com/angedessin/skills/pull/9
- [x] CI なし（checks 空）
- [x] マージ（https://github.com/angedessin/skills/pull/9 → integration）

## 福利化

- [x] compound — 追加昇格なし（skill-design-patterns 既存原則でカバー）。codify-log 記載

## クローズ

- [x] knowledge-capture（横断残りなし）
- [x] steering archive モードでアーカイブ

Archived: 20260804
