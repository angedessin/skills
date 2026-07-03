# スターターキット — 他プロジェクトへのスキル配置手順

対象: このマスターリポジトリから他プロジェクトへスキルを配置する人。
配布方式は手動コピー（[ADR 20260612](decisions/20260612-manual-copy-skill-distribution.md)）— **どのスキルを持っていくかは人が選ぶ**。それ自体が誤発動を防ぐガードレール。

---

## 推奨構成

| セット | スキル | いつ入れるか |
|---|---|---|
| **最小** | design-doc / steering / frontend-code-review / impl-review / test-review / knowledge-capture | まず試すならこれ。設計ゲート + レビュー 2 軸 + 知見保存の最小複利ループ |
| **拡張 1: レビュー厚み** | review-security / review-a11y / review-performance / review-correctness / review-ui | frontend-code-review のフルモード（7 エージェント並列）を使う場合 |
| **拡張 2: ワークフロー** | impl-from-design / tdd / e2e / debug | 設計→実装の型・テスト駆動・E2E・障害調査まで揃える場合 |
| **メタ層** | compound / rule-audit / empirical-prompt-tuning / feature-pipeline | 自己改善ループとオーケストレーションまで運用する場合（このマスター級の運用） |

- frontend-code-review はサブスキル未配置でも動く（未配置分をスキップして報告する縮退動作）
- feature-pipeline は依存サブスキルが揃っている前提のため最小セットに含めない

## フロントエンド以外・別ワークフローのプロジェクトへの導入

スキルは「本文 = スタック非依存の判断軸 / references = スタック固有の具体例」で分離されているため、フロントエンド以外にも層を選んで導入できる:

| 導入先 | 持っていけるもの |
|---|---|
| **どんなスタックでも**（バックエンド・CLI・インフラ含む） | メタワークフロー: design-doc / steering / debug / knowledge-capture / compound / rule-audit / feature-pipeline / empirical-prompt-tuning。設計承認ゲート・障害調査・知見蓄積・剪定はコードの種類に依存しない |
| **テストを書くプロジェクト全般** | tdd / test-review / e2e。本文は判断軸のみなので、references/patterns.md を自分のテストスタック（pytest / JUnit / Go test 等）で再生成する |
| **フロントエンド（React 以外も可）** | frontend-code-review + review-* 全 7 軸。判断軸は概ねフレームワーク中立（a11y / CWV / XSS / correctness）。compatibility とコード例を自分のフレームワークに合わせる |
| **フロントエンド以外でのレビュー** | review-correctness は言語横断で使える（境界条件・null・非同期レース・エラー握りつぶし）。review-a11y / ui / performance は対象外なので配置しない |

既存の開発ワークフロー（レビュー体制・ブランチ運用・チケット管理）があるプロジェクトでは、**スキル本文を書き換えず**、配置先 CLAUDE.md の発動ポリシー側で接続を定義する（例:「PR 作成は既存のチーム運用に従い、feature-pipeline の Phase 3.5 はスキップする」「設計レビューは design.md ではなく既存の Design Doc プロセスに読み替える」）。

## 配置手順（5 ステップ）

1. **選ぶ** — 上の表からプロジェクトに必要なスキルを選ぶ（全部入れない。無関係なスキルは誤発動の種）
2. **コピー** — 配置先の `.claude/skills/` にディレクトリごとコピーする
3. **source-commit を記録** — 各スキルの frontmatter の `metadata:` にマスターの配置時点 HEAD を追記する:
   ```yaml
   metadata:
     version: "1.0"
     source-commit: <マスターで git rev-parse HEAD した値>
   ```
   （`version` はコピー元の値を保つ — 上の例の "1.0" で上書きしない。マスター側には source-commit を書かない — 配置先にだけ意味がある情報）
4. **references を再生成** — `references/` が example と明記されているスキル（tdd / test-review / e2e / review-ui）は、配置先のスタックに合わせて中身を再生成する。使わない場合は削除してよい — 本文は判断軸のみで縮退動作する
5. **CLAUDE.md に発動ポリシー節を作る** — 下の雛形から。行動ルールは配置先で育てる（マスターの CLAUDE.md を丸ごとコピーしない）
6. **ガードレールも同送する（サプライチェーン対策）** — スキルだけコピーすると、references が指示する `npx` 実行等に対する防御が配置先に存在しない状態になる:
   - マスターの `.claude/settings.json` から **permissions（allow / ask / deny）セクション**を配置先の settings.json に取り込む（パッケージインストール deny・npx / rm -r の ask・env / 鍵ファイルの Read deny・ガードレール自己改変の ask）
   - `.claude/hooks/guard-env-read.sh` をコピーし、settings.json の `hooks.PreToolUse` 登録も移す（deny の前置一致では防げない .env 読み取りの迂回を全文検査で ask に落とす）
   - `session-stop.sh`（Stop hook）は `.steering/` ワークフローを採用する場合のみコピーする
   - `settings.local.json` はコピーしない（マシン固有の承認履歴）
   - 配置先の `.npmrc` に `ignore-scripts=true` を推奨（install 時の postinstall 実行 = サプライチェーン攻撃の主経路を既定で遮断。ビルドスクリプトが必要なパッケージだけ個別に許可する運用）

## ドリフト確認と改善の還元

- **ドリフト確認**: マスターのリポジトリで `git diff <source-commit> -- .claude/skills/<name>` — 配置後にマスター側で入った改善が一覧できる
- **改善の還元**: 配置先で直接編集しない。改善はマスターに還元し、再コピーで配る（コピー時に source-commit を更新する）
- **配置前チェック**: マスター側で `python3 scripts/validate_skills.py` が全 PASS であることを確認してからコピーする

## CLAUDE.md 雛形（発動ポリシー節のみ）

```markdown
## スキル発動ポリシー

- 新しいタスクを開始するときは design-doc を使い、design.md が APPROVED になるまで実装しない
- 実装後のコードレビューは frontend-code-review を使う
- セッションで得た知見は knowledge-capture で docs/ に保存する
<!-- 配置したスキルに合わせて追記・削除する。行動ルール（プロジェクト固有の規約）はこの下に育てていく -->
```
