# 設計: p1d-terminology-at-refs

Created: 20260730
Status: **APPROVED**
Approved: 20260730

## 目的

2026-07-30 の docs↔実装乖離レポートで後続にした **P1d**（用語混線「7軸」と、@参照配線の陳腐化した Context）を閉じ、docs・関連 SKILL.md・ADR・rule-audit・CLAUDE / template の現行事実を揃える。説明文だけの追記はせず、誤った語・誤った配線主張を正本に置き換える。

## スコープ

### 用語の境界（正本）

| 種別 | 扱い | 例 |
|---|---|---|
| **禁止** | フルモードの別名としての「7軸」「全 7 軸」「review-* 7 軸」 | starter-kit L46、impl-review の「フルモード: 7 軸を並列」 |
| **許容** | サブスキル内の観点数など、フルモード別名ではない「N軸」 | test-review 本文の「5軸: 実装エコー・…」、一般語「判断軸」 |

置換先の正本: フルモード = **7エージェント**（`review-*` 5 サブスキル + `impl-review` + `test-review`）。

### 対象

| ID | 内容 |
|---|---|
| **用語** | 上の禁止語を、洗い出しでヒットした**現行パス**から除去し正本語に置換。最低限: `docs/starter-kit.md` / `docs/user-guide.md` / `impl-from-design` / `impl-review` / `test-review` / `skill-deploy` の各 `SKILL.md`（プレモータムで確認済み） |
| **@残骸** | ADR 20260715: **Context 該当文を過去形／現行運用に置換**し、**Amendments に 20260730 を追記**（操作は1手に固定）。Decision / Consequences 核は不変。`rule-audit` L41・L56 の @配線前提を現行化（L97 参照切れ検出は残す）。`CLAUDE.md` と `templates/SKILL.template.md` の skill-design-patterns サイズ表記を実測に揃える |
| **BACKLOG** | 本タスククローズ時に `.steering/BACKLOG.md` 節 4 の P1d 行を完了印または削除（旧「7軸」表記のノイズ防止） |

### 対象外

- P2（design 契約/付録分離・SPIKE）、capture 粒度、ナレッジ鮮度機械化、配置1件実走、passthrough 拡充
- company / export（Frozen）
- ADR Decision / Consequences 本文の書き換え（段階基準・手動 rule-audit は維持）
- `docs/archive/` / `.steering/archived/` の歴史文書
- `@` 常時ロードの復活
- `rule-audit` Step 3 の `@docs/...` **参照切れ検出**（consumer。残す）
- README の「7エージェント」表記（既に正。変更不要）
- **用語ドリフトの永続機械ゲート**（今回は手動 rg のみ。再発リスクは受け入れる — 未解決で確認）
- 既存タスク `20260730-report-driven-fixes` の compound / archive（別クローズ）

## 制約

- 受け皿ブランチ: `feature/20260730-p1d-terminology-at-refs`（base = `integration/20260730-reports`）
- **PR のマージは人間の明示指示があるまでしない**
- CLAUDE.md・SKILL.md・docs/ への書き込みは承認制（本 design 承認後の実装で実施）
- 片側修正禁止 — 用語クラスタと @残骸クラスタは、下表の対象を同コミットまたは同 PR で揃える
- 説明文だけ増やす修正は禁止（誤語の削除・置換、または ADR Context 置換 + Amendment / 手順の現行化）
- company 追随・持ち出し Gate を受け入れ条件にしない

## 完了条件

- [ ] 対象パス（archive / archived 除外。洗い出しで確定した集合）に、禁止語「7軸」「全 7 軸」「review-* 7 軸」および「フルモード: 7 軸」が残っていない
- [ ] 置換後、フルモードは「7エージェント」、内訳は `review-*` 5 + `impl-review` + `test-review` と読める（starter-kit 依存表に固定フレーズあり）
- [ ] ADR 20260715: Context の「CLAUDE.md の @参照に配線」現在形が消え、過去形または現行運用（必要時に読む・`@` なし既定）になっている。Amendments に 20260730 がある。Decision 核は不変
- [ ] `rule-audit` L41・L56 が knowledge を「@参照として配線」／必須 @ 前提で現在形主張しない。L97 参照切れ検出は残る
- [ ] `CLAUDE.md` と `templates/SKILL.template.md` の skill-design-patterns サイズが同じ実測表記（実装時再計測。目安 約49KB・547行。丸めは「約 N KB・M 行」）
- [ ] `.steering/BACKLOG.md` 節 4 の P1d が完了印または削除されている（マージ直前でも可）
- [ ] 変更対象語の全文検索で表の漏れが無い（実装前の洗い出しを tasklist 先頭で実施）

## アプローチ

用語は frontend-code-review の実装語彙（「7エージェント」）を正とし、docs **および** フルモードを「7軸」と呼ぶ SKILL.md を同梱で直す（プレモータムで docs 限定だと完了条件と矛盾することが判明）。@残骸は Context 文の置換 + Amendment を1操作とし、Decision は触らない。サイズ誤記は CLAUDE と template を対で直す。永続用語ゲートは作らない。

## 主要コンポーネント

| コンポーネント | 場所 | 変更後の記述（原本なしで判定できる粒度） |
|---------------|------|------|
| starter-kit 依存表 | `docs/starter-kit.md` L46 付近 | 依存先: `review-*` 5 サブスキル + `impl-review` + `test-review`（フルモード 7 エージェント） |
| starter-kit 導入表 | `docs/starter-kit.md` L61 付近 | `frontend-code-review` + `review-*` 全 5 サブスキル（「全 7 軸」禁止） |
| user-guide | `docs/user-guide.md` L43 付近 | `review-*`（5 サブスキル）と `test-review` / `impl-review` を別列挙。「（7 軸）」削除 |
| impl-from-design | `.claude/skills/impl-from-design/SKILL.md` | 「フルモードなら 7 軸」→「フルモードなら 7 エージェント」 |
| impl-review | `.claude/skills/impl-review/SKILL.md` | 「フルモード: 7 軸を並列」→「フルモード: 7 エージェントを並列」 |
| test-review | `.claude/skills/test-review/SKILL.md` | 同上（Related のオーケストレータ記述）。本文の「5軸: …」は許容のため残す |
| skill-deploy | `.claude/skills/skill-deploy/SKILL.md` | 「review-* 7 軸フルモード」→「review-* 5 + フル 7 エージェント」など正本に整合 |
| ADR 20260715 | `docs/decisions/20260715-docs-lifecycle-tiers.md` | Context 該当文を置換 + Amendments 20260730。Decision / Consequences 核は不変 |
| rule-audit | `.claude/skills/rule-audit/SKILL.md` L41・L56 | @ 必須配線の現在形をやめ、必要時読込・参照切れ検出は任意で残す旨。L97 維持 |
| CLAUDE.md | `CLAUDE.md` L51 付近 | サイズを実測の「約 N KB・M 行」に（`@` にしない注意は維持） |
| SKILL template | `templates/SKILL.template.md` 冒頭 | CLAUDE と同じ実測表記に揃える |
| BACKLOG | `.steering/BACKLOG.md` 節 4 | P1d 完了印または行削除 |

### 実装前の対象洗い出し（tasklist 先頭で実行）

禁止語で全文検索し表の漏れを潰す: `7軸` / `7 軸` / `全 7 軸` / `review-* 7` / `フルモード.*7` / `@参照として` / `CLAUDE.md の @参照` / skill-design-patterns 文脈の `36KB`。`docs/archive/` と `.steering/archived/` は対象外。許容の「N軸」（フルモード別名でないもの）は触らない。

## データフロー

```
実装正本: frontend-code-review（7エージェント並列）
    → starter-kit / user-guide / 関連 SKILL.md の禁止語を置換

現行運用: knowledge = 必要時に読む（@ 既定なし）
    → ADR Context 置換 + Amendment
    → rule-audit L41/L56 現行化（L97 consumer 残置）
    → CLAUDE ↔ template のサイズ表記を対で更新
```

## 影響範囲

- システム / 外部連携: なし（文書・スキル手順のみ）
- データ: なし
- 他チーム / 利用者: 配置先で starter-kit / user-guide / 関連スキルを読む人の用語理解。挙動変更なし。skill-deploy は master-only
- リグレッション懸念: archive の旧語は残る（意図的）。rule-audit の参照切れ検出を誤って消すと退行。許容「N軸」を禁止検索で巻き込むと過剰修正

## テスト方針

- 機械（必須）: archive / archived 除外で禁止語ゼロ。rule-audit に「@参照として配線」現在形が無いこと。CLAUDE と template のサイズ表記が一致
- 肯定側: starter-kit 依存表に「7 エージェント」固定フレーズがあること（rg）
- Unit / Integration / E2E: 対象外
- `npm run validate`（スキル本文変更のため）

## 未解決の論点

- [x] **用語ドリフトの永続ゲート**: 今回は手動 rg のみ（CI ゲートは作らない。再発したら BACKLOG に積む）。承認時に推奨案で確定

## 調査結果

### 既存パターン調査（20260730）

- Markdown 文言置換のみのため code-explorer はスキップ（単純な用語・Context 修正）
- 洗い出しで禁止語ヒット: starter-kit / user-guide / impl-from-design / impl-review / test-review / skill-deploy / ADR Context / rule-audit L56 / CLAUDE+template の 36KB / BACKLOG P1d 行
- 触らない: frontend-code-review（既に「7エージェント」）、claude-code-config の「@参照は毎セッション展開」警告節（正しい落とし穴）、review-workflow「7 並列」、許容の「N軸」

## 検討した代替案

| 代替案 | 却下理由 |
|--------|----------|
| 「7軸」をフルモードの別名として残し注記のみ | 用語混線が再発する。実装語彙「7エージェント」に寄せる方が短い |
| ADR を触らず rule-audit / CLAUDE のみ | Context 陳腐化が残り、rule-audit が参照する ADR と手順が再び食い違う |
| Decision 本文を書き換える | 核（段階基準・手動監査）は有効。レポートも Decision の安易な書き換えを非推奨 |
| docs（starter-kit / user-guide）だけ直す | プレモータム: 関連 SKILL.md に「7軸」が残り、完了条件（禁止語ゼロ）と矛盾する |
| P2 や capture 粒度を同 PR に混ぜる | スコープ肥大。BACKLOG の別項目として残す |
| 既存 `report-driven-fixes` に P1d を追記して再開 | 完了条件・マージ済みスコープを汚す。切り出し済み方針に反する |

## プレモータム所見（design-premortem）

実施: 20260730（フレッシュ subagent + 呼び出し側で rg 裏取り）

### 反映済み（設計本文を修正）: 6 件

- docs 限定スコープ vs 完了条件の禁止語ゼロ矛盾 → 用語対象に impl-from-design / impl-review / test-review / skill-deploy を追加。完了条件を「対象パス集合」に整合
- CLAUDE のみ 36KB 更新で template が残る → `templates/SKILL.template.md` を対で対象に。表記は「約 N KB・M 行」で揃える
- ADR が Amendment のみか Context 置換かが曖昧 → 「Context 該当文の置換 + Amendments 追記」に操作固定。Decision / Consequences は不変
- 「軸」語の禁止/許容境界が無い → 用語の境界表を追加（フルモード別名の7軸のみ禁止）
- rule-audit L41 が検査外 → L41・L56 を対象に明記。L97 は残す
- BACKLOG の P1d 行が旧語のまま残る → クローズ時の BACKLOG 更新を対象・完了条件に追加

### 人間の判断に委ねる: 1 件

- 攻撃: 再ドリフト防止が手動 rg のみで、3ヶ月後に「7軸」が再流入しても検知されない
  影響: 今回と同型の後続負債
  提案: 永続ゲートは対象外のまま受け入れる（推奨）か、別スライスで validate 追加するか — **未解決の論点**に残した
  反論: 今回は説明文修正パッケージであり、ゲート新設はスコープ肥大。手動完了条件で足りる

（このスキルは設計を承認しない。design-doc の Phase 3 STOP に戻る）
