# Decisions: lint-verification-loop

## 20260705 — lint hook はフェイルオープン、guard 系はフェイルクローズ

**Decision**: post-edit-lint.sh / stop-typecheck.sh は jq・ツール・設定が無ければ無音で exit 0 にする（guard-env-read.sh のフェイルクローズとは逆）。
**Reason**: lint は品質ゲートでありセキュリティゲートではない。配布先の未整備プロジェクトで編集が止まる方が害が大きい。
**Impact**: hook を配布物として任意のプロジェクトにコピーしても安全（no-op で共存）。

## 20260705 — ツール検出は node_modules/.bin の存在チェック

**Decision**: `pnpm exec` ではなく `$PROJECT_ROOT/node_modules/.bin/<tool>` の実行可能チェックで検出・起動する。
**Reason**: PostToolUse は編集のたびに走るため、pnpm の起動オーバーヘッド（数百 ms）を毎回払わない。
**Impact**: pnpm workspace のルート以外に依存を置くモノレポでは検出されない。必要になったら pnpm exec フォールバックを追加（まず作ってカスタマイズ方針）。

## 20260705 — 部分修正 + 違反残りの場合は再読の注意も stderr に含める

**Decision**: exit 2 で差し戻すケースでも、自動修正でファイルが書き換わっていれば「Re-read it before further edits」を先頭に付ける。
**Reason**: AI が違反修正の Edit を古い old_string で当てて失敗する二次被害を防ぐ。
**Impact**: reformatted 通知（additionalContext）は違反ゼロ時のみ、違反ありの時は stderr に統合。
