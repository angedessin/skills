# Design: skill-portability

Created: 20260703
Status: **APPROVED**
Approved: 20260703

> 設計素材: [ai-driven-frontend-workflow-plan.md](../../docs/ai-driven-frontend-workflow-plan.md) 6-1/6-2 / [issues-and-plan.md 論点 4-B/4-C](../../docs/skillset-improvement/issues-and-plan.md) / [ADR 20260612 手動コピー配布](../../docs/decisions/20260612-manual-copy-skill-distribution.md)

## Goal

手動コピー配布を支える機構を整備する。ADR 20260612 の規律（マスター還元・source-commit 記録）は確立しているが支える仕組みが無く、(1) ドリフト追跡が手作業、(2) 配置のたびに取捨選択と生成を頭から考える、(3) frontmatter・構造の検証が目視 — の 3 点が「次フェーズ」のまま止まっている。これを metadata 導入・検証スクリプト・スターターキットで埋め、新規プロジェクトへの配置を「考える作業」から「選ぶ作業」にする。

## Scope

### In scope

1. **`metadata.version` の全 19 スキル導入（4-B）** — frontmatter に `metadata: {version: "1.0"}` を一括付与。`source-commit` はマスターには置かず、**配置時に配置先で追記する**（スターターキットの配置手順に明記）
2. **検証スクリプト `scripts/validate_skills.py` 新設（4-C）** — name=ディレクトリ名 / description ≤1024 文字・引用符付き / 本文 ≤500 行 / アストラル面絵文字なし / metadata.version 必須、を機械検証。skills-ref CLI はインストールしない（依存追加を避け、同等チェックを自前で持つ）
3. **スターターキット `docs/starter-kit.md` 新設** — 推奨構成表（最小 / 拡張）+ 配置手順（コピー → source-commit 記録 → references 再生成 → CLAUDE.md 雛形）+ CLAUDE.md 雛形（発動ポリシー節のみ）を 1 ファイルに
4. **README 横展開節の拡充** — 配布方式の段階基準表（計画 6-1: 手動コピー → スターターキット+記録自動化 → プラグイン化/ADR 改訂）+ starter-kit.md へのリンク
5. **rule-audit Step 4 の 1 行改訂** — 手動同等チェックの代わりに `scripts/validate_skills.py` を「あれば使う」（無ければ従来の手動チェック）

### Out of scope

- 配置を自動化するスクリプト（コピー先の選定は人が行う — ADR 20260612 の核心。記録の自動化は「拡大」段階になってから）
- プラグイン化・テンプレートリポジトリ化（チーム標準化の段階で ADR 改訂とセットで判断）
- GitHub Actions への validate 組み込み（push 運用が定着してから。ローカルスクリプトで先に価値を出す）
- skill-creator による baseline 比較（説明責任・評価の別項目。課金ありのため個別判断）

## Constraints

- `metadata` は agentskills.io 仕様のフィールド（論点 4-B で採用決定済み）。既存 frontmatter（name / description / compatibility）の順序・内容は変えない
- 検証スクリプトは Python 標準ライブラリのみ（依存ゼロ。このリポジトリに package.json や venv を持ち込まない）
- スターターキットの CLAUDE.md 雛形は「発動ポリシー節のみ」— 行動ルールは配置先が育てる（計画 6-2 の確定事項）
- version の運用: 人間向けの粗いラベル（大改訂で上げる）。真のドリフト追跡は source-commit + `git diff <hash>` が担う
- 絵文字なし・既存ドキュメントの表記と整合

## Acceptance criteria

- [ ] 全 19 スキルの frontmatter に `metadata.version: "1.0"` があり、既存フィールドが壊れていない（validate スクリプトで全パス確認）
- [ ] `scripts/validate_skills.py` が存在し、全 19 スキルに対して 5 項目の検証を実行して PASS/FAIL を報告する。意図的に壊した frontmatter を検出できる（動作確認）
- [ ] `docs/starter-kit.md` が存在し、最小/拡張の構成表・配置 5 手順・CLAUDE.md 雛形を含む
- [ ] README 横展開節に段階基準表と starter-kit.md へのリンクがある
- [ ] rule-audit Step 4 が validate スクリプトを「あれば使う」形で参照している
- [ ] 構造検証パス（アストラル面絵文字・行数）

## Approach

マスターには `version` のみ持たせ、`source-commit` は配置時に配置先で追記する — マスター自身に自コミットハッシュを埋めると commit のたびに陳腐化する自己参照になるため（4-B の記述を実装形に落とす際の核心判断）。検証は skills-ref CLI をインストールせず標準ライブラリの自前スクリプトで同等チェックを実装する: 依存ゼロで「あれば使う」問題自体を消し、rule-audit Step 4・新スキル作成時の受け入れ検証・配置前チェックの 3 場面で同じスクリプトを使い回す。スターターキットは 1 ファイル（docs/starter-kit.md）に集約し、配置先に持っていくのは skills ディレクトリだけで済む形を保つ。

## Key components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| metadata 一括付与 | `.claude/skills/*/SKILL.md`（19 ファイル） | frontmatter 末尾に `metadata: {version: "1.0"}` を追加（スクリプトで一括 + validate で確認） |
| validate_skills.py（新設） | `scripts/validate_skills.py` | 5 項目の機械検証（name 一致 / description / 行数 / 絵文字 / metadata.version）。終了コードで PASS/FAIL |
| starter-kit.md（新設） | `docs/starter-kit.md` | 推奨構成表 + 配置手順（source-commit 記録含む）+ CLAUDE.md 雛形 |
| README 横展開節 | `README.md` | 段階基準表 + starter-kit リンク |
| rule-audit 改訂（1 行） | `.claude/skills/rule-audit/SKILL.md` | Step 4 で validate_skills.py を「あれば使う」 |

## Data flow

```
マスター側（このリポジトリ）:
  スキル改訂 → validate_skills.py で構造検証 → コミット
  （rule-audit の定期監査でも同スクリプトを利用）

配置側（他プロジェクト、starter-kit.md の手順）:
  1. docs/starter-kit.md の構成表からスキルを選ぶ（人が選ぶ — ADR の核心）
  2. .claude/skills/ にコピー
  3. 各スキルの frontmatter に source-commit: <マスターの HEAD> を追記
  4. references/（example）を自分のスタック用に再生成 or 削除（縮退動作に任せる）
  5. CLAUDE.md 雛形から発動ポリシー節を作る
  ドリフト確認: マスターで git diff <source-commit> -- .claude/skills/<name>
  改善はマスターに還元 → 再コピー（source-commit を更新）
```

## Test strategy

- validate_skills.py の動作確認: 全 19 スキルで PASS を確認 → 一時的に壊した frontmatter（name 不一致・version 欠落）で FAIL を確認 → 戻す（scratchpad にコピーして壊す方式で本体は触らない）
- metadata 付与の回帰確認: 付与前後で frontmatter の他フィールドが変わっていないことを git diff で目視 + validate で機械確認
- starter-kit.md の手順検証: 実際の配置先プロジェクトが必要なため初回配置時に繰り越し（手順の机上レビューのみ）

## Open questions

すべて 20260703 の承認時に推奨案で確定:

- [x] **source-commit はマスターに置かない**。マスターは `version` のみ、配置時に配置先で追記（自己参照の陳腐化を回避）
- [x] **最小セット**: `design-doc + steering + frontend-code-review + impl-review + test-review + knowledge-capture`。拡張は「レビュー厚み増強 → ワークフロー拡張 → メタ層」の 3 段階
- [x] **version**: 全スキル一律 `"1.0"` 開始。判断軸の変更で minor・互換を壊す再構成で major の緩い運用（真の追跡は source-commit）
- [x] **validate は python3 前提のマスター専用ツール**（配置先には持っていかない）

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| skills-ref CLI をインストールして使う | 外部依存が増え、CLI の仕様変更に追従が必要。チェック 5 項目は標準ライブラリで 100 行未満 — 自前の方が安い |
| マスターの frontmatter に source-commit を持つ | 自己参照で commit のたびに陳腐化。追跡情報は配置先にだけ意味がある |
| 配置スクリプト（コピー+記録の自動化）まで作る | ADR 20260612 の「人が選ぶ」を守りつつ自動化するのは「拡大」段階の課題。現在の配置先数（≤3）では手順書で十分 |
| GitHub Actions で validate を CI 化 | push 運用がまだ定着していない。ローカルスクリプト先行で価値を出し、CI は運用が変わったら追加 |
| starter-kit を複数ファイル（テンプレ別体）で構成 | 参照が分散する。1 ファイルなら「これを読めば配置できる」が成立する |
