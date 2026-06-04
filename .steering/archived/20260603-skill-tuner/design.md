# Design: skill-tuner → empirical-prompt-tuning

Status: **APPROVED**
Approved: 20260603
Updated: 20260603（方針転換により更新）

## Approach

当初は `skill-tuner`（このリポジトリ専用）を自作する設計だったが、議論の中で汎用的な `empirical-prompt-tuning` スキルを採用する方針に転換した。セキュリティチェック（Bash コマンド・外部 URL・プロンプトインジェクション確認）と欠落ステップ（1〜4）の補完を行った上で導入。`compound` スキルを対象に4サイクル実行し、評価→修正→再評価のループが正常に機能することを確認した。

## Key components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| empirical-prompt-tuning | `.claude/skills/empirical-prompt-tuning/SKILL.md` | 任意プロンプトの評価・改善スキル本体 |
| compound（改善済み） | `.claude/skills/compound/SKILL.md` | 動作確認対象、4サイクルで改善 |
| design-doc（改善済み） | `.claude/skills/design-doc/SKILL.md` | 方針転換時の design.md 更新ルールを追加 |

## 方針転換の詳細

### 変更前（skill-tuner）
- 対象: `.claude/skills/[name]/SKILL.md` 専用
- 評価軸: 要件充足率のみ（0〜100点）
- 収束条件: スコア80点以上 or 4サイクル
- 結果保存: `skill-tuner-result.md`

### 変更後（empirical-prompt-tuning）
- 対象: 任意のプロンプトファイル
- 評価軸: 7軸（成功/精度/ステップ数/duration/再試行/不明瞭点/裁量補完）
- 収束条件: 連続2回で不明瞭点ゼロ + メトリクス飽和 + hold-out 過適合チェック
- 結果保存: なし（git diff で代替）

### セキュリティチェック結果
- ゼロ幅・制御文字: 異常なし
- Bash コマンドブロック: 破壊的コマンドなし
- 外部 URL: なし
- プロンプトインジェクション: なし
- 欠落箇所: ステップ 1〜4 が欠落していたため補完

## compound への empirical-prompt-tuning 適用結果

| Iter | 主な変更 | [critical] |
|------|---------|-----------|
| 1 | ベースライン | ✅ |
| 2 | Step 1 に CLAUDE.md 重複確認追加 / Step 5 タイミング明記 | ✅ |
| 3 | Step 3 にゼロ候補テンプレート追加 / Step 5 フラグ削除の条件明記 | ✅ |
| 4 | Step 1 に `.steering/` 不在フローを直接統合 | ✅ |

## セッション中に発見した副次的改善

- `design-doc` スキルに「方針転換時の design.md 更新ルール」を追加
  - 本タスク自体が .steering を更新しないまま方針転換した事例となった

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| skill-tuner を自作（当初案） | 評価軸・収束判定が不十分、汎用性がない |
| skill-tuner-result.md の保存 | git diff で代替可能、ファイルが増えるだけ |
| スコア80点で打ち切り（当初設計） | スコアではなく不明瞭点の有無で判断する方が本質的 |
