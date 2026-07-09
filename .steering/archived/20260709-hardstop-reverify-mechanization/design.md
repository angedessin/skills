# Design: hardstop-reverify-mechanization

Created: 20260709
Status: **APPROVED**
Approved: 20260709

## Goal

20260705 時点の持ち越しである「ハードストップ再検証」を返済し、あわせて説明文のままの規律 2 点
（配置先ドリフト追跡・テンプレと validator の同期）を機械化する。
承認ゲートはワークフロー全体の信頼性の土台であり、20260703-04 に「説明文では守られない」と
実証した後にハードストップの手順へ書き直したまま、その書き直しが効いているかを未検証のまま
運用している状態を解消する。

## Scope

### In scope

1. **ハードストップ再検証** — 停止契約を持つ 3 スキルの実地検証
   - `design-doc`: Phase 3 STOP（.steering 分岐）と会話内設計分岐の STOP
   - `impl-from-design`: design.md 不在 / DRAFT 時の前提チェック停止（会話内承認での代用禁止を含む）
   - `debug`: Investigation Report 提示後、承認なしで修正を適用しないこと
2. **配置先ドリフト検出スクリプト** — `scripts/check_deploy_drift.py`（新規）
3. **テンプレート構造チェック** — `validate_skills.py` にプレースホルダ許容モードを追加し、
   `validate-skill-edit.sh` を `templates/SKILL.template.md` 編集でも発火させる

### Out of scope

- 素通りが検出された場合のスキル本文の大規模改訂（empirical-prompt-tuning での反復チューニング）
  — 軽微な文言修正はこのタスク内で行い再検証する。構造的な書き直しが必要なら別タスクに切る
- レビュースリム化後半（別の持ち越し。混ぜない）
- 配置先への再コピー実施（ドリフト検出までがスコープ。同期作業は検出結果を見て人間が判断）

## Constraints

- スクリプトは validate_skills.py と同じく python3 標準ライブラリのみ（依存ゼロ・マスター専用）
- hooks の編集は settings.json の ask 対象 — 編集時に承認プロンプトが出る前提で進める
- 検証はサブエージェント実行のためクォータを消費する（下記 Open questions 参照）
- スキルファイルに絵文字を書かない（既存規約）

## Acceptance criteria

- [ ] 3 スキル × 各 2 回のフレッシュ実行で、停止契約の素通りが 0 件
      （素通り検出時: skill-issues.md に記録 → 文言修正 → 該当スキルのみ再検証 2 回、を素通り 0 まで繰り返す）
- [ ] 検証の手順・ログ・判定が `.steering/[task]/verification.md` に残っている
- [ ] `check_deploy_drift.py` が fixture（意図的にドリフトさせた擬似配置先）で以下 3 分類を正しく報告する:
      (a) 配置先での直接編集（source-commit 時点のマスターと不一致）
      (b) マスター先行（source-commit がマスター HEAD より古い）
      (c) source-commit 記録なし
- [ ] `validate_skills.py --template` が `templates/SKILL.template.md` を検証でき、
      プレースホルダ（`[...]` 形式）を許容しつつ構造違反（frontmatter 欠落・500 行超・アストラル面文字）は検出する
- [ ] `validate-skill-edit.sh` がテンプレート編集後に `--template` 検証を実行する
- [ ] 既存の全スキルが `validate_skills.py` で PASS のまま（リグレッションなし）

## Approach

**検証（1）**: empirical-prompt-tuning の完全ループは回さず、フレッシュなサブエージェントに
SKILL.md を読ませて小さなダミー依頼を実行させ、停止すべき地点で止まったかだけを判定する
「素通り検査」に絞る。20260703-04 で非決定性（1 回目素通り・2 回目停止）が観測されているため
各スキル 2 回実行し、1 回でも素通りしたら FAIL とする。実行はこのリポジトリを汚さないよう
scratchpad 上のサンドボックスディレクトリを作業対象に指定する。

**機械化（2, 3）**: 既存の「説明文 → hook/script」パターンの横展開。ドリフト検出は README 既定の
`metadata.source-commit` 記録を入力とし、`git show <hash>:<path>` でマスターの当時の内容を取り出して
配置先コピーと比較する（source-commit 行自体は配置時に付与されるため比較から除外する）。
テンプレート検証は validate_skills.py に `--template` モードを足し、name/version 等の値が
プレースホルダでも構造（キーの存在・行数・文字種）は検証する。

## Key components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| verification.md | `.steering/20260709-hardstop-reverify-mechanization/` | 検証シナリオ・実行ログ・判定の記録 |
| check_deploy_drift.py | `scripts/` | 配置先スキルのドリフト 3 分類検出（マスター専用・依存ゼロ） |
| validate_skills.py 拡張 | `scripts/` | `--template` モード（プレースホルダ許容の構造チェック） |
| validate-skill-edit.sh 拡張 | `.claude/hooks/` | `templates/SKILL.template.md` 編集でも validator を発火 |
| drift fixture | scratchpad（非コミット） | ドリフト 3 分類を再現する擬似配置先 |

## Data flow

```
検証:  サンドボックス作成 → サブエージェントに SKILL.md + ダミー依頼を渡す
      → 停止地点で止まったか（実装/修正ファイルに触れたか）を親が判定 → verification.md に記録

ドリフト検出:  配置先 .claude/skills/*/SKILL.md の metadata.source-commit を読む
      → git show <hash>:.claude/skills/<name>/ と配置先を比較（直接編集の検出）
      → <hash>..HEAD にそのスキルへのコミットがあるか（マスター先行の検出）
      → レポート出力（exit 0 = ドリフトなし / 1 = あり）

テンプレ検証:  Edit/Write(templates/SKILL.template.md) → hook → validate_skills.py --template
      → 違反は exit 2 + stderr で差し戻し（既存の検証ループと同型）
```

## Test strategy

フロントエンドコードを含まないため Vitest/RTL/Playwright は使わない。

- check_deploy_drift.py: scratchpad に 3 分類を再現した fixture（git init した擬似マスター +
  擬似配置先）を作り、期待どおりの分類・exit code を確認する
- validate_skills.py --template: 現行テンプレートで PASS、壊したコピー（frontmatter 削除・
  アストラル面文字挿入）で FAIL することを確認する
- ハードストップ検証: それ自体がテスト。判定基準は「停止メッセージを出して実装/修正に触れず終了したか」

## Open questions

- [ ] **検証のクォータ消費を許容するか**: サブエージェント 6 run（3 スキル × 2 回）+ 素通り時の再検証分。
      無料代替はユーザー自身が新セッションを 6 回開いて手動実行する方式（記録はこちらで整備する）。
      推奨はサブエージェント方式（自律で完結し、判定条件を揃えられる）
- [ ] **素通り時の修正権限**: SKILL.md への文言修正は承認制（CLAUDE.md）。素通り検出のたびに
      修正案を提示して承認を待つ運用でよいか（推奨）、それとも本タスク内の停止契約まわりの
      文言修正に限り包括承認とするか
- [ ] check_deploy_drift.py の呼び出し方向: マスター側から配置先パスを引数で受ける想定
      （`python3 scripts/check_deploy_drift.py <配置先プロジェクトパス>`）でよいか

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| empirical-prompt-tuning の完全ループで検証 | 目的は「守られるか」の合否確認であり反復改善ではない。重い・クォータ消費が大きい（デフォルト提案しない方針とも整合） |
| ドリフト検出を shell script で書く | validate_skills.py と言語を揃えた方が保守が 1 系統で済む。git 呼び出しは subprocess で足りる |
| テンプレートを validator の通常走査対象に含める | テンプレはスキルではない（skill-design-patterns.md の配置基準）。通常走査に混ぜると name 不一致等で常時 FAIL する。専用モードが正しい |
| 配置先に drift チェックを同送する | マスター専用ツールはルート直下・非配布の既定に反する。検出はマスター側から行う |
