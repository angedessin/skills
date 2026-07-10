# impl-tournament commands — git worktree + モデル振り分け（カートリッジ）

SKILL.md 本文の各 Step に対応する具体コマンドと指定。別 VCS・別エージェント環境に配置する場合はこのファイルを差し替える（本文の手順はツール非依存）。

## §0 前提チェック

```bash
# git リポジトリか
git rev-parse --git-dir >/dev/null 2>&1

# 作業ツリーがクリーンか（出力が空ならクリーン）
git status --porcelain
```

## §2 並列実装 — worktree を切る

アプローチごとに独立した worktree + ブランチを作る。ベースは現在の HEAD（クリーン前提）。

```bash
# 例: 3 アプローチ
git worktree add ../tourney-A -b tourney/approach-a
git worktree add ../tourney-B -b tourney/approach-b
git worktree add ../tourney-C -b tourney/approach-c

# 一覧
git worktree list
```

各 worktree でフレッシュな subagent に渡す brief は「design.md 全文 + そのアプローチの 1 段落説明」のみ。他アプローチのブランチ名やコードを渡さない（独立性の確保）。

## モデル振り分け（コスト対策）

変種の数だけ実装コストがかかる。上位モデルを N 本すべてに使うと高いので振り分ける:

- **変種の実装**（Step 2）: 安価・高速なモデルに担当させる（例: サブエージェント起動時にモデルを Haiku 相当に指定）。数で探索するフェーズなので 1 本あたりの質より本数を取る。
- **採点・統合**（Step 3 / Step 5）: 上位モデル（Opus 相当）に担当させる。トレードオフの評価と最終統合は判断の質が効く。

具体的なモデル指定方法は実行環境のサブエージェント起動 API に従う（モデル名はここに焼き込まず、実行時の指定に任せる — ドリフト防止）。振り分けの意思決定（どのモデルをどの Step に）だけをこのカートリッジで固定する。

## §5 統合と後始末

```bash
# 勝者ブランチをメインに統合（例: approach-b が勝者）
git switch main            # または元の作業ブランチ
git merge --no-ff tourney/approach-b

# 敗者 worktree の削除（Step 4 で承認済み・不可逆）
git worktree remove ../tourney-A
git worktree remove ../tourney-C
git branch -D tourney/approach-a tourney/approach-c

# 勝者 worktree も統合後は片付ける
git worktree remove ../tourney-B
```

削除の前に、敗者から得た知見を `.steering/[task]/decisions.md` に記録すること（worktree を消すとコードは失われる）。
