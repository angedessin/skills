---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, TodoWrite]
append_system_prompt: |
  # Project instructions (CLAUDE.md)
  ## .steering ルール
  新しいタスクを開始するときは必ず:
  1. `design-doc` スキルを使い `.steering/[YYYYMMDD]-[task]/` を作成
  2. `design.md` の提示後は人間のレビュー待ちで止まること（実装に入らない）
  3. 作業完了後は必ず `tasklist.md` を更新すること
---

商品検索に、価格の安い順・高い順の並び替えと、カテゴリでの絞り込みを追加したい。設計から始めて。
