# ブロッカー・環境の問題

## 20260725 — pnpm のバイナリが壊れていて npm script を実行できない

**事象**: `pnpm validate` / `pnpm --version` のいずれも次のエラーで失敗する。

```
/Users/kentaro/Library/pnpm/.tools/@pnpm+exe/11.12.0/node_modules/@pnpm/exe/pnpm: line 1: This: command not found
```

シェルスクリプトとして実行されているが中身がバイナリ／別形式らしく、1 行目が解釈できていない。`pnpm --version` 単体でも再現するため、**このタスクの変更とは無関係な既存の環境問題**。

**影響**: Phase 3 で追加した `validate` / `validate:portability` / `check:export` の npm script を `pnpm` 経由で実行できない。ただし:
- `package.json` は妥当（JSON パース確認済み・4 スクリプト登録）
- 各スクリプトの実体（`python3 scripts/...`）は直接実行で全て正常動作を確認済み

**回避策**: 当面は `python3 scripts/validate_skills.py` のように直接実行する。

**対応**: このタスクのスコープ外（pnpm の再インストールが要る）。npm script の追加自体は完了しており、pnpm が直れば動く。
