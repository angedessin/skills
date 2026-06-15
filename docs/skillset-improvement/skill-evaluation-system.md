# スキル評価体系 — 設計メモ

作成日: 2026-06-13
ステータス: **設計案（議論中）**
関連: [empirical-prompt-tuning](../../.claude/skills/empirical-prompt-tuning/SKILL.md) / [rule-audit メモ](./20260613-rule-audit-skill.md) / skill-creator プラグイン

---

## 動機

スキルが増えてきた（13個）。継続運用には**評価・検証・テストの仕組み**が要る。
現状は `empirical-prompt-tuning`（質的改善）のみで、以下が欠けている:
- スキルが「スキルなしより本当に良い」かの定量比較（baseline）
- 誤発動・未発動の定量測定（triggering accuracy）
- 改訂による退行（回帰）の検出
- 複数回実行のばらつき（variance / flaky）検出

→ ビルトインの `skill-creator` プラグインがこれらを既に持つ。自前で作らず活用する。

---

## 3層の評価体系

```
新規作成 / 改訂
  ↓ ① empirical-prompt-tuning（質的・軽量・自己完結）
     「なぜ詰まるか」を dispatch で深掘り（不明瞭点・裁量補完・tool_uses 相対分析）
  ↓ ② skill-creator eval/benchmark（定量・重量・マスター専用）
     baseline比較 + triggering最適化 + variance + 回帰監視
  ↓ ③ skills-ref validate / rule-audit（静的・構造）
     frontmatter・命名・行数の機械検証
```

---

## レイヤー比較

| | ① empirical-prompt-tuning | ② skill-creator | ③ validate / rule-audit |
|---|---|---|---|
| 主眼 | 質的改善（なぜ詰まる） | 定量検証（効果・発動・退行） | 構造・規約 |
| 手段 | subagent dispatch | Python スクリプト + subagent | CLI / 静的読み |
| 依存 | **dispatch のみ（自己完結）** | **Python + プラグイン** | skills-ref CLI（or 手動） |
| 配布 | 配布スキルに同梱可 | **マスター専用**（配布物に依存させない） | マスター専用 |
| コスト | 中（dispatch 数本） | 高（baseline 並列・複数回実行） | 低 |
| 主な出力 | 不明瞭点リスト・収束判定 | benchmark.json（pass率/time/token ±stddev）・best_description | 違反リスト |

---

## skill-creator の主要機能（活用対象）

| 機能 | 中身 | このリポジトリでの価値 |
|---|---|---|
| **with-skill vs baseline 比較** | スキルあり/なしを並列実行し差分測定 | 「このスキル効果ある?」を定量化。新スキルのマージ受け入れ基準 |
| **triggering 最適化**（`run_loop.py`） | should-trigger/not 20件を train/test 分割、各3回実行で発動率測定→改善→test scoreで選択 | **誤発動防止の直球**。最重要課題に直結 |
| **回帰検出**（`--previous-workspace`） | iteration 間で benchmark 比較 | 改訂による退行を検知 |
| **variance 分析**（`aggregate_benchmark.py`） | mean±stddev で flaky 検出 | 不安定スキルの発見 |
| **eval-viewer**（`generate_review.py`） | 出力＋benchmark を HTML レビュー | 人間レビューの効率化（`--static` で headless 対応） |
| **blind A/B**（comparator/analyzer） | 2版を盲検判定 | 「新版は本当に良い?」の厳密比較（任意） |

---

## 使い分け基準（いつどれを使うか）

| 状況 | 使うもの |
|---|---|
| スキル新規作成・大幅改訂の直後、挙動が曖昧な原因を探る | ① empirical |
| 「このスキルは baseline より効果があるか」を示したい | ② skill-creator（baseline比較） |
| 誤発動 / 未発動が疑われる（skill-issues.md に記録あり） | ② skill-creator（triggering最適化 run_loop.py） |
| スキル改訂後に退行していないか確認 | ② skill-creator（回帰検出） |
| frontmatter / 命名 / 行数の規約チェック | ③ skills-ref validate / rule-audit |
| 軽い静的チェックだけで十分 | ③ or empirical の構造審査モード |

**コスト注意**: ① と ② は機能が一部重複する（両方 subagent 実行）。両方フルで回すと高い。
軽い質的チェック=①、本格 QA・triggering・回帰=② と発動条件を分ける。

---

## 既存スキルとの連携

- **rule-audit → skill-creator**: rule-audit が「誤発動しやすい description」を検出 → skill-creator の triggering 最適化で改善
- **skill-issues.md → skill-creator**: 誤発動の記録が triggering eval の should-not-trigger ケースの素材になる
- **compound → 回帰監視**: compound がルール/スキルを増やすほど退行リスクが上がる。改訂時に benchmark を取る運用とセット
- **empirical → skill-creator**: empirical で質的に磨いた後、skill-creator で定量固定。順序は ① → ②

---

## 制約・運用ルール（重要）

1. **自己完結原則の維持** — skill-creator は Python/プラグイン依存。**配布スキルに依存を持ち込まない**。skill-creator は「マスターでの開発・QA 工程で使う外部ツール」と位置づける（empirical は dispatch のみで自己完結なので配布物にも使える）
2. **成果物の git 方針** — `evals/evals.json`（eval定義）は残す候補、`*-workspace/`（実行結果）は `.gitignore` 候補。要決定
3. **モデル指定** — triggering 最適化は現在のセッションを動かすモデル ID を渡す（`--model`）。実利用と発動条件を一致させるため

---

## 未決事項

1. skill-creator を「正式なQAレイヤー」として README のワークフローに組み込むか
2. eval 成果物（evals.json / workspace）の git 管理方針
3. triggering 最適化を定期実行するか（誤発動が増えやすいスキルの定期監視）
4. empirical-prompt-tuning と skill-creator の役割を SKILL.md レベルで相互参照させるか（混同防止）
