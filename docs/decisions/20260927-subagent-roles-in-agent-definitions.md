# Decision: サブエージェントの役割ごとの model / effort / tools を `.claude/agents/` の定義に集約する

Date: 20260927
Status: Accepted
Supersedes: [20260706-no-custom-reviewer-agent](20260706-no-custom-reviewer-agent.md)

## Context

20260706 にレビュー subagent は汎用ディスパッチのままとし、カスタム agent 定義を見送った。
その後、外部レポート 2 件（コスト構造レビュー・客観評価。`.steering/archived/20260917-report-driven-improvements/reports/`）
の検証で次が判明した:

- 散文によるモデル指定（`impl-tournament/references/commands.md` の「Haiku 相当に指定」）は機構を持たず、
  実際には何も指定されていなかった。役割ごとのモデル / エフォート割当を効かせる手段が定義ファイル以外に無い
- `Bash(git diff *)` で「読み取り専用」にしたつもりの agent でも、`--output=<path>` で任意ファイルへ書けることを
  実測した（review-result S1・2 軸が独立に再現）。旧 ADR の「事故は未観測」という見送り根拠のうち、
  書き込み経路の存在が実証された

## Decision

サブエージェントを起動する役割（レビュー 7 軸・premortem-attacker・codebase-explorer・tournament-variant /
-scorer・knowledge-scanner の計 12 本）を `.claude/agents/` に定義し、model / effort / tools は定義側だけに書く。
読み取り専用の役割は `Read` / `Grep` / `Glob` のみを許可する。

## Rationale

- 定義ファイルは model / effort / tools を実際に効かせる唯一の機構
- 旧 ADR が挙げたコストへの対処:
  - ポータビリティ — スキル本文は役割名で指し、定義が無い・未登録なら汎用エージェント / 自己実行へ落ちる
    フォールバックを持つ。`.claude/agents/` は配布対象外（master-only）で、配置先はフォールバックで動く
    （[[20260612-manual-copy-skill-distribution]] の自己完結を維持）
  - haiku 化の精度リスク — レビュー軸は sonnet。haiku は推論力に依存しない走査役
    （codebase-explorer / knowledge-scanner）に限定
- 読み取り専用はホワイトリスト方式にし、契約 (p) で機械検査する

## Consequences

- Good: モデル / エフォート割当が設定として効く。レビュー役の書き込み経路が消える。
  compound の知識走査（約 23k トークン）をメイン文脈から外せる
- Bad: 定義と本文の二系統を同期する必要がある（契約 (o) で突合）。
  レビュー役は git を実行できないため diff は呼び出し側がファイルで渡す（`pnpm audit` も実行不可）。
  `tournament-variant` の無制限 Bash は受容（S4）。配置先では定義の恩恵を受けない

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| 現状維持（旧 ADR のまま汎用ディスパッチ） | 散文のモデル指定が効かず、S1 型の書き込み経路も残る |
| `Bash(git diff\|log\|show *)` に絞って git を許可 | `--output` で任意パスに書ける（実測）。コマンド単位で安全に絞る手段が無い |
| スキル frontmatter に `model` / `effort` を書く | スキル単独起動時にしか効かず、サブエージェントの割当にならない（decisions 20260920 論点 3） |
| compound を `context: fork` でスキルごとにフォーク | スキルが 1 本増え（29→30）、fork 先は会話履歴を見ないため候補の引数渡し設計が別途要る。目的はサブエージェント隔離で達成できる |
| `.claude/agents/` を配置先にも配布 | 配布経路が増え隠れ依存になる。配布は BACKLOG で別途検討 |
