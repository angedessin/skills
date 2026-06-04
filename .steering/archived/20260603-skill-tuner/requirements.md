# Requirements: skill-tuner → empirical-prompt-tuning

Created: 20260603
Updated: 20260603（方針転換により更新）

## Goal

経験的プロンプトチューニング手法をもとに、任意のプロンプト（skill / slash command / task プロンプト / CLAUDE.md 節）の品質を検証・改善するメタスキルを導入する。当初は本リポジトリ専用の `skill-tuner` を自作する方針だったが、設計・議論の中で汎用的な `empirical-prompt-tuning` スキルの採用に方針転換した。

## Scope

### In scope
- 任意のプロンプトファイルを入力として受け取る
- 典型シナリオ + エッジケースを定義し、フレッシュな AI エージェントで実行・評価する
- 評価結果（不明点・裁量判断・メトリクス）をもとにプロンプトを改善する
- 改善が頭打ちになるまで反復する（最大4サイクル、収束条件あり）
- `compound` スキルを対象に empirical-prompt-tuning を実行し動作確認する

### Out of scope
- スキルの新規作成（→ `skill-creator` が担当）
- 結果ファイル（skill-tuner-result.md）の保存（→ git diff で代替）
- 複数スキルの一括チューニング

### 方針転換の経緯
- 当初: このリポジトリ専用の `skill-tuner` を自作
- 変更: 汎用的な `empirical-prompt-tuning` スキルを採用（セキュリティチェック・欠落ステップ補完済み）
- 理由: skill-tuner は評価手法の本質（汎用性・7軸評価・収束判定）が不十分だった

## Constraints

- 評価エージェントは毎回フレッシュな Agent tool 呼び出しを使う（学習バイアス防止）
- サードパーティ製スキルのため、採用前にセキュリティチェック（Bash コマンド・外部 URL・プロンプトインジェクション）を実施した

## Acceptance criteria

- [x] empirical-prompt-tuning スキルを導入しスキルリストに登録される
- [x] `compound` スキルを対象に4サイクル実行して動作確認できた
- [x] compound SKILL.md が評価結果をもとに改善された
- [x] skill-tuner（旧版）を削除した
