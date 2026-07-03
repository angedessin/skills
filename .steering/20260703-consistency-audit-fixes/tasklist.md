# Tasklist: consistency-audit-fixes

Last updated: 20260703

## Implementation

- [x] High-1: review-security Axis 3 の NEXT_PUBLIC_ を中立化（VITE_/NEXT_PUBLIC_/REACT_APP_ の例示形。version 1.1）
- [x] High-2: サブスキル 7 本のスコープを合算 diff に置換（6 本は機械置換・test-review は散文修正。各 version 1.1）
- [x] High-3: frontend-code-review ディスパッチテンプレートに重要度尺度（High/Medium/Low/Info の基準）を定義（version 1.1）
- [x] Med-4: impl-review Axis 4 の RSC 例を条件付き 1 行に縮退（version 1.1）
- [x] Med-5: tdd の E2E 導線撤去 + patterns.md §e2e に委譲注記（version 1.1）
- [x] Med-6: CLAUDE.md セッション開始 find を capture/codify 両対応に（spec.md と完全一致）
- [x] Med-7/Low-9: knowledge-capture 決定木の条件付き @ + capture_done 再実行ガード（version 1.2）
- [x] Med-8: feature-pipeline Phase 2 モード選択スキップ・Phase 5 Deploy 列挙（version 1.1）
- [x] Low-10: debug に書き先タスクの判定基準を追記（version 1.1）
- [x] Low-11: starter-kit.md に version 巻き戻し防止の注記

## Verification

- [x] 残骸ゼロ確認: NEXT_PUBLIC / use client / use server / §e2e 導線 / HEAD-only スコープの grep すべてクリア（中立表現の例示のみ残存）
- [x] 構造検証: validate 19/19 PASS

## Deploy

- [x] コミット + push（main 直コミット運用）

## Compound

- [ ] compound スキルの実行（「片側修正」アンチパターンの昇格判断）

## Knowledge

- [ ] knowledge-capture スキルの実行
- [ ] steering archive モードでアーカイブ
