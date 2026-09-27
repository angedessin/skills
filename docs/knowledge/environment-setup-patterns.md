# Environment Setup Patterns — 新規プロジェクト環境構築での実践知識

## 設定ファイルの $schema はツール導入前に推測で書かない

インストール前に `biome.json` の `$schema` をバージョン推測（例: `2.1.2`）で記述すると、
実インストールされたバージョン（例: `2.5.3`）と食い違い、警告や非推奨フィールド
（`recommended` 等）の警告が出て `biome migrate` 等の手戻りが発生する（20260713 webgl-boilerplate 実例）。

- ツール導入後に `[tool] init` / `[tool] migrate` 等の生成コマンドで設定ファイルを作る
- バージョン固定の `$schema` を先に書かない。導入後に実バージョンへ揃える

## mise 管理プロジェクトでは Bash ツールから bare pnpm/node を呼ばない

非対話 Bash では mise が有効化されないため、PATH 上に残った壊れた standalone
インストール（例: `~/Library/pnpm/pnpm`）を拾って `pnpm exec` 等が exit 127 になることがある
（20260713 webgl-boilerplate 実例）。

- mise 管理プロジェクトでは `mise exec --` 経由か `node_modules/.bin/` 直叩きを既定にする
- bare `pnpm`/`node` 呼び出しは非対話シェルでの mise 未有効化を前提に避ける

## Rosetta 下の Bash で `pnpm install` すると biome の x64 バイナリが外れる

このマシンの非対話 Bash は Rosetta 下（`arch` = i386）で mise の Node は x64 だが、pnpm は arm64 版だけを入れるため
`@biomejs/cli-darwin-x64` が外れて `lint` が MODULE_NOT_FOUND で落ちる（20260921）。

- `node_modules` を再インストールしない。CI 再現は各コマンドを個別に回すだけで足りる
- 外してしまったら、一時的に `pnpm-workspace.yaml` へ `supportedArchitectures: {os: [darwin], cpu: [x64, arm64]}` を置いて
  `pnpm install --frozen-lockfile` → 削除する

