# Decisions: review-axes-coverage

## 20260702 — 実装モードは Impl-first 相当（TDD 不適用）

**Decision**: impl-from-design のモード選択で TDD モードを採らず、design.md の Test strategy（構造検証 + empirical-prompt-tuning + 統合検証）に従う Impl-first 相当で進める
**Reason**: 成果物が SKILL.md（Markdown）で Vitest のテスト対象が存在しない。スキルの「テスト」に相当するのは fresh subagent 実行（empirical）と実 diff での統合実行
**Impact**: tasklist.md の Verification セクションが TDD フェーズの代替になる

## 20260702 — impl-review と review-correctness の責務境界

**Decision**: 型注釈の品質（any・アサーション・@ts-ignore）は impl-review の TypeScript 軸に残し、ランタイムでロジックが壊れるか（null 参照・境界値・レース）を review-correctness が担う。同一行で同趣旨の指摘はオーケストレーターの重複統合で review-correctness に帰属させる
**Reason**: 「型が雑」と「動作が壊れる」は別の関心。既存の impl-review 5 軸を変更せずに済み、統合ルールだけで整合が取れる
**Impact**: frontend-code-review Phase 3 の重複統合ルールに 2 行追加

## 20260702 — エラーハンドリングの分担

**Decision**: エラーの「握りつぶし」（catch {} 等）は review-correctness Axis 4、エラーの「ユーザー向け表示の有無」は review-ui Axis 3 が担う。単独のエラーハンドリングスキルは作らない
**Reason**: design.md Approach の確定事項（workflow-plan 4-2 の判断を踏襲）。同一エラー箇所でも趣旨が異なるため重複統合しない
**Impact**: 両スキルの本文に相互の境界を明記して subagent の裁量補完を防ぐ

## 20260702 — docs/skillset-improvement の記述が古くなった（追随候補）

**Decision**: issues-and-plan.md の「★要判断（3-A: correctness の担い先）」と Part C「課題3 は保留中」は本タスクで解決済みになったが、docs/ への書き込みは承認制のため未更新のまま残した
**Reason**: 履歴ドキュメントの更新は knowledge-capture / compound のフローでまとめて承認を得る方が一貫する
**Impact**: knowledge-capture 時に issues-and-plan.md へ「解決済み（20260702 review-axes-coverage）」の注記を入れる提案をすること

## 20260702 — 挙動検証の分担

**Decision**: empirical-prompt-tuning による新スキル 2 本の検証はユーザーが実施する。統合検証（フルモード 1 回）はこのリポジトリでは実施せず、React プロジェクトへの配置後の初回利用時に行う
**Reason**: ユーザーの意向（課金作業は自分で制御したい）。またこのリポジトリは Markdown のみで .ts/.tsx の diff が作れず、レビューサブスキルのスコープが全て空振りするため統合検証として成立しない
**Impact**: tasklist.md の Verification 3 項目は未チェックのまま分担を明記。empirical で指摘が出た場合はマスターの SKILL.md に還元する
