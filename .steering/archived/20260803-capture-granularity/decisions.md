# 決定事項: capture-granularity

## 20260803 — 分離の形はフラグ1＋三択UX＋完了ゲート

**決定**: `.capture-needed` は 1 種のまま。セッション確認を「今 / 後で / スキップ」にし、完了時の硬い義務は別ゲートにする（案 B）。
**理由**: 1ビット潰しをフラグ増殖なしで解消できる。レポートの向き先例に近い。
**却下**: フラグ 2 種（面が増える） / `capture_done` 生涯廃止のみ（完了とセッションが分離されない）。

## 20260803 — 完了ゲートは steering archive 直前のみ

**決定**: 硬い発火点は `steering` archive 直前のみ。tasklist 全チェック時や新「タスク完了」コマンドは使わない。
**理由**: 完了ライフサイクルが既存 archive と一致する。途中セッションは柔らかい三択のまま。
**確定（承認時）**:
- スキップ → `.capture-needed` のみ削除、`capture_done` なし。**効果＝次 Stop まで**
- SessionStart 操作定義 → **`session-start-check.sh` 注入文**（CLAUDE.md 再掲は任意）
- 途中 knowledge-capture → 現行どおり `capture_done` を立てる
- archive 充足 → `capture_done` または「知見なしでアーカイブ」のみ（`[x]`・汎用省略は非充足）

## 20260803 — SessionStart 操作定義は hook 注入文（APPROVED 追認）

**決定**: 「正本＝CLAUDE.md」をやめ、SessionStart の操作定義は `session-start-check.sh` の注入文とする。CLAUDE.md は任意再掲。
**理由**: PR #9 レビュー。CLAUDE.md は配置先ごとに変わり、必須依存にすると死んだ参照になる。hook は配布され注入文に操作が既にある。
**影響**: knowledge-capture / CLAUDE.md / spec / starter-kit / README / design 主要コンポーネントを同一コミットで同期。Status は APPROVED 維持。

## 20260803 — 承認（推奨で未解決を確定）

**決定**: Status APPROVED。未解決 5 件は推奨どおり確定（省略句「知見なしでアーカイブ」 / 充足 A / タスク単位 / validate 入れる / 三択先・codify 残す）。
**理由**: ユーザー明示「推奨のもので実装を進めて」。
**影響**: 実装の正本は完了条件・主要コンポーネント。`[x]` 単独では archive 不可。
