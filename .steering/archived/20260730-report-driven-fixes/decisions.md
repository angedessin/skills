# 決定事項: report-driven-fixes

## 20260730 — スコープと company 境界（Phase 1.5）

**決定**: 今回は P0 + P1a/b/c + E1。P1d / P2 / capture 粒度・鮮度機械化・配置実走・passthrough は対象外。
**理由**: 宣言と実装の矛盾と生きた company 負債を先に閉じる。中〜大のワークフロー変更は混ぜない（案 G）。
**影響**: 実装単位は docs/スキル/検査の整合が主戦場。

## 20260730 — company は E1（機械削除＋文書凍結）

**決定**: `check_export_stopcontract.py`・契約 (g)(i)・関連 npm/README/skill-test 義務を除去。deployments / knowledge は Frozen・過去形化。worktree 実体・ADR・一般法則は残す。
**理由**: 残った生きた検査は認知税と片側修正の温床（技術的負債）。E2（worktree 削除）は別判断。
**却下**: 文書凍結のみ（E3）— 負債が残る。
