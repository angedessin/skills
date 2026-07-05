# Decision: ホットループ linter に Biome を採用し、hook は linter 非依存に書く

Date: 20260705
Status: Accepted

## Context

lint 検証ループ（post-edit-lint.sh）は AI の編集のたびに走るため、実行速度が体験の本質になる。
業界標準は ESLint（npm 週間 DL 1.37 億 vs Biome 983 万 vs oxlint 約 670 万、2026-06 実測）だが、
ESLint はプラグイン解決と JS 実行のため編集ごとの起動に構造的に遅い。
また参照した nextjs-starter の構成では jsx-a11y / react-hooks が eslint-config-next 経由のため、
Next.js を剥がすと再組み立てコストも発生する。

## Decision

PostToolUse の lint は Biome を第一候補とし、hook スクリプトは設定ファイルの自動検出
（biome.json → Biome / eslint.config.* → ESLint / stylelint 設定 → Stylelint）で linter 非依存に書く。

## Rationale

「多数派に乗る」なら ESLint だが、hook を自動検出設計にしたことで linter の選択が
可逆（＝軽い決定）になった。将来 oxlint 等へ移る場合も設定ファイルの差し替えと
hook への 1 分岐追加で済む。用途適合（速度）を優先できるのは決定が軽いから、という順序。

## Consequences

- Good: 編集ごとの lint が数十 ms で完結し、AI の自己修正ループが閉じる
- Good: 配布先が ESLint プロジェクトでも同じ hook がそのまま動く
- Bad: 型情報ルール（prefer-nullish-coalescing / prefer-optional-chain）は Biome に代替がなく捨てた（tsc とレビューで補完）
- Bad: SCSS は Biome 対象外のため Stylelint 併用が続く

## Alternatives considered

| Alternative | Reason rejected |
|-------------|-----------------|
| ESLint 続投（starter 構成の移植） | ホットループに構造的に遅い。Next 剥がし後のプラグイン再組み立てコスト |
| oxlint + oxfmt | lint は最速だが formatter の実用化が最近で成熟度が Biome に劣る（2026 年時点。国内事例は増加中で将来の乗り換え候補） |
| CI のみで lint | エラーが PR に出る時点で修正者がコンテキストを失い、ループの外に漏れる |
