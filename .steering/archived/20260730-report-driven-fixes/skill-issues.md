# スキル課題: report-driven-fixes

## 20260730 — 知見保存が「マージ後」固定だと PR に無関係差分が混ざる

**事象**: tasklist テンプレと feature-pipeline が「デプロイ（PR・マージ）→ knowledge-capture」順のため、
エージェントが knowledge / archive を「本 PR 対象外・後続」に先送りした。後続 PR に無関係な
docs / `.steering` 差分が混ざる構造。

**期待**: PR 差分に属する知見はマージ前に同じブランチへ含める。マージ後の capture は横断・会話残り・
compound・アーカイブ用、と役割を分ける。

**対応**: 本 PR で (1) 知見を同梱 (2) templates / feature-pipeline / skill-design-patterns に上記を明記。
