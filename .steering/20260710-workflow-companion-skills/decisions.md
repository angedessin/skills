# Decisions: workflow-companion-skills（実装フェーズ）

## 20260711 — validator 項目6 は「見出しに When NOT to use を含む」で判定
**Decision**: 項目6は `## When NOT to use` の完全一致ではなく、見出し行に "When NOT to use" 文字列を含めば PASS とした（正規表現 `^#+ .*When NOT to use`）。
**Reason**: pr-create は既に `## このスキルの境界（When NOT to use）` を使っており、完全一致にすると既存準拠スキルを FAIL させる。テンプレ・pr-create・新規スキルすべてが英語句を見出しに含む慣行に揃っている。
**Impact**: review-* 7件・empirical・frontend-code-review に `## When NOT to use` を新設。既存の「スコープ」「いつ使うか」節はそのまま残し、境界節を追加。

## 20260711 — 項目7 のエスケープマーカーは接頭辞一致にした
**Decision**: `<!-- validator: no-stop-needed` の接頭辞で判定（末尾に理由テキストを許容）。当初は完全一致 `-->` 込みで実装したが、理由をコメント内に書く運用（design 指定）と両立しないため接頭辞一致に変更。
**Reason**: design が「使用時はコメント内に理由を書く運用」と明記。理由を書くと閉じタグ位置が動くため完全一致では拾えない。
**Impact**: impl-review / test-review / steering がエスケープ + 理由付きで PASS。

## 20260711 — 項目7 で落ちた既存5スキルの振り分け
**Decision**: rule-audit・feature-pipeline は**真の停止点**なので「ここで止まる」を追記（rule-audit Step6 適用前・feature-pipeline Gate3.5 マージ判断）。impl-review・test-review・steering は停止点を持たない（レビュー報告のみ / APPROVED は status 値の引用）ためエスケープマーカー。
**Reason**: design の「落ちたという事実は説明文だけの停止契約の検出そのもの」に従い、本物の停止点は手順化。誤検出はエスケープで逃す。
**Impact**: 説明文だけだった rule-audit の適用ゲートが明示ハードストップになった（検出の実利）。

## 20260711 — check_deploy_drift.py は新規作成せず既存を拡張
**Decision**: design の Premortem #7 の通り、新規 harvest.py を作らず既存スクリプトにレジストリモード + issues 回収を追加。比較ロジック（source-commit 行除去・references 除外）は既存を再利用。読み取り専用・単一パスモード互換を維持。
**Reason**: 比較ロジックの二重化を防ぐ（片側修正の温床になる）。
**Impact**: 引数なし=レジストリモード / 1引数=単一配置先（既存互換）。scratchpad のダミー配置先で (a)(c) 検出・マーカー前後切り分け・レジストリループを確認。

## 20260711 — passthrough_check.py に --dry-run を追加
**Decision**: design にない `--dry-run`（サンドボックス生成 + SHA1 スナップショット + プロンプト構築まで行い、課金するエージェント起動だけスキップ）を追加。
**Reason**: ユーザー方針（課金ループを既定で回さない）と、実行層のエンドツーエンド構造を無課金で検証したい要求の両立。design 受け入れ基準「E2E が通る構造を確認できる」を課金せず満たせる。
**Impact**: `--dry-run` / `--all --dry-run` で design-doc シナリオの構造検証済み。実課金の 2run 判定は AGENT_CMD 定数を実環境に合わせた上でユーザー承認後に回す。

## 20260711 — pr-feedback のワークフロー位置は [6.5]、feature-pipeline では Phase 3.7
**Decision**: README 図では pr-create [6] → pr-feedback [6.5] → マージ [6.9]。feature-pipeline では Phase 3.5（PR作成）→ Phase 3.7（往復）→ Gate 3.5（マージ）。
**Reason**: マージ（人間判断・外向き）の手前に往復フェーズを挟むのが自然。既存の Gate 3.5 マージゲートは維持。
**Impact**: feature-pipeline の現在地判定表に Phase 3.7 行を追加（ファイルだけでは往復の有無を完全検出できないため、pr-create の返送報告 / ユーザー要求を入力に含める旨を明記）。

## 未了（別ステップ）
- skill-test の残シナリオ整備（impl-from-design/debug/pr-create/新設4）は任意・未着手。design-doc の 1 本のみ先行。
- knowledge-capture: 新パターン「配布分類（distributable/master-only）」「課金操作の前置承認」を skill-design-patterns.md へ昇格するかは knowledge-capture ステップで判断（docs/ 書き込みは承認制）。
