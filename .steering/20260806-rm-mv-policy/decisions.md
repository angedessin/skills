# decisions: rm-mv-policy

## 20260806 — 設計承認（プレモータム未解決の確定）

**決定**: Status を APPROVED。プレモータムの人間判断 4 件を次で閉じた。

| 論点 | 決定 | 却下 |
|---|---|---|
| 別名・複合 | `git rm` / `/bin/rm` / `bash -c` 等は対象外。素の `rm`/`mv` のみ | 別名まで追うパーサ軍拡 |
| permissions flag | **C: 現行維持＋文書のみ。permissions / DEPLOY_PERMISSIONS は触らない** | A 最小追加（終わり条件なし）/ B 別バックログ起票 |
| export ドリフト | 既知・今回非対応の一文を残す。追従タスクは今切らない | Frozen 下で追随を受け入れ条件に混ぜる |
| hook 名 | `guard-gated-delete.sh` | `rm-mv` 等の別名 |

**理由**: hook 本命・完全封鎖しない脅威モデル・company Frozen を一貫させるため。

## 20260806 — 人間確認: PreToolUse deny 発火

**決定**: 完了条件の人間確認を PASS とする。
**観測**: セッション再起動後、Bash で `rm -f docs/knowledge/x.md` をそのまま実行 → `guard-gated-delete` がブロック（人間側で確認）。
