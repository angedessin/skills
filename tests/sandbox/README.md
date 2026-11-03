# tests/sandbox

`.claude/settings.json` の sandbox の設定を、課金なしで確かめる。

| 何を | どう流す | どこで |
|---|---|---|
| 設定の形（GATED_PATHS と ask の一致・allow に git が無い・sandbox の値など） | `mise exec -- pnpm run test:sandbox` | どこでも |
| sandbox の中で読めないもの・書けないもの・動くもの | `mise exec -- pnpm run test:sandbox:probe` | sandbox を有効にした Claude Code の Bash ツール |
| sandbox の外に出すコマンド | 下の手順 | 同上 |

probe は `.env.sandbox-probe` と `.tmp/sandbox-probe/` にダミーの仮ファイルを置いて使い回す。denyRead のファイルは sandbox の中で消せないので、消すなら通常のターミナルで消す。

## sandbox の外に出すコマンドの確かめ方

`excludedCommands` は Claude Code が呼び出しの文字列で判定する。スクリプトの子プロセスは sandbox の中に残るので、Bash ツールで 1 コマンドずつ直接呼ぶ。`cd`・リダイレクト・`$(...)` を混ぜると sandbox の中に戻る。

作業ツリーがきれいな状態で、次を順に流す。`<別ブランチ>` は `.claude/` の中身が違うブランチにする。

```text
git fetch origin
git push --dry-run origin HEAD
gh pr list --limit 1
git switch <別ブランチ>
git switch -
git switch -c sandbox-merge-probe
git merge --no-ff --no-edit <別ブランチ>
git merge --abort または git reset --merge
git switch -
git branch -D sandbox-merge-probe
```

`gh pr create` は実際に PR を作るので流さない。`gh pr list` で通信と TLS の検証が通ることを確かめる。

設定や Claude Code のバージョンを変えたら流し直し、結果を残す。
