# 福利化ログ: report-driven-improvements

## 20260927 — compound 実行

### 効果検証
- 昇格済みルールの再発: `docs/knowledge/skill-design-patterns.md`「検出ツールを書くときの4規律」の規律1（比較対象 0 件を弾く）が散文で存在したのに、契約 (n) で再発した（review-result C5）。散文ルールは効いていない → 機械化へ切り替えた（下記 1）

### 昇格したパターン
1. 検出ツールの偽グリーン（0 件 PASS・黒名簿の素通り）→ `tests/assets/run.py`（検査器の回帰テスト・CI に追加）。契約 (m)(n)(p)(r) を壊した入力 17 通り + 対照 4 で固定。検査器に旧欠陥（0 件ガード削除・黒名簿化）を戻すと 7 件 FAIL することを確認（一回限りの確認。常設はテスト 20 件側）
2. skill-issues 2 件目（スコープ外ファイルの割り当て）→ `frontend-code-review/SKILL.md` のスコープ外ファイル規定を「観点が当たるエージェントすべて（impl / correctness / security）」に変更

### 昇格しなかったもの
- 全直積での全域性検査: `tests/state` で機械化済み・状態機械は 1 つのみ
- agent 未登録時のフォールバック: 5 か所に反映済み
- ホワイトリストの原則: 1 の (p) ケースが担保する。docs/knowledge への散文追加はしない（ユーザー方針: 死んだナレッジを増やさない）

### 変更したファイル
- tests/assets/run.py（新規）
- .github/workflows/validate.yml
- README.md
- .claude/skills/frontend-code-review/SKILL.md
