# Design: workflow-hardening-slimming

Status: **APPROVED**
Approved: 20260611

## Approach

変更は「バグ修正（正しさ）」「スリム化（構造）」「進化ループ強化（compound）」の3グループに分け、この順で適用する。バグ修正は他と独立なので先行させ、スリム化は design-doc → templates → hook → 参照スキル群の順で「定義元 → 参照元」の方向に直す（参照切れを作らないため）。スキル本文の修正はすべて「孤立 subagent が読んでも実行可能か」を基準に書く（docs/knowledge/skill-design-patterns.md 準拠）。

## Key components

| Component | Location | 変更内容 |
|-----------|----------|----------|
| frontend-code-review | `.claude/skills/frontend-code-review/SKILL.md` | Phase 1: diff ベース変更（base branch との merge-base + 未コミット合算）、`--name-status -M` トリアージ、未マッチ→ロジック変更フォールバック。Phase 2A: ディスパッチプロンプトのテンプレート新設（SKILL.md パス明記）。Phase 3: 同一 file:line 指摘の統合ルール。再確認フロー: 指摘があった軸のみの差分再レビューに置換 |
| settings.json | `.claude/settings.json` | `deny` に `Read(./.env*)`・`Read(./**/.env*)` を追加 |
| README | `README.md` | ワークフロー図・スキル関係図は維持。各スキルは「起動タイミング1行 + 概要2〜3行 + SKILL.md リンク」に縮小。トリアージ表・レビュー軸表など SKILL.md と重複する詳細を削除 |
| design-doc | `.claude/skills/design-doc/SKILL.md` | requirements.md 作成を廃止し design.md に Goal/Scope/Acceptance criteria セクションを統合。「複数セッションにまたがる見込みのタスクのみ .steering を作る」基準を When NOT to use に明文化 |
| templates | `.claude/skills/design-doc/references/templates.md` | design.md テンプレートに Goal/Scope/Acceptance を統合。requirements.md テンプレート削除。skill-issues.md テンプレート追加 |
| session-stop.sh | `.claude/hooks/session-stop.sh` | session-log.md 追記・ハッシュ重複抑制を削除。「アクティブタスクに capture_done がなければ .capture-needed を作成してリマインド出力」のみに縮小（約 20 行） |
| steering | `.claude/skills/steering/SKILL.md` + `references/spec.md` | requirements.md / session-log.md / .last-log-hash への参照を削除。resume モードの読み込み対象を design.md + tasklist.md（+ 任意ファイル）に変更 |
| knowledge-capture | `.claude/skills/knowledge-capture/SKILL.md` | 入力から session-log.md を外し、decisions.md / review-result.md / 会話コンテキストを入力に変更 |
| impl-from-design | `.claude/skills/impl-from-design/SKILL.md` | requirements.md 参照があれば design.md の該当セクション参照に変更 |
| compound | `.claude/skills/compound/SKILL.md` | Step 1 の入力に skill-issues.md を追加・session-log.md を削除。Step 2 に「codify-log.md の昇格済みルールと今回の review-result.md を突合し、再発していればルール自体を改善対象にする」を追加。skill-issues.md 由来の候補は empirical-prompt-tuning の起動提案に接続 |
| CLAUDE.md | `CLAUDE.md` | 「スキルの誤発動・指示の曖昧さに気づいたら `.steering/[task]/skill-issues.md` に1行追記」ルールを追加。セッション開始手順から session-log 関連があれば削除 |

## Data flow

```
[レビュー] frontend-code-review
  base = merge-base(main, HEAD) の diff + 未コミット diff（合算）
  → --name-status -M でトリアージ（未マッチ → ロジック変更）
  → 各 subagent へ「SKILL.md パス + 対象ファイル一覧」を明記してディスパッチ
  → Phase 3 で file:line 重複統合 → review-result.md
  → 修正後: 指摘のあった軸のみ再ディスパッチ → RESOLVED

[進化ループ] セッション中の気づき → skill-issues.md（人間 or Claude が追記）
  review-result.md ─┬→ compound Step 2: 新規パターン抽出
  codify-log.md   ──┤   + 昇格済みルールとの突合（再発検知）
  skill-issues.md ──┘   + スキル不具合 → empirical-prompt-tuning 起動提案
```

## Test strategy

アプリコードがないため、検証は以下で行う:

- **hook**: `bash -n` で構文確認後、一時 git リポジトリに `.steering/test-task/` を作って手動実行し、(1) フラグ作成 (2) capture_done 存在時にスキップ (3) .steering なしで無害終了、を確認
- **settings.json**: `jq .` でパース確認
- **参照整合**: 全編集完了後に `grep -rn "requirements\.md\|session-log\.md\|last-log-hash" .claude/ CLAUDE.md README.md` を実行し、archived 以外でヒットゼロを確認
- **スキル品質**: frontend-code-review（変更量最大）のみ empirical-prompt-tuning を 1 イテレーション実施（Open question 参照）

## Open questions

- [ ] **ベースブランチの特定方法**: `git symbolic-ref refs/remotes/origin/HEAD` で自動検出し、remote がなければ `main` にフォールバック、で良いか？（このリポジトリ自体 remote なし運用のため、フォールバック既定は重要）
- [ ] **session-log.md 廃止後の knowledge-capture**: 入力が decisions.md / review-result.md / 会話コンテキストになる。「diff 統計の自動記録」は完全に捨てて良いか？（git log で代替可能という判断）
- [ ] **skill-issues.md の置き場**: `.steering/[task]/` 配下のみとし、.steering がない軽量セッションでは記録せずその場で対処、で良いか？（横断ファイル `docs/skill-issues.md` 案は管理が増えるため不採用の提案）
- [ ] **README の縮小幅**: 各スキル 3〜4 行 + リンクまで削る提案。トリアージ表・レビュー軸表も README からは消える（SKILL.md が一次情報）。許容できるか？
- [ ] **empirical-prompt-tuning の実施範囲**: frontend-code-review のみ 1 イテレーションの提案（全スキル実施はコスト過大）。スキップして後日でも可。どうするか？

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| impl-review の a11y/TS 軸をフルモード時にスキップして重複を防ぐ | サブスキルの完全性が条件分岐で崩れ、単独利用時と挙動が分かれる。Phase 3 の統合ルールで吸収する方が単純 |
| .steering を全廃して git ブランチ + PR 説明に寄せる | 設計承認ゲート（Status: APPROVED）とフラグによる福利化ループの置き場が消える。スリム化で十分 |
| フラグファイルを廃止して「review-result.md に未解決項目があるか」等の派生状態に置換 | hook・スキル双方の判定ロジックが複雑化する。フラグの方が単純で、実害が出ていない |
| session-log.md を残して内容を充実させる（判断・学びを hook で記録） | hook は git 情報しか取れず、判断・学びは会話の中にしかない。decisions.md / skill-issues.md への手動追記の方が情報の質が高い |
| README を自動生成（SKILL.md から抽出） | 生成スクリプトの保守が増える。個人リポジトリの規模ではリンク化で十分 |

## Research

（既存コードベースの調査は本セッションのレビューで完了済み。対象ファイル・問題点は会話およびKey componentsに反映済み）
