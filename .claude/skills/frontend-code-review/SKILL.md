---
name: frontend-code-review
description: "実装後のコードレビューに使う — 「コードをレビューして」「レビューしよう」「コードレビュー」「実装を確認して」などのフレーズが対象。diff トリアージでモードを判定し、ロジック/コンポーネント変更はフルモード（5エージェント並列）、リファクタリング/スタイルのみは軽量モード（直列）で実行。結果を .steering/[task]/review-result.md に書き込む。"
---

# Frontend Code Review

diff の変更種別を判定し、適切なモードでレビューを実行するオーケストレーター。

## When to use sub-skills directly

- テストコードのみを確認したい → `test-review` を直接使う
- 実装コードのみを確認したい → `impl-review` を直接使う
- セキュリティのみ → `review-security` を直接使う
- パフォーマンスのみ → `review-performance` を直接使う
- アクセシビリティのみ → `review-a11y` を直接使う

---

## Phase 1 — diff トリアージ

変更ファイルを取得して種別を分類する:

```bash
git diff --name-only HEAD
```

**分類ルール:**

| ファイルパターン | 種別 |
|---|---|
| `src/lib/`・`src/hooks/`・`src/api/`・`src/utils/` | ロジック変更 |
| `src/components/`・`src/app/`・`src/pages/` | コンポーネント変更 |
| リネーム・移動・型定義のみ | リファクタリング |
| `*.css`・`*.scss`・`config.*`・`*.env*`・`*.json` | スタイル/設定のみ |
| `*.md`・`*.txt` 等ドキュメント | 種別なし（モード判定に影響しない） |

**優先順位**: 拡張子パターンはディレクトリパターンより優先する。例: `src/components/Button.module.css` は `.css` に該当するため「スタイル/設定のみ」。

**モード判定:**
- **ロジック変更またはコンポーネント変更を含む** → フルモード（並列エージェント）
- **リファクタリング/スタイル/設定のみ** → 軽量モード（直列）

ユーザーにモードと対象ファイルを提示してから実行に進む:
```
トリアージ結果:
- ロジック変更: src/hooks/useAuth.ts, src/api/user.ts
- テストファイル: src/hooks/useAuth.test.ts
→ フルモード（5エージェント並列）で実行します
```

---

## Phase 2A — フルモード（並列エージェント）

以下の5エージェントを**単一メッセージ内で同時に**ディスパッチする。

各エージェントは対応するサブスキルのロジックを実行し、軸ごとの結果を返す:

- **test-agent**: `test-review` スキルの全ロジックを実行
  - スコープ: `*.test.ts`・`*.spec.ts`・`*.test.tsx`
  - 5軸: 実装エコー・アサーション品質・MSW 規律・RTL クエリ・カバレッジ意図

- **impl-agent**: `impl-review` スキルの全ロジックを実行
  - スコープ: `.ts`・`.tsx`（テストファイルを除く）
  - 5軸: 設計整合性・プロジェクト規約・TypeScript・React/Next.js・基本 a11y

- **security-agent**: `review-security` スキルの全ロジックを実行
  - スコープ: `.ts`・`.tsx`（テストファイルを除く）
  - 4軸: XSS・型安全・env var・依存関係

- **perf-agent**: `review-performance` スキルの全ロジックを実行
  - スコープ: `.ts`・`.tsx`（テストファイルを除く）
  - 3軸: Bundle サイズ・再レンダリング・CWV

- **a11y-agent**: `review-a11y` スキルの全ロジックを実行
  - スコープ: `.tsx`（テストファイルを除く）
  - 4軸: セマンティクス・ARIA・フォーカス管理・キーボード操作

---

## Phase 2B — 軽量モード（直列）

リファクタリング/スタイル/設定のみの変更に対して直列で実行:

1. `test-review` を実行
2. `impl-review` を実行
3. Phase 3 に進む（security/perf/a11y はスキップ）

---

## Phase 3 — 統合サマリーの出力と記録

全エージェントの結果をまとめて出力する:

```
## Code Review Summary

### テスト（test-review）
重要な問題: N件
| Axis | 問題 | ファイル | 分類 |
|------|------|----------|------|
| [軸] | [内容] | [file:line] | [分類] |

### 実装（impl-review）
重要な問題: N件
| Axis | 問題 | ファイル |
|------|------|----------|
| [軸] | [内容] | [file:line] |

### セキュリティ（review-security）
重要な問題: N件
| Axis | 問題 | ファイル |
|------|------|----------|

### パフォーマンス（review-performance）
重要な問題: N件
| Axis | 問題 | ファイル |
|------|------|----------|

### アクセシビリティ（review-a11y）
重要な問題: N件
| Axis | 問題 | ファイル |
|------|------|----------|

### 全体サマリー
- 合計の重要な問題: N件
- モード: フル / 軽量
```

### review-result.md への書き込み

`.steering/[task]/` タスクディレクトリが存在する場合のみ `review-result.md` を書き込む。タスクディレクトリが存在しない場合は出力のみで書き込みを行わない。
`templates.md` の形式に従う。ファイルが存在しない場合は「## Code Review Result\n\n### 指摘事項\n- [ ] [Axis] [内容] [file:line]」の形式で合理的に生成してよい。修正状況チェックボックスはすべて未チェックで初期化する。

書き込み後に `.codify-needed` フラグを作成する:
```bash
touch .steering/[task]/.codify-needed
```

書き込み完了後にユーザーに通知:
```
review-result.md を更新しました。

次のステップ:
- [ ] 指摘事項を修正する（review-result.md を参照）
- [ ] 修正後に再確認
- [ ] Deploy（PR 作成 → CI → マージ）
- [ ] compound スキルで学びをルール・知識に昇格（.codify-needed が作成されました）
```

---

## 修正後の再確認フロー

ユーザーが修正完了を伝えた場合:
1. `review-result.md` の指摘チェックボックスを確認
2. 修正済み項目に `✅ DONE` を追記
3. 残っている未修正の指摘を再提示
4. 全指摘が解消されたら `review-result.md` の Status を `RESOLVED` に更新

---

## Related skills

- `test-review` — テストコードのみを審査（単独利用可）
- `impl-review` — 実装コードのみを審査（単独利用可）
- `review-security` — セキュリティ観点のみを審査（単独利用可）
- `review-performance` — パフォーマンス観点のみを審査（単独利用可）
- `review-a11y` — アクセシビリティ観点のみを審査（単独利用可）
- `compound` — レビュー完了後に学びをルール・知識に昇格
- `knowledge-capture` — レビューで発見したパターンを docs/ に保存
