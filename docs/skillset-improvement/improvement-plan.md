# 改善方針 — 実装前まとめ

作成日: 2026-06-13
前提ドキュメント: [20260613-current-issues.md](./20260613-current-issues.md)
ステータス: **方針確定（実装承認待ち）**

## 確定事項（2026-06-13 確認済み）
1. SSR/RSC: **フレームワーク非依存で SSR 観点は残す**（案B）
2. `explore`: **まず実体確認してから判断**（次フェーズ）
3. 今回スコープ: **スタック整理を先行**（論点1 + 論点3 + 課題2 + 論点4-A の `compatibility` 分離）。`debug` / `explore` / E2E / `rule-audit` / metadata・validate 整備は次フェーズ

---

## 論点1: 技術スタックから Next.js を外す

### 背景・決定
- Next.js は Vercel 依存が強すぎる（Server Actions / App Router / `next/image` / `next/dynamic` / Vercel 前提の CWV 最適化）
- スタック記述は **React** ベースにする
- 新スタック表記案: `React / TypeScript / Vitest / React Testing Library / MSW / Playwright`
  - ビルドツール（Vite 等）はスタックに明記しない（プロジェクト裁量・中立に保つ）

### 影響箇所（実測 14 ファイル）

| 種別 | ファイル | 対応 |
|---|---|---|
| スタック表記 | `CLAUDE.md` / `README.md`(L3,5,73) / `design-doc/references/templates.md`(L31) / `steering/references/spec.md`(L54) | `Next.js / ` を削除して `React /` に |
| description | `test-review` / `impl-review` / `review-performance` / `review-a11y` / `review-security` | 先頭の `Next.js/` を削除 |
| 観点軸（要設計判断） | `impl-review`(Axis4 ×2) / `frontend-code-review`(L111) | `React/Next.js` → `React` |
| Next固有ロジック（要設計判断） | `review-performance`(`next/dynamic`, CWV「Next.js固有」節) / `tdd/references/patterns.md`(Server Action / API Route テスト) | 下記参照 |

### 機械的置換でよい箇所
- スタック表記・description の `Next.js/` 削除は単純置換

### 一般化方針（★確定: 案B = フレームワーク非依存で SSR 観点を残す）
- `review-performance`: `next/dynamic` → `React.lazy` + `Suspense` / 動的 import に一般化。CWV 節は「Next.js 固有」をやめてフレームワーク中立（画像最適化・コード分割・フォント読み込み）に
- `tdd/patterns.md`: 「Server Action / API Route テスト」→ API クライアント / fetch 層のテストに一般化
- **SSR / ハイドレーション / コード分割の観点はフレームワーク中立な形で残す**（Vite SSR・React Router・TanStack 等でも有効）。特定フレームワークの API 名（`next/*`）には依存させない

---

## 論点2: 障害調査 + コード探索スキル

### 背景
`design-doc` は description で「障害調査に使う」と謳うが、実体は設計ドキュメント作成スキルで、調査手順（再現→切り分け→根本原因→修正）を持たない。看板と中身が乖離している。

### 決定方針
「障害調査」と「コード探索」は別の関心。分離して独立スキル化する。

### 新スキル案A: `debug`（障害調査）
- フロー: 再現確認 → 仮説立案 → 切り分け（二分探索的に） → 根本原因特定 → 修正方針
- 設計（design-doc）とは順序が逆（原因特定が先）なので別スキルが妥当
- 記録先: `.steering/[task]/investigation.md`（無ければ会話内）
- `design-doc` の description から「障害調査」を外し、`debug` へ委譲

### 新スキル案B: `explore`（コード探索）
- 役割: 既存コードの構造・依存・データフロー・命名規約を把握する
- **障害調査・新機能実装・リファクタすべての共通基盤**になる
- ★要確認: ビルトインの `Explore` エージェント / `feature-dev:code-explorer` と役割が重複
  - 案A: 独自スキルを新設（このリポジトリの規約・出力形式に最適化）
  - 案B: ビルトインを使う「使い方ガイド」薄いスキルに留める
  - 案C: `impl-from-design` が既に参照している "code-explorer" の実体を確認し、それを正式化
  - **暫定推奨: まず案C で現状の実体を確認 → 不足なら案A**

---

## 論点3: TDD を t_wada 流に寄せる

### 参考スキル評価（YunosukeYoshino/ImageScraper の tdd）
**良い点（取り込む）:**
1. 哲学の明文化 — 「テストは設計行為」「テストは仕様書」「小さく回す」
2. **Step1: 要件を振る舞いで分解**（テストケースリストを Red の前に作る）← 現状 tdd に無い
3. **AAA（Arrange-Act-Assert）構造の明示** ← 現状 tdd に無い
4. **境界値・異常系の体系的チェックリスト** ← 現状 tdd は弱い
5. アンチパターン集（実装詳細テスト / テスト間依存 / 過度なモック / 巨大テスト）
6. 1テスト1振る舞い・完了時チェックリスト

**取り込まない点:**
- Python / pytest 固定 → 自分は TS / Vitest のまま
- `description` の「自動適用」表現 → 誤発動リスクが高い。現状の明示トリガー方式を維持
- `tdd-wada-style` 命名 → `tdd` のまま

### 現状 tdd の強み（維持する）
- RTL クエリ優先順位 / MSW 規律 / In-source testing / コロケーション配置

### 改訂方針（課題2のスリム化と統合）
**SKILL.md 本文** = ツール非依存の判断軸に寄せる:
- 哲学（3原則）
- Red → Green → Refactor サイクル
- 振る舞い分解（テストケースリスト）
- AAA 構造
- 境界値・異常系チェックリスト
- アンチパターン集

**references/patterns.md** = ツール依存の具体例を集約:
- Vitest / RTL / MSW の API 例（現状本文の API 断片をここへ退避 → 課題2解決）

→ これで「論点3（哲学追加）」と「課題2（tdd 本文スリム化）」が同時に解決する。

---

## 論点4: agentskills.io 仕様の活用

出典: https://agentskills.io/specification

### 現状（実測）
全13スキルが仕様の制約をクリア済み（name=ディレクトリ名一致 / description ≤1024文字 / 本文 ≤500行）。
**構造は準拠済み**なので「違反の修正」は不要。価値は未使用の仕様要素の活用にある。

### 4-A. `compatibility` フィールドでスタック依存を分離（論点1・課題2と直結・最有用）
スタック依存を description から `compatibility` に出す。

```yaml
# Before
description: Next.js/TypeScript/Vitest... のテストコード品質をレビューする。「テストをレビューして」...
# After
description: テストコード品質をレビューする。「テストをレビューして」...   # スタック非依存
compatibility: React / TypeScript / Vitest / RTL / MSW 前提
```

→ **論点1（Next.js除去）と課題2（ツール依存の分離）が仕様準拠の形で同時に解決**。
description がスタック非依存になり、横展開時の可搬性も上がる。

### 4-B. `metadata` フィールドで横展開のドリフト追跡
CLAUDE.md の運用ルール「配置時にマスターのコミットハッシュを記録」の置き場として使う。

```yaml
metadata:
  version: "1.0"
  source-commit: <マスターのコミットハッシュ>
```

### 4-C. `skills-ref validate` で機械検証
`skills-ref validate ./skill` で frontmatter・命名規約を自動チェック。
→ `rule-audit` スキルの監査ステップ / CI に組み込む（手動目視を削減）。詳細は rule-audit メモ参照。

### 4-D. Progressive disclosure の定量基準を明文化
仕様の推奨値: **本文 <500行 / <5000トークン、metadata ~100トークン**。
→ 課題2（test-review/tdd スリム化）の**目標値**として採用。今後の肥大化防止ガイドにする。

### 採用しない / 保留
- `license`: 個人用なので任意。横展開を本格化するなら検討（優先度低）
- `allowed-tools`: 実験的。パーミッションは settings.json で管理しているため当面不要

---

## 実装順序

### 今回スコープ（スタック整理先行）
| 順 | 作業 | 論点 |
|---|---|---|
| 1 | Next.js → React 置換（スタック表記・description の機械的箇所） | 1 |
| 2 | Next 固有観点の一般化（`next/dynamic`→React.lazy、CWV中立化、Server Action→fetch層／SSR観点は中立で残す） | 1 |
| 3 | スタック依存を `compatibility` フィールドに分離（全スキルの frontmatter） | 4-A + 1 + 課題2 |
| 4 | `tdd` 改訂（哲学 + 振る舞い分解 + AAA + 境界値/異常系 + 本文スリム化、目標 <500行/<5000トークン） | 3 + 課題2 + 4-D |
| 5 | `test-review` 本文スリム化（references 新設、同上の目標値） | 課題2 + 4-D |
| 6 | README / CLAUDE.md / ワークフロー図のスタック表記更新 | 全体 |

> `metadata`（4-B）・`skills-ref validate`（4-C）は次フェーズ（横展開・CI 整備時）。

### 次フェーズ（別途着手）
| 作業 | 論点 |
|---|---|
| `impl-from-design` の "code-explorer" 実体確認 → `explore` の扱い決定 | 2 |
| `design-doc` から「障害調査」除去 + `debug` 新設 | 2 |
| E2E（Playwright）スキル新設 | 課題1-A |
