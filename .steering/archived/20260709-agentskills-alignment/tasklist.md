# Tasklist — agentskills-alignment

design.md 承認後に着手。Open questions 1〜3 の決着を先に得ること。

## 採用（静的・無料）
- [ ] 採用1: Gotchas の扱いを Open question 1 の決着どおりに `templates/SKILL.template.md` へ反映
- [ ] 採用2: references の「いつ読むか」条件明記の規律を `skill-design-patterns.md` に追記＋テンプレ Step 雛形に反映
- [ ] 採用3: `validate_skills.py` に仕様準拠チェック追加（Open question 2 の確定項目）
- [ ] 採用3 の回帰: 全 20 スキルで validator 実行し false positive なしを確認

## 警戒事項の記録
- [ ] 警戒1: 「理由説明 > rigid directives」を停止・承認ゲートに適用しない旨をハードストップ節に一行追記
- [ ] 警戒2〜4: eval ループ／allowed-tools／npx 見送りの ADR を `docs/decisions/20260709-agentskills-non-adoption.md` に作成

## 掃除
- [ ] 20260703 系 archived の古い `.capture-needed` 4 件を削除

## クローズ前チェック
- [ ] 変更した語・契約をリポジトリ全体で grep（片側修正禁止の自己適用）
- [ ] 同じ情報を持つ全箇所を同一コミットで直したか確認
- [ ] tasklist.md 更新（CLAUDE.md 規約）
- [ ] knowledge-capture / compound の要否を判断

---
Archived: 20260709（保留判断。導入は検討中で見送り。結論は decisions.md 参照。再開時は `.steering/` 直下に戻す）
