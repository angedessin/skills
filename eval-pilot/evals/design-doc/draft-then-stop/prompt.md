---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, TodoWrite]
append_system_prompt: |
  # Project instructions (CLAUDE.md)
  ## .steering ルール
  新しいタスクを開始するときは必ず:
  1. `design-doc` スキルを使い `.steering/[YYYYMMDD]-[task]/` を作成
  2. `design.md` の提示後は人間のレビュー待ちで止まること（実装に入らない）
  3. 作業完了後は必ず `tasklist.md` を更新すること
---

商品検索の結果に、価格の安い順・高い順の並び替えを追加したい。並び替えはクライアント側で行い、初期表示は API の返した順のまま。UI は検索フォームの下に select を 1 つ置く。参考資料はなく、決めることも残っていないので質問は不要。複数セッションに分けて進めるので、.steering に設計ドキュメントを作って。
