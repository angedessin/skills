# impl-tournament commands — git worktree（カートリッジ）

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

## モデル・エフォートの指定

変種の数だけ実装コストがかかるため、役割ごとにモデルを分ける。**値はこのファイルに書かない** — `.claude/agents/` の定義が正本:

- 変種の実装（Step 2）: `tournament-variant`
- 採点（Step 3）: `tournament-scorer`

散文でモデルの指定を書いても、subagent の起動に効く機構が無く何も指定されない。定義ファイルに `model` / `effort` を持たせることで初めて効く。
定義が無い環境ではセッション設定のまま実行する（コスト見積にその旨を書く）。

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
