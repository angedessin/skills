## .steering ルール

新しいタスクを開始するときは必ず:
1. `design-doc` スキルを使い `.steering/[YYYYMMDD]-[task]/` を作成（1セッションで完結する見込みのタスクは、design-doc がユーザーに確認して会話内設計が選ばれた場合のみ `.steering/` を作らず縮退する。Claude の見積もりだけで縮退を確定しない。feature-pipeline 配下では常に作成）
2. `design.md`（会話内設計の場合は設計方針）の提示後は人間のレビュー待ちで止まること（実装に入らない）
3. 作業完了後は必ず `tasklist.md` を更新すること

