# Requirements: workflow-hardening-slimming

Created: 20260611

## Goal

スキルセットのワークフローレビューで発見された実害のあるバグ（diff 取得・トリアージ・subagent ディスパッチ・.env 保護）を修正し、運用実績に対して過剰だった .steering 構造をスリム化し、自律進化ループ（compound）にスキル自身の失敗と昇格済みルールの効果検証を組み込む。「同じ指摘を二度しない」ループを実際に閉じることが目的。

## Scope

### In scope

1. **frontend-code-review のバグ修正**
   - diff ベースを「main...HEAD + 未コミット」の合算に変更
   - トリアージを `git diff --name-status -M` ベースに修正（リネーム判定を実現可能に）
   - どの分類にもマッチしないファイルは「ロジック変更」扱いにするフォールバック追加
   - subagent ディスパッチプロンプトに各サブスキル SKILL.md の絶対パス読み込みを明記
   - Phase 3 に重複指摘の統合ルール追加（同一 file:line は最も具体的な軸に帰属）
   - 修正後の再確認を「指摘があった軸のみ再ディスパッチする差分再レビュー」に変更
2. **settings.json** — `Read(./.env*)` 系の deny 追加
3. **README スリム化** — ワークフロー図 + 各スキル概要数行 + SKILL.md へのリンク構成に縮小
4. **.steering スリム化**
   - requirements.md を design.md に統合（design.md に Goal / Scope / Acceptance criteria を吸収）
   - session-log.md とハッシュ重複抑制を廃止、session-stop.sh をフラグ作成のみに縮小
   - 「.steering は複数セッションにまたがる見込みのタスクのみ作成」基準を design-doc に明文化
   - steering / design-doc / knowledge-capture / compound / impl-from-design の関連記述を連動修正
5. **自律進化ループ強化**
   - `.steering/[task]/skill-issues.md`（スキルの誤発動・曖昧指示の記録）を compound の入力に追加
   - スキル不具合に気づいたら skill-issues.md に追記する行動ルールを CLAUDE.md に追加
   - compound に codify-log.md × review-result.md の突合による「昇格済みルールの効果検証」を追加

### Out of scope

- 新スキルの追加（test-blind テスト作成オプションなどは別タスク）
- `.steering/archived/` 内の既存ファイルの書き換え（過去の構造のまま残す）
- empirical-prompt-tuning による全面再チューニング（必要なら別タスクで実施）
- lint ルール・CI の導入

## Constraints

- Stack: Claude Code skills（SKILL.md）/ bash hook / JSON settings — アプリコードなし
- CLAUDE.md は ≤200 行厳守
- スキルは孤立 subagent が読む前提で書く（docs/knowledge/skill-design-patterns.md）
- このタスク自体は現行プロセス（3ファイル構成）で進める。新構造はタスク完了後から適用

## Acceptance criteria

- [ ] frontend-code-review がコミット済み変更を含む diff を対象にできる手順になっている
- [ ] トリアージ手順が `--name-status -M` を使い、未マッチ時のフォールバックが明記されている
- [ ] ディスパッチプロンプトのテンプレートに SKILL.md パスの読み込み指示が含まれる
- [ ] settings.json で Read ツール経由の .env 読み取りが deny される
- [ ] README が「図 + 概要 + リンク」構成になり、スキル詳細の全文複製がなくなっている
- [ ] design-doc が requirements.md を作らず、design.md 単体 + tasklist.md 構成になっている
- [ ] session-stop.sh がフラグ作成のみ（ログ追記・ハッシュなし）になっている
- [ ] 全スキル・テンプレートから requirements.md / session-log.md への参照が消えている（archived 除く）
- [ ] compound が skill-issues.md を読み、codify-log との突合手順を持っている
- [ ] CLAUDE.md に skill-issues.md 追記ルールが追加され、200 行以内を維持している
