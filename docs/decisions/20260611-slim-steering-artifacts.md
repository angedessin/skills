# Decision: session-log.md（hook 自動記録）を廃止し .steering をスリム化する

Date: 20260611
Status: Accepted

## Context

`.steering/[task]/` には hook（session-stop.sh）が自動追記する session-log.md・
`.last-log-hash`、および design.md と分離した requirements.md があり、
タスクごとのアーティファクトとワークフローが肥大化していた。
hook はセッション終了ごとに git 情報からログを生成していたが、
内容が薄く参照されることがほぼなかった。

## Decision

- session-log.md と hook による自動記録（ハッシュ重複抑制含む）を廃止する
- requirements.md を design.md に併合する（Goal/Scope/Acceptance criteria セクションとして統合）
- hook は「アクティブタスクに capture_done がなければ .capture-needed フラグを作成する」のみ（約 20 行）に縮小する
- knowledge-capture の入力は decisions.md / review-result.md / 会話コンテキストとする

## Rationale

- hook が機械的に取れるのは git 情報のみで、**判断・学び・ハマりどころは会話の中にしかない**。decisions.md / skill-issues.md への手動追記の方が情報の質が高い
- diff 統計・変更履歴は git log で代替可能（リポジトリ自体が記録を持つ）
- requirements.md と design.md の分離は参照の手間を増やすだけで、承認ゲート（Status: APPROVED）は design.md 単体で機能する

## Consequences

- Good: セッションごとのノイズファイルが消え、hook の保守コストが最小化される
- Good: knowledge-capture の入力が「質の高い手動記録 + 会話」に揃う
- Bad: 記録が decisions.md / skill-issues.md への手動追記の規律に依存する（書かなければ残らない）
- 注: archived/ 配下の旧構造（session-log.md 等）は意図的に温存。steering spec.md に後方互換として明記済み

## Alternatives considered

| Alternative | Reason rejected |
|-------------|-----------------|
| .steering を全廃して git ブランチ + PR 説明に寄せる | 設計承認ゲートとフラグによる福利化ループの置き場が消える |
| フラグファイルを廃止して派生状態（review-result.md の未解決有無等）で判定 | hook・スキル双方の判定ロジックが複雑化する。フラグの方が単純 |
| session-log.md を残して内容を充実させる | hook は git 情報しか取れず、判断・学びは会話の中にしかない |
