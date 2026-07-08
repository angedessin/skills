---
Status: **DRAFT**
Created: 20260709
---

# Design — agentskills.io 調査差分の取り込み

## Goal

agentskills.io（クロスベンダーの Agent Skills 仕様・best practices）を精読し、このリポジトリの現状（20 スキル・`validate_skills.py`・`skill-design-patterns.md`）と突き合わせた結果、**サイト内容の約7割は既に実践済み or 独自到達済み**だった。本タスクは、残る「真に新規で・静的・無料で取り込める差分」だけを既存の語彙・規律（片側修正禁止／同一コミット原則）に翻訳して取り込み、同時にサイトの推奨のうち**このリポジトリの実測と矛盾する罠を明示的に無効化**することを目的とする。課金 eval ループには乗らない。

## Scope

### In scope
- `docs/knowledge/skill-design-patterns.md` への差分反映（外部 best practices との整合・矛盾点の無効化を明記）
- `templates/SKILL.template.md` の骨格追記（採用が決まった構造要素のみ）
- `scripts/validate_skills.py` への仕様準拠チェック追加（静的・無料の範囲）
- archived タスクに残る古い `.capture-needed` フラグの掃除（20260703 系 4 件）

### Out of scope
- トリガー評価ループ・出力評価ループの導入（課金・ROI 不成立 — 下記 Alternatives）
- `allowed-tools` frontmatter の採用（Experimental・クロスクライアント可搬性を毀損）
- npx/uvx ランナー推奨の採用（pnpm ポリシーと衝突 — `[[personal-projects-use-pnpm]]`）
- 既存 20 スキル本文の一斉改修（テンプレ＋新規スキルからの前進採用に留める。既存への遡及は別タスク）

## Constraints

- スタック非依存のメタ改修（スキル運用基盤）。React/TS のプロダクトコードには触れない
- 変更は静的チェックで締める（empirical はデフォルト提案しない — `[[skip-empirical-verification-by-default]]`）
- スキルは他プロジェクトへ単体コピーされる前提を崩さない（クロスクライアント可搬性は明示的設計目標）
- 同じ情報を持つ全箇所を同一コミットで直す（`skill-design-patterns.md` の「片側修正の禁止」節の自己適用）

## Acceptance criteria

- [ ] **採用1（Gotchas）**: テンプレに落とし穴記載の置き場を用意 — ただし既存「フォールバックを該当ステップに直接書く」規律と重複しない形に決着（Open question 1）
- [ ] **採用2（references 読み込み条件）**: 参照ファイルを「いつ読むか」の条件を該当ステップに書く規律を `skill-design-patterns.md` に明文化＋テンプレの Step 雛形に反映
- [ ] **採用3（validator 仕様準拠チェック）**: `validate_skills.py` に仕様準拠の静的チェックを 1〜2 項目追加（具体項目は Open question 2 で確定）
- [ ] **警戒1（停止契約の防衛）**: 「rigid directives より理由説明が効く」という外部推奨を、停止・承認ゲートには適用しない旨を該当節（ハードストップの節）に一行追記
- [ ] **警戒2〜4の記録**: allowed-tools 見送り・eval ループ見送り・npx/uvx 見送りの判断理由を ADR 化（`docs/decisions/`）し、将来の再検討時に蒸し返さない
- [ ] 掃除: 20260703 系 archived の古い `.capture-needed` 4 件を削除
- [ ] 変更した語・契約をリポジトリ全体で grep し、同義箇所の腐りがないことを確認してからクローズ

## Approach

外部サイトの「文言」ではなく「差分3〜5点＋警戒事項」だけを、既存 `skill-design-patterns.md` の節構造に翻訳して追記する。新規節は作らず、可能な限り既存節（フォールバック／片側修正禁止／ハードストップ／リポジトリ構成）に相乗りさせて肥大化を防ぐ。判断の見送り（eval・allowed-tools・npx）は ADR に「なぜ乗らないか」を一度だけ書き、知識本文には持ち込まない（`[[commit-directly-to-main]]` の運用で main へ直接コミット）。

## Key components

| ファイル | 変更内容 | 種別 |
|---|---|---|
| `docs/knowledge/skill-design-patterns.md` | 採用2（references 条件）明文化・警戒1（停止契約の防衛）一行・採用1 の決着を反映 | 既存節に追記 |
| `templates/SKILL.template.md` | 採用1・採用2 の構造要素を Step 雛形に反映 | 骨格追記 |
| `scripts/validate_skills.py` | 採用3 の仕様準拠チェック追加 | ロジック追加 |
| `docs/decisions/20260709-agentskills-non-adoption.md` | eval ループ／allowed-tools／npx 見送りの理由 | 新規 ADR |
| `.steering/archived/20260703-*/` | 古い `.capture-needed` 削除 | 掃除 |

## Data flow

なし（静的なドキュメント・スクリプト・テンプレの改修）。`validate_skills.py` の変更のみ実行時挙動を持つ → 全 20 スキルに対して回帰実行し、新チェックで既存スキルが落ちないこと（または落ちる場合は正当な指摘であること）を確認する。

## Test strategy

- **Unit/Integration**: `validate_skills.py` に追加したチェックを、既存 20 スキル全体で実行して回帰確認（新規 false positive がないこと）
- **E2E**: 対象外（プロダクトの E2E ではない）
- **empirical**: デフォルトでは行わない。テンプレ改修が実際に孤立 subagent に効くかの検証は任意扱い（`[[skip-empirical-verification-by-default]]`）

## Open questions（要レビュー）

1. **採用1「Gotchas」の扱い** — サイトは SKILL.md に独立「Gotchas」節を推奨するが、このリポジトリは既に「エッジケース処理を該当ステップに直接書く（末尾注記に分離しない）」規律を持つ。独立 Gotchas 節はこの規律と逆行しかねない。案:
   - (A) 独立節は作らず、「ステップ横断で効く落とし穴」だけをテンプレの `## When NOT to use` 直後に短い箇条書き置き場として用意する（推奨）
   - (B) サイト通り独立「Gotchas」節を追加する（規律との整合を別途明記）
   - (C) 採用1 を見送る（既存規律で十分と判断）
   → **どれを採るか要判断。**

2. **採用3「validator 仕様準拠チェック」の具体項目** — 静的に安全に検査できる候補:
   - (a) `allowed-tools` が書かれていたら **warn**（Experimental・可搬性リスクの注意喚起。error にはしない）
   - (b) frontmatter に未知キーがあれば warn（typo 検出）
   - (c) description が三人称記述で始まっているか等の緩いスタイルチェック
   → **(a) は本タスクの警戒3 と一貫して有用。(b)(c) はやり過ぎか？ どこまで入れるか要判断。**

3. **既存 20 スキルへの遡及** — 本タスクはテンプレ＋新規前進採用に留める方針だが、採用2（references 条件明記）を既存スキルにも今回まとめて反映するか、別タスクに切るか。**Out of scope に置いたが、確認したい。**

## Alternatives considered

- **トリガー評価ループ（20クエリ×3ラン×反復＝60回以上の課金実行）** — 却下。ミストリガーは既に `skill-issues.md` に無料で蓄積され compound が回収する仕組みがある。個人利用で統計的トリガー率を測る便益は薄く、`[[prefers-no-billed-optimization-loops]]`・`[[skip-empirical-verification-by-default]]` と衝突。将来やるなら「誤発動報告が最多の 1 スキルだけ」に限定するのが上限。
- **出力評価ループ（with/without 二重実行）** — 同上の理由で却下。
- **`allowed-tools` frontmatter** — 却下。仕様自身が Experimental でクライアント間サポートが割れる。クロスクライアント可搬性はこのリポジトリの設計目標であり、乗ると可搬性を自ら削る。
- **npx/uvx 一回性ランナー推奨** — 却下。「fetch しない・pnpm exec を使う」ポリシーと衝突（`[[personal-projects-use-pnpm]]`）。スクリプト設計の原則（エラーメッセージ・構造化出力）だけ取り、ランナー推奨は無視。
