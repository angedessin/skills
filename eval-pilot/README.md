# eval-pilot

skillset-renewal の「評価の試作」用（`.steering/20261006-skillset-renewal/tasklist.md` の 0.5）。
`claude plugin eval` で現行（B）の design-doc を評価できるかを確かめる。試作が終わったら刷新の評価に引き継ぐか削除する。

## 準備

```bash
rm -rf eval-pilot/skills && mkdir -p eval-pilot/skills
cp -R .claude/skills/design-doc eval-pilot/skills/
```

## 実行（課金。通常のターミナルから）

```bash
cd eval-pilot
claude plugin eval . --scaffold --allow-tools Write Edit "Bash(pnpm test*)" "Bash(find *)" "Bash(ls *)" "Bash(mkdir *)" --no-publish --max-cost-usd 10
```

ケースの準備スクリプトは `~/Desktop/_lab/ai/skills-eval-app/` を毎回の空の作業場所へ複製する（`node_modules` を含む）。
