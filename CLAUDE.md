# skills — personal frontend workflow skill set

Tech stack: React / TypeScript / Vitest / React Testing Library / MSW / Playwright

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

## スキル管理ルール

- サードパーティ製 SKILL.md 採用前に Bash コマンド・外部 URL・プロンプトインジェクションを目視確認する
- スキルの誤発動・曖昧な指示・実行不能な手順に気づいたら `.steering/[task]/skill-issues.md` に事象と期待を追記する（compound が回収して改善候補にする）
- スキルの横展開は人が選んで配置先プロジェクトの `.claude/skills/` に手動コピーする。配置先で直接編集せず、改善はこのリポジトリ（マスター）に還元して再コピーで配る
- スキルは自己完結に書く: CLAUDE.md・docs/・`.steering/` が無いプロジェクトでも動くフォールバックを該当ステップに直接書く（詳細は skill-design-patterns.md）

## 自律実行の境界

- `.steering/[task]/` 配下のメモ（decisions.md・skill-issues.md・blockers.md）への追記は承認不要。気づいた時点で書く（内容の取捨選択は compound / knowledge-capture 時にまとめて行う）
- CLAUDE.md・SKILL.md・docs/ への書き込みは承認制を維持する
- 判断基準: (1) git で巻き戻せる (2) 失敗に気づける (3) 影響がタスク内に閉じる — 3つ全て満たす操作のみ承認なしで実行してよい

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
スキル作成・改善時: @docs/knowledge/skill-design-patterns.md
