# 現在のISSUE / 改善方針 — 既存スキルの修正

作成日: 2026-06-13 / 最終更新: 2026-06-17
対象: `.claude/skills/` 配下のスキルセット
スコープ前提: 個人用 / React / TypeScript / Vitest / RTL / MSW / Playwright
ステータス: **方針確定（実装承認待ち）**

> このドキュメントは「**既存スキルをどう直すか**」を扱う。ゼロから作る新スキルの設計は [new-skills.md](./new-skills.md)、スキルの評価・QA の仕組みは [evaluation-system.md](./evaluation-system.md) を参照。

---

## 確定事項（2026-06-13 確認済み）

1. SSR/RSC: **フレームワーク非依存で SSR 観点は残す**（案B）
2. 今回スコープ: **スタック整理を先行**（論点1 + 論点3 + 課題2 + 論点4-A の `compatibility` 分離）
3. 新スキル（debug / explore / E2E / rule-audit / prompt-lint）・metadata / validate 整備は次フェーズ → [new-skills.md](./new-skills.md)

---

# Part A. 課題（診断）

## 課題1: ワークフロー上に居場所のないスキル領域

> 1-A / 1-B は新スキルで埋める。設計は [new-skills.md](./new-skills.md) に集約。ここでは穴の所在のみ記録する。

### 1-A. E2E テスト（Playwright）— 最優先 → 新スキル `e2e`
スタックに `Playwright` が明記され `tdd/references/patterns.md` に「E2E」節もあるが、**E2E を主役にしたスキルが存在しない**。実装フェーズ [3] の `tdd` は Vitest + RTL + MSW 専用、`test-review` は Playwright 設定の監査を「対象外」と宣言。結果 E2E は付録扱いで、いつ・どの粒度で書くか、どの軸でレビューするかをワークフロー上で誰も担っていない。
→ **設計は [new-skills.md](./new-skills.md) の `e2e`。**

### 1-B. デバッグ / 障害調査 → 新スキル `debug`
`design-doc` が description で「障害調査に使う」と謳うが、実体は設計ドキュメント作成スキルで調査手順（再現→切り分け→根本原因→修正）を持たない。**看板と中身が乖離**。バグ修正は新機能とフローが異なる（設計より先に原因特定が要る）のに専用手順がない。
→ **設計は [new-skills.md](./new-skills.md) の `debug`。`design-doc` の description から「障害調査」を外す作業もそちらに記載。**

### 1-C. PR / 統合フェーズ（新スキル不要）
メインワークフローが [8] `steering archive` で終わり、**変更を世に出すステップ（PR 作成・CI 確認）が図にない**。
**対応**: `pr-create`（ビルトイン）をワークフロー図に位置づける。新規スキルは不要の可能性が高い。

> 補足: リファクタリング専用スキルは `/simplify` 等のビルトインと `frontend-code-review` 軽量モードで実質カバーされており、新規作成の優先度は低い。

---

## 課題2: ツール依存の偏り（テスト系2スキルに集中）

全スキルが均等にツールへ寄っているのではなく、**テスト系2スキルだけが突出**している。

### SKILL.md 本文でのツール名出現数（実測）
| 層 | スキル | 出現数 | 評価 |
|---|---|---|---|
| ツール非依存 | `steering` / `design-doc` / `compound` | 0 | ワークフロー構造そのもの。完全に汎用 |
| 軽度依存 | `review-*` / `impl-review` / `impl-from-design` / `knowledge-capture` | 1–6 | 観点が主役、ツールは例示。健全 |
| 重度依存 | `tdd` | 21 | references があるのに本文にも API が漏れている |
| 重度依存 | `test-review` | 17 | references を持たず本文に API が混在 |

### 問題の本質
「汎用性が足りない」問題ではなく、**判断ロジックと API 例が本文で混在している（関心の分離不足）** という可読性・保守性の問題。スコープが「個人用 React/TS」と明示され、横展開も「別スタックには配置しない」と決まっているため、スタック固定そのものは設計意図であって欠陥ではない。汎用化を追うのは YAGNI。

### あるべき関心の分離
- **SKILL.md 本文** = 「何を見るか・どう判断するか」（観点・ロジック）→ スタック非依存に保つ
- **references/** = 「具体的にどう書くか」（API・コマンド例）→ スタック依存を集約

こうしておけば別スタックへ移す場合も本文はそのまま references だけ差し替えで済む。

### 対応案
- `test-review`: references を新設し、MSW ハンドラ例・RTL クエリ具体例を退避。本文は「実装エコー」「アサーション品質」等の判断軸に絞る
- `tdd`: 本文に残る API 断片を `references/patterns.md` に寄せる（論点3と統合）
- それ以外の11スキルは現状維持で問題なし

---

## 課題3: レビュースキルの観点に欠落がある

現状のレビュー軸は5スキル21軸。**テスト・設計整合・TS・React・セキュリティ・パフォーマンス・a11y** はよく揃っているが、4つの観点が欠けている。

### 現状のカバレッジ
| スキル | 軸 |
|---|---|
| `test-review` | 実装エコー / アサーション品質 / MSW規律 / RTLクエリ / カバレッジ意図 |
| `impl-review` | 設計整合性 / プロジェクト規約 / TypeScript / React / 基本a11y |
| `review-security` | XSS / 型安全 / env var / 依存関係 |
| `review-performance` | Bundleサイズ / 再レンダリング / CWV |
| `review-a11y` | セマンティクス / ARIA / フォーカス管理 / キーボード操作 |

### 3-A. correctness（ロジックバグ）— 最大の盲点
レビューの根幹なのに**専任軸がない**。impl-review は「設計に沿っているか」「Reactパターンとして妥当か」は見るが、コードが正しく動くかは主軸にしていない。
- 境界条件 / off-by-one、null/undefined の取りこぼし
- 非同期のレースコンディション、stale closure
- 状態遷移の矛盾、エラーの握りつぶし（`catch {}`）

★要判断: ビルトイン `/code-review` が correctness を担う設計か？ そうでなければ `frontend-code-review` のオーケストレーション（5エージェント）に correctness 担当が不在。自前軸を足すか、ビルトインに委ねるかを決める。

### 3-B. UI / ビジュアル / レスポンシブ — フロントエンド特有の明確な欠落
**観点が完全にゼロ**。フロントエンドなのにビジュアルレビューがない。
- CSS の破綻、レスポンシブ崩れ、ブレークポイント
- デザイントークン / Tailwind 規約の遵守、ダークモード対応
- レイアウトの一貫性（spacing・typography スケール）

a11y はセマンティクス、performance は CLS を見るが、視覚的正しさは誰も見ていない。

### 3-C. UX状態の網羅性 / エラーハンドリング
loading / error / empty / disabled / オフライン状態の**実装漏れ**、エラーバウンダリの有無。impl-review にも correctness にも分散しうるが専任なし。フロントの体感品質に直結（特に空状態・エラー状態の未実装は頻出）。

### 3-D. i18n / l10n（条件付き）
文字列ハードコード、日付/数値/通貨フォーマット、複数形、RTL、テキスト長膨張。**プロジェクトが国際化対応する場合のみ**重要なのでスコープ次第。

### 対応案
- 3-A: `frontend-code-review` に correctness 軸を追加、または `impl-review` に Axis 拡張、またはビルトイン `/code-review` 委譲を明文化
- 3-B: `review-ui`（ビジュアル/レスポンシブ/デザイン整合）を新設、または `impl-review` に UI 軸追加
- 3-C: `impl-review` か correctness 軸に UX状態チェックを統合
- 3-D: i18n 対応プロジェクト向けのオプション軸として `review-security` 等に相乗り or 独立スキル

---

# Part B. 改善方針（処方）

## 論点1: 技術スタックから Next.js を外す

### 背景・決定
- Next.js は Vercel 依存が強すぎる（Server Actions / App Router / `next/image` / `next/dynamic` / Vercel 前提の CWV 最適化）
- スタック記述は **React** ベースにする
- 新スタック表記: `React / TypeScript / Vitest / React Testing Library / MSW / Playwright`
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

## 論点3: TDD を t_wada 流に寄せる（課題2のスリム化と統合）

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
RTL クエリ優先順位 / MSW 規律 / In-source testing / コロケーション配置

### 改訂方針
**SKILL.md 本文** = ツール非依存の判断軸に寄せる:
- 哲学（3原則）/ Red → Green → Refactor サイクル / 振る舞い分解（テストケースリスト）/ AAA 構造 / 境界値・異常系チェックリスト / アンチパターン集

**references/patterns.md** = ツール依存の具体例を集約:
- Vitest / RTL / MSW の API 例（現状本文の API 断片をここへ退避 → 課題2解決）

→ これで「論点3（哲学追加）」と「課題2（tdd 本文スリム化）」が同時に解決する。目標値は 4-D（<500行 / <5000トークン）。

---

## 論点4: agentskills.io 仕様の活用

出典: https://agentskills.io/specification

### 現状（実測）
全13スキルが仕様の制約をクリア済み（name=ディレクトリ名一致 / description ≤1024文字 / 本文 ≤500行）。**構造は準拠済み**なので「違反の修正」は不要。価値は未使用の仕様要素の活用にある。

### 4-A. `compatibility` フィールドでスタック依存を分離（論点1・課題2と直結・最有用）
スタック依存を description から `compatibility` に出す。
```yaml
# Before
description: Next.js/TypeScript/Vitest... のテストコード品質をレビューする。「テストをレビューして」...
# After
description: テストコード品質をレビューする。「テストをレビューして」...   # スタック非依存
compatibility: React / TypeScript / Vitest / RTL / MSW 前提
```
→ **論点1（Next.js除去）と課題2（ツール依存の分離）が仕様準拠の形で同時に解決**。description がスタック非依存になり、横展開時の可搬性も上がる。

### 4-B. `metadata` フィールドで横展開のドリフト追跡
CLAUDE.md の運用ルール「配置時にマスターのコミットハッシュを記録」の置き場として使う。
```yaml
metadata:
  version: "1.0"
  source-commit: <マスターのコミットハッシュ>
```

### 4-C. `skills-ref validate` で機械検証
`skills-ref validate ./skill` で frontmatter・命名規約を自動チェック。→ `rule-audit` スキルの監査ステップ / CI に組み込む（手動目視を削減）。詳細は [new-skills.md](./new-skills.md) の `rule-audit` 参照。

### 4-D. Progressive disclosure の定量基準を明文化
仕様の推奨値: **本文 <500行 / <5000トークン、metadata ~100トークン**。→ 課題2（test-review/tdd スリム化）の**目標値**として採用。今後の肥大化防止ガイドにする。

### 採用しない / 保留
- `license`: 個人用なので任意。横展開を本格化するなら検討（優先度低）
- `allowed-tools`: 実験的。パーミッションは settings.json で管理しているため当面不要

---

# Part C. 実装順序

## 今回スコープ（スタック整理先行）
| 順 | 作業 | 論点 |
|---|---|---|
| 1 | Next.js → React 置換（スタック表記・description の機械的箇所） | 1 |
| 2 | Next 固有観点の一般化（`next/dynamic`→React.lazy、CWV中立化、Server Action→fetch層／SSR観点は中立で残す） | 1 |
| 3 | スタック依存を `compatibility` フィールドに分離（全スキルの frontmatter） | 4-A + 1 + 課題2 |
| 4 | `tdd` 改訂（哲学 + 振る舞い分解 + AAA + 境界値/異常系 + 本文スリム化、目標 <500行/<5000トークン） | 3 + 課題2 + 4-D |
| 5 | `test-review` 本文スリム化（references 新設、同上の目標値） | 課題2 + 4-D |
| 6 | README / CLAUDE.md / ワークフロー図のスタック表記更新 | 全体 |

> `metadata`（4-B）・`skills-ref validate`（4-C）は次フェーズ（横展開・CI 整備時）。

## 次フェーズ（[new-skills.md](./new-skills.md) で詳細設計）
| 作業 | 出典課題 |
|---|---|
| `debug` 新設 + `design-doc` から「障害調査」除去 | 1-B / 論点2 |
| `explore`（コード探索）の扱い決定（ビルトイン重複の確認含む） | 論点2 |
| `e2e`（Playwright）新設 | 1-A |
| `rule-audit` 新設 | — |
| `prompt-lint` 新設 | — |

---

## 優先度サマリ
| 優先 | 課題 | 種別 | 工数感 | 詳細 |
|---|---|---|---|---|
| 高 | レビューに correctness 軸が不在（3-A） | 機能 or 設計判断 | 小〜中 | 本書 課題3-A |
| 高 | UI/ビジュアル/レスポンシブのレビュー観点ゼロ（3-B） | 機能追加 | 中 | 本書 課題3-B |
| 高 | E2E（Playwright）スキルの欠落 | 機能追加 | 中 | [new-skills.md](./new-skills.md) |
| 中 | UX状態網羅 / エラーハンドリングのレビュー（3-C） | 整理 or 機能 | 小〜中 | 本書 課題3-C |
| 中 | `test-review` / `tdd` 本文スリム化 | 整理 | 小〜中 | 本書 課題2 / 論点3 |
| 中 | デバッグ/障害調査の扱い（新設 or description 修正） | 機能 or 整理 | 小〜中 | [new-skills.md](./new-skills.md) |
| 低 | i18n/l10n レビュー（国際化対応プロジェクトのみ）（3-D） | 機能追加 | 小〜中 | 本書 課題3-D |
| 低 | PR/統合フェーズのワークフロー図への位置づけ | ドキュメント | 小 | 本書 課題1-C |
