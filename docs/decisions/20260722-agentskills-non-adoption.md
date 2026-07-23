# Decision: agentskills 由来の 3 項目を採用しない（allowed-tools / eval ループ / npx・uvx ランナー）

Date: 20260722
Status: Accepted

## Context

20260709 に agentskills.io（クロスベンダーの Agent Skills 仕様）とこのリポジトリの運用差分を棚卸しした。その結果、採用候補とされた 3 点が「このリポジトリの既存方針と衝突する」と判定され見送りが確定したが、ADR 化のタスクが未実施のまま `.steering/archived/20260709-agentskills-alignment/` がアーカイブされた（`tasklist.md:13` が未チェック）。

判断の根拠がアーカイブ済みタスクの中にしか無いため、20260722 に「skill に allowed-tools の記載は不要か」という形で同じ論点が蒸し返された。判例として一度だけ書き残す。

## Decision

次の 3 項目を採用しない。将来採用を検討する場合は、本 ADR に書かれた却下理由が失効したことを先に示す。

1. SKILL.md frontmatter の `allowed-tools`（および `disallowed-tools` 等の同系フィールド）
2. トリガー評価ループ・出力評価ループ（課金を伴う反復実行による最適化）
3. npx / uvx による一回性ランナーの推奨

## Rationale

**1. `allowed-tools`** — このフィールドは「ツールの制限」ではなく、スキル起動ターン限りのパーミッション事前承認であり、書かなくてもスキルは動く（公式 frontmatter リファレンス上 Required: No。`description` のみ recommended）。一方、権限はこのリポジトリでは settings.json で一元管理している。得られるのは「プロンプトが減る」だけで、代わりに Claude Code 固有拡張への依存が増え、クロスクライアント可搬性という明示的設計目標（`20260612-manual-copy-skill-distribution.md` が前提とする単体コピー配布）を自ら削る。

**2. eval ループ** — トリガー評価は 20 クエリ × 3 ラン × 反復で 60 回以上の課金実行になる。ミストリガーは既に `skill-issues.md` に無料で蓄積され compound が回収する経路があり、個人利用で統計的トリガー率を測る便益がコストに見合わない。

**3. npx / uvx ランナー** — 「fetch しない・`pnpm exec` を使う」という既存ポリシーと正面衝突する。スクリプト設計の原則（明確なエラーメッセージ・構造化出力）だけを取り、ランナー推奨は採らない。

## Consequences

- Good: 全スキルの frontmatter が `name` / `description` / `compatibility` / `metadata` に揃い、単体コピーでの可搬性が保たれる
- Good: 蒸し返し時に判断を再構成せず ADR 1 本で決着する（本 ADR の起票動機そのもの）
- Bad: スキル同梱スクリプトを持つスキルが増えた場合、`allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/*.sh *)` による無プロンプト実行という利便を取り逃す。**再検討のトリガーはこれ** — `scripts/` を持つ配布可スキルが実際に増え、パーミッションプロンプトの摩擦が実証されたときに限り再考する（「自動化は摩擦が実証されてから」の原則に従う）
- Bad: 20260709 時点の却下理由にあった「仕様が Experimental」は 20260722 の再確認時点で公式 docs に該当表記がなく、既に失効している。可搬性の論点のみが現行の根拠

## Alternatives considered

| Alternative | Reason rejected |
|-------------|-----------------|
| `allowed-tools` を採用しパーミッションをスキル側に持たせる | 権限の管理点が settings.json とスキルに二重化する。Claude Code 固有拡張への依存で可搬性を毀損。得るものは無プロンプト実行のみ |
| `allowed-tools` を validator の warn 対象にする（20260709 の私案） | 「起きない事象への保険」。このリポジトリのスキルは誰も書いていない。security-audit が第三者スキルの広範な権限要求としてスキャンする経路で足りる |
| トリガー評価ループを 1 スキルに限定して実施 | 将来やるならこの形が上限、と留保はする。現時点では誤発動報告が特定スキルに集中しておらず対象を選べない |
| npx / uvx をスクリプト配布に使う | pnpm ポリシーと衝突。fetch を伴う実行はサプライチェーン監査の対象を増やす |
