# 決定事項: passthrough-pipeline-gate1

## 20260806 — スコープ（Gate 1 のみ）

**決定**: `feature-pipeline` の Gate 1（DRAFT で実装に入らない）シナリオのみ作成する。`frontend-code-review` は対象外。Gate 3.5 / ハーネス拡張は BACKLOG 節 2d に残す。
**理由**: 現行ハーネスで SHA1 差分判定できる停止に限定する。FCR は 20260725 で承認ゲートではない・非 git で意図分岐に届きにくいとして落としている。Gate 3.5 はファイル差分に出ない。
**影響**: レポート後続の「passthrough 拡充」は Gate 1 完了後も FCR・Gate 3.5 が残る可能性あり。BACKLOG 更新時に明記する。

## 20260806 — 完了条件の深さ（dry-run 必須）

**決定**: 必須完了はシナリオ作成 + `--dry-run` 構造健全まで。課金実走（`--runs 4`）は任意で、`skill-test` のコスト承認後にのみ行う。
**理由**: 素通り検査の課金を完了必須に載せない。前提チェック型は過去 `impl-from-design` で 4/4 であり、初回から本文改修前提にしない。
**影響**: PR マージ判断に実走 PASS を必須としない。実走したい場合は別ゲート。

## 20260806 — プレモータム反映（judge_glob / 命名 / BACKLOG 語義）

**決定**: (1) `judge_glob` に `.steering/**/design.md` を含め Status 改変も素通りとする (2) ディレクトリは `feature-pipeline-gate1` (3) BACKLOG は「骨格・未実走」と書き一段落過信を防ぐ (4) request は既存 DRAFT 続行に一本化 (5) dry-run 非空は目視必須（ハーネス改修はしない）
**理由**: プレモータム所見。pipeline は Status が状態機械入力のため src のみ監視は偽陽性 PASS になる。dry-run 完了と行動検証済みを混同しない。
**影響**: シナリオは impl-from-design 同型より判定対象が広い。`--all` 利用者向けに任意実走の推奨コマンドを完了条件に記載。
**正本**: `design.md` 付録「プレモータム所見」の各 **推奨対応（採用）**（却下した代替も同節）。

## 20260806 — 実装完了（dry-run 必須分）

**決定**: シナリオ・BACKLOG 更新・dry-run（N=2）まで完了。課金実走は未実施のまま任意項に残す。
**理由**: 設計の完了条件（必須）と Phase 1.5 A に一致。
**影響**: 次は frontend-code-review → PR（base=integration）。
