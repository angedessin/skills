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

---

※ このファイルは開発が進むにつれ knowledge-capture / compound スキルによって更新される。
