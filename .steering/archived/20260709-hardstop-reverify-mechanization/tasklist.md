# Tasklist: hardstop-reverify-mechanization

Last updated: 20260709

## Part 1 — ハードストップ再検証 ✅ 完了（6/6 PASS・素通り 0）

- [x] 検証シナリオ 6 本（design-doc / impl-from-design / debug 各 2）を verification.md に定義
- [x] サンドボックス準備（scratchpad・このリポジトリを汚さない）
- [x] design-doc: フレッシュ実行 2 回（A1 Phase 3 STOP + A2 会話内分岐 STOP）→ 両 PASS
- [x] impl-from-design: フレッシュ実行 2 回（B1 不在+会話内承認主張 / B2 DRAFT で停止）→ 両 PASS
- [x] debug: フレッシュ実行 2 回（C1/C2 Report 提示後に承認なしで修正せず）→ 両 PASS
- [x] 判定を verification.md に記録（素通りなし → skill-issues.md 記録不要）
- [x] （素通り時のみ）文言修正 — 素通り 0 のため不要

## Part 2 — 機械化 ✅ 完了

- [x] check_deploy_drift.py 実装（3 分類: 直接編集 / マスター先行 / 記録なし）
- [x] drift fixture で 3 分類 + exit code を確認（debug=a / tdd=b / e2e=c / review-security=OK / exit=1）
- [x] validate_skills.py に --template モード追加
- [x] 現行テンプレで PASS / 壊したコピー4種で FAIL を確認（frontmatter欠落・アストラル面・version欠落・500行超）
- [x] validate-skill-edit.sh をテンプレ編集で発火するよう拡張（正常=exit0 / 違反=exit2+stderr を確認）
- [x] 全スキル PASS のリグレッション確認（20/20 PASS）

## Review

- [x] /code-review（8 アングル自己精査・スクリプトは非フロントエンドのため frontend-code-review は不使用）→ confirmed バグ 0
- [x] レビュー指摘の修正 — 指摘なしのため不要

## Deploy

- [x] main へ直接コミット（このリポジトリの慣行。PR は明示要求時のみ）

## Compound

- [-] compound スキルの実行 — 見送り（ユーザー選択。機械化は既存「説明文→hook/script」パターンの
      横展開で新ルール昇格の必要が薄い。将来 compound を回す場合はドリフト検出/テンプレ検証の運用知見を候補に）

## Knowledge

- [x] knowledge-capture 実行（skill-design-patterns.md「ハードストップ」節に再検証結果＋素通り検査手法を追記）
- [x] steering archive モードでアーカイブ

Archived: 20260709
