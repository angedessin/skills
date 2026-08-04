# verification: knowledge-freshness-nudge hook fixtures

Date: 20260804
Command: temporary CLAUDE_PROJECT_DIR fixtures against `.claude/hooks/session-start-check.sh`

| # | Case | Result |
|---|------|--------|
| 1 | マーカー無し → 注入 | PASS |
| 2 | 新しい → 非注入 | PASS |
| 3 | age>=2592000 → 注入 | PASS |
| 4 | age==2591999 → 非注入 | PASS |
| 5 | `.steering/` 無し → 素通し | PASS |
| 6 | rule-audit スキル無し → 非注入 | PASS |
| 7 | 壊れたマーカー（非整数）→ 注入 | PASS |
| 7b | 先頭ゼロ `0999999999` → 注入（八進 fatal 回避） | PASS |
| 8 | capture/codify あり → 注入順後段 | PASS |
| 9 | `PATH` 先頭の失敗 `date` → 他注入継続・ナッジなし | PASS |

再現手段 (9): `PATH` に `exit 1` だけの `date` を置き、本物より先に解決させる。
修正後 (7b): `0[0-9]*` 拒否 + `10#` 十進強制（review Medium 対応）。
