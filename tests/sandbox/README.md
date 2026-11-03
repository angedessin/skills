# tests/sandbox

`.claude/settings.json` の sandbox の設定を、課金なしで確かめる。

| 何を | どう流す | どこで |
|---|---|---|
| 設定の形（GATED_PATHS と ask の一致・allow に git が無い・sandbox の値・雛形との差など） | `mise exec -- pnpm run test:sandbox` | どこでも |
| sandbox の中で読めないもの・書けないもの・動くもの | `mise exec -- pnpm run test:sandbox:probe` | sandbox を有効にした Claude Code の Bash ツール |
| sandbox の外に出すコマンド | 下の手順 | 同上 |

sandbox の設定を変えたら、セッションを再起動してから probe を流す。途中で有効にしたセッションでは、許可していない通信先に届いたことがある。

probe は `.env.sandbox-probe` と `.tmp/sandbox-probe/` にダミーの仮ファイルを置いて使い回す。denyRead のファイルは sandbox の中で消せないので、消すなら通常のターミナルで消す。

## sandbox の外に出すコマンドの確かめ方

`excludedCommands` は Claude Code が呼び出しの文字列で判定する。スクリプトの子プロセスは sandbox の中に残るので、Bash ツールで 1 コマンドずつ直接呼ぶ。`cd`・リダイレクト・`$(...)` を混ぜると sandbox の中に戻る。

作業ツリーがきれいな状態で、次を順に流す。`<元のブランチ>` は今のブランチの名前にする。

```text
git fetch origin
git push --dry-run origin HEAD
gh pr list --limit 1
git switch -c sandbox-probe-a
git rm -q .claude/agents/review-bug.md
git commit -q -m "probe"
git switch <元のブランチ>
git switch -c sandbox-probe-b
git commit -q --allow-empty -m "probe"
git merge --no-ff --no-edit sandbox-probe-a
git switch <元のブランチ>
git branch -D sandbox-probe-a sandbox-probe-b
```

- **sandbox の設定が無いブランチへ切り替えない。** settings.json が読み直されて、そのセッションの sandbox が無効になり、確認の意味がなくなる
- `gh pr create` は実際に PR を作るので流さない。`gh pr list` で通信と TLS の検証が通ることを確かめる
- `git branch -D` はブランチを消せるが、sandbox の中では `.git/config` を書けない。そのブランチの設定（VS Code が足す `vscode-merge-base` など）が残ったら、通常のターミナルで `git config --remove-section branch.<名前>` を流す

設定や Claude Code のバージョンを変えたら流し直し、結果を残す。
