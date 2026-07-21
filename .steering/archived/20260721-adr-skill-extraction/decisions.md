# Decisions: 20260721-adr-skill-extraction

## 20260721 — ADR の起票・維持を master-only スキル adr に切り出す

**Decision**: ADR の起票・Nygard 形式・Superseded/Amended 運用・近縁検出を master-only スキル
`adr` に移し、配布可の knowledge-capture からは ADR の語彙・形式・書き込みを全削除する
**Reason**: ADR の権威は批准プロセスから来るため、批准の仕組みを持たない配置先で単独生成すると
公式記録と競合する「影の決定ログ」になる。加えて増え続ける ADR 群の維持は「知見を振り分ける」
責務と別物
**Alternatives**: 出力先のカートリッジ化 / 配布版に 1 分岐残す / 配布版が Nygard ドラフトを提示 /
adr も配布可にする（すべて却下。理由は ADR 本文の Alternatives considered 参照）
**Impact**: 配布可スキル 5 本 + ドキュメント 4 種 + deploy_skills.py
→ **ADR 起票済み**: [docs/decisions/20260721-adr-as-master-only-skill.md](../../docs/decisions/20260721-adr-as-master-only-skill.md)（こちらが現行の決定記録）

## 20260721 — 配布可スキルに master-only スキル名を書かない

**Decision**: compound / rule-audit / session-retrospective / feature-pipeline /
steering references から ADR の帰属記述を**削除**する（`adr` に置き換えない）
**Reason**: 配置先には存在しないスキル名を指す死んだ参照になる。design-premortem が
Constraints と Key components の直接矛盾として検出した
**Impact**: 境界の相互明記が不要になり、同じ入力を読むスキルが 3 本になるコストを構造的に回避

## 20260721 — 近縁検出は Superseded 済みも対象に含める（Open questions 3）

**Decision**: `adr` の近縁検出は Superseded 済み ADR も走査対象にし、候補提示時に
「Superseded 済み」と明示する
**Reason**: 除外すると、置き換え済みの決定を再提案しても検出されない穴が開く。
明示すれば「なぜ古い決定を読むのか」にも答えられる
**Alternatives**: 除外する（却下 — 穴の方が高くつく）
**Impact**: adr スキル Step 2

## 20260721 — 「定型フォーマットを生成しない」は静的で締める（Open questions 4）

**Decision**: 禁止句の明示ステップ化 + grep による静的プロキシで受け入れ、
素通り検査（課金）は回さない
**Reason**: 「自動化・課金は摩擦が実証されてから」の既存方針と一貫させる
**Alternatives**: `tests/passthrough_check.py` に 1 シナリオ追加（却下 — 実害の観測が先）
**Impact**: **再検討トリガー**: knowledge-capture が決定記録の定型フォーマットを生成したのを
一度でも観測したら、シナリオを追加する

## 20260721 — ADR の置き場は docs/decisions/ のまま

**Decision**: `docs/adr/` へ改名しない
**Reason**: `docs/decisions/` は MADR のデフォルトで既に標準的。スキル名とディレクトリ名が
一致する必要もない（knowledge-capture → docs/knowledge/ も一致していない）
**Alternatives**: `docs/adr/` へ改名（却下 — CLAUDE.md・README・rule-audit・既存 7 本の
相互リンクが追随対象になり、片側修正のリスクだけ増えて機能的な利得がない）

## 20260721 — 実装中に判明した追加対象（設計からの乖離）

**Decision**: `scripts/deploy_skills.py:45` の `MASTER_ONLY` と
`.claude/skills/skill-deploy/SKILL.md:51` の 2 箇所を Key components に追加した
**Reason**: Open questions 5（除外リストの実体確認）の過程で判明。`deploy_skills.py:6` に
「同一コミットで改訂する（片側修正の禁止）」と明記されていたため両方を同一コミットで修正
**Impact**: `adr` は配置対象に指定されても実行時に機械的に拒否される
