Last updated: 2026-11-11

# tasklist: skill-loop-fixes

統合用ブランチ: `feature/skill-loop-fixes`。各項目は、確かめるテストを同じ項目の中で書く（A4 の規則を自分にも当てる）。

## PR 1 — テストの必須化（ブランチ `feature/test-gate`）

- [ ] 1. `vitest related` で、関係するテストが 0 件のとき・あるとき・落ちたときの終了コードと出力を、一時的なプロジェクトで確かめる。結果を decisions.md に残す（判定できなければ、判定する範囲を未コミットだけに戻す）
- [ ] 2. 型検査の hook を自分の状態で判定する形に直す（A1'）。fixture を先に書いて落ちることを確かめてから直す
- [ ] 3. ゲートの fixture の仕組みと、テストの有無・免除・ベースとの差分・worktree・削除だけ・対象外のファイルのケースを書き、ゲートの骨格（判定 1〜4・免除のファイル）を通す
- [ ] 4. テストの成否・打ち切り・道具の故障・同じ差分で流さない、のケースと実装
- [ ] 5. テストを弱めた判定・タスクの外の免除の警告、のケースと実装
- [ ] 6. settings とその雛形に登録し、README（依存の一覧・hook の説明・cp の行・外す目安）を直す。`test:sandbox` を通す
- [ ] 7. steering の 3・4（A2）と design-doc の 4（A4）を直す。`eval/gen_design_cases.py` の s1・s2 の tasklist と `q1-right-item` を直し、A2・A4 の grader を足す
- [ ] 8. validate に C3 の検査と self-test を足す
- [ ] 9. `validate`・`test:hooks`・`test:sandbox`・`lint` を流す → 回帰ケースの見積もりを示し、承認後にユーザーに流してもらう → 結果を読んで確かめる
- [ ] 10. レビュー → PR（統合用ブランチへ）

## PR 2 — 知見を設計で読む（ブランチ `feature/design-reads-knowledge`）

- [ ] 11. design-doc の 2 に `docs/knowledge/` を読む 1 行を足し、知見を置いた評価のケースを足す
- [ ] 12. 静的検査 → 回帰ケースの見積もり・承認・実行 → レビュー → PR

## PR 3 — レビューまわり（ブランチ `feature/review-upkeep`）

- [ ] 13. 差分を数えるスクリプトと `tests/skills/` のテスト・`test:skills` を書き、Step 1 を短くする（C1）
- [ ] 14. `review-test` の起動条件と観点、`review-verify` の 3 種類の基準を足す（A3）。テストの無い差分・形だけのテストの評価のケースを足す
- [ ] 15. 報告に担当を添える（C2）
- [ ] 16. 静的検査 → 回帰ケースの見積もり・承認・実行（Step 1 の費用の目安を測り直す）→ レビュー → PR

## PR 4 — 変える前のコードで流す判定（ブランチ `feature/test-before-check`）

- [ ] 17. 判定の手順（ベースのコードの用意・テストの持ち込み・リファクタリングの除外）を、スクリプトとテストで作る
- [ ] 18. frontend-code-review に組み込み、評価のケースを足す
- [ ] 19. 静的検査 → 回帰ケースの見積もり・承認・実行 → レビュー → PR

## 仕上げ

- [ ] 20. main に注釈付きのタグを打つ（戻り先）
- [ ] 21. steering で閉じる（history.md に 1 行）→ 統合用ブランチを main へ PR
- [ ] 22. tasklist の更新
