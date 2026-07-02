# Decisions: rule-audit

## 20260703 — CLAUDE.md の @参照は毎セッション自動読み込みされる

**Decision**: 参照切れの `@docs/knowledge/testing-patterns.md` は差し替えではなく削除。claude-code-config.md への導線は @ なしのプレーンパス表記で追加
**Reason**: `@参照` は「必要なトピック作業時のみ」ではなく毎セッション中身が展開される（skill-design-patterns.md で実測）。大きいファイルを @ で繋ぐと固定費になる。「必要時に読む」を意図するなら @ を付けない
**Impact**: CLAUDE.md ドキュメント参照節の運用が明確化。テスト知識は実体が docs/knowledge/ に溜まったときに @参照ごと復活させる

## 20260703 — 受け入れ試行の結果

**Decision**: rule-audit の初回実行（本リポジトリ CLAUDE.md・スキル 17 個）で検出した 6 所見のうち 5 件を適用（参照切れ削除 / find の archived 除外 / glossary 削除 / empirical 引用符統一 / config 導線追加）。「保持 16 件」の判定は全て理由付きで提示できた
**Reason**: 実在する問題（参照切れ・今セッションで実害の出た find の穴）を検出でき、受け入れ基準を満たす
**Impact**: スキルは設計どおり機能する。定期実行（/loop・/schedule）の組み込みはユーザーが必要時に判断
