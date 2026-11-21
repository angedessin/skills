# tests/sandbox

`.claude/settings.json` の sandbox の設定を、課金なしで確かめる。

| 何を | どう流す | どこで |
|---|---|---|
| 設定の形（GATED_PATHS と ask の一致・allow に git が無い・sandbox の値・雛形との差など） | `mise exec -- pnpm run test:sandbox` | どこでも |
| sandbox の中で読めないもの・書けないもの・動くもの | `mise exec -- pnpm run test:sandbox:probe` | sandbox を有効にした Claude Code の Bash ツール |
| sandbox の外に出すコマンド | 下の手順 | 同上 |

sandbox の設定を変えたら、Claude Code を再起動してから probe を流す。有効にする前から動いていたプロセスでは、`/clear` の後でも許可していない通信先に届き、probe が 20/21 になった。

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

## 外向きの gh が確認で止まるかの確かめ方

`permissions.ask` の `Bash(gh pr create*)` などが効くかは、静的検査では分からない。Claude Code を再起動してから、Bash ツールで次を 1 つずつ流す。

| コマンド | 期待 |
|---|---|
| `gh pr list --limit 1` | 確認なしで流れる |
| `gh api repos/{owner}/{repo} --jq .name` | 確認が出る（断って止める） |
| `cd . && gh api repos/{owner}/{repo} --jq .name` | 確認が出る（つないだ形でも効く） |

`gh pr create` は実際に PR を作るので流さない。同じ `ask` の書き方の `gh api` で代える。

auto mode では、`*` の前に空白の無い ask（`Bash(gh api*)`）は確認を出さなかった。空白のある `Bash(npx *)` は出た。deny は空白の無い `Bash(git clean -f*)` でも `git clean -fn` を止めた（20261121。`test:sandbox` が空白の無い ask を落とす）。
