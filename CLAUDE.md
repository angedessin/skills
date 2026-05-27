# skills — personal frontend workflow skill set

Tech stack: Next.js / TypeScript / Vitest / React Testing Library / MSW / Playwright

## .steering ルール

新しいタスクを開始するときは必ず:
1. `design-doc` スキルを使い `.steering/[YYYYMMDD]-[task]/` を作成
2. `design.md` 作成後は人間のレビュー待ちで止まること（実装に入らない）
3. 作業完了後は必ず `tasklist.md` を更新すること

セッション開始時:
1. 必ず `find .steering -name '.capture-needed' 2>/dev/null` を Bash で実行して確認
2. `.capture-needed` があれば「前回セッションのナレッジが未保存です。knowledge-capture を実行しますか？」と確認
3. `.steering/` のアクティブタスクをすべて読んでから作業開始
4. 複数のアクティブタスクがある場合はどれを再開するか確認

## ナレッジ保存先のルール

CLAUDE.md は行動ルールのみ。知識の倉庫にしない（毎回コンテキストを消費するため）。

| 種類 | 保存先 |
|---|---|
| 行動ルール（短い命令形） | このファイル or `~/.claude/CLAUDE.md` |
| 経験・パターン・アンチパターン | `docs/knowledge/[topic].md`（@参照で読む） |
| 設計判断（ADR） | `docs/decisions/[date]-[slug].md` |
| タスク固有の決定 | `.steering/[task]/decisions.md` |

## ドキュメント参照（必要なトピック作業時のみ）

テスト実装時: @docs/knowledge/testing-patterns.md

## スタック制約（行動ルール）

- `vi.mock` でネットワーク系のモックは禁止（MSW の `http.*` を使う）
- RTL クエリ: `role > label > text > testId` の優先順位を守る
- Playwright: `waitForTimeout` 禁止
- `as any` / `as unknown` の不用意な使用禁止
- `<div onClick>` → `<button>` に置き換える
