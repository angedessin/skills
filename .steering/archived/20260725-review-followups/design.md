# 設計: レビュー積み残しの解消

Status: **APPROVED — in progress**
Date: 20260725（実効性確認の実測: 20260726）

## 目的

`20260725-skillset-hardening`（アーカイブ済み）のレビューで DEFERRED にした指摘を解消する。**先頭の 1 件は他と性質が違い、否定されると前タスクの結論が撤回対象になる**ため最優先で片付ける。

前タスクの記録: `.steering/archived/20260725-skillset-hardening/`（`review-result.md` が指摘の一次情報・`decisions.md` の末尾にバックログ）

## 最優先: hook の実効性確認（セッション再起動後の最初にやる）

**背景**: 承認前の書き込みを止める機械防御として `permissions.ask`（CLAUDE.md / docs/knowledge/ / docs/decisions/）と `.claude/hooks/guard-gated-write.sh`（PreToolUse・Bash 経由の書き込みリダイレクトを ask に落とす）を入れた。だが**前セッションでは一度も発火を確認できなかった**。

**前セッションで判明していること**:
- `guard-gated-write.sh` はスクリプト単体では実ペイロードで正しく発火する（発火 5/5・誤検知 0/5）
- 登録構造も正しい（配列 2 番目でも独立 matcher ブロックでも試した）
- 同じ PreToolUse(Bash) の `guard-env-read.sh`（セッション開始時から存在）は**発火する**
- セッション中に追加した `remind-config-docs.sh`（PostToolUse）は**登録直後に発火した**
- → 「設定が再読込されない」では説明できない。**原因未解明**

### 手順

1. **セッションを再起動してから**、次を実行する:
   ```bash
   echo test > docs/decisions/_probe.md
   ```
2. 結果を判定する:
   - **確認ダイアログが出た** → hook は機能している。`_probe.md` を削除し、`ask` 側も同様に確認（`docs/knowledge/` 配下を Edit してプロンプトが出るか）。前タスクの「機械の別防御を足した」結論が裏づけられる
   - **出ずに書き込まれた** → **機械防御は成立していない**。`.steering/archived/20260725-skillset-hardening/review-result.md` の該当指摘と `docs/knowledge/claude-code-config.md` の記述を「効いていない」に訂正し、`guard-gated-write.sh` と ask エントリを外すか作り直すかを判断する（**書いたまま放置しない**）
3. どちらでも `docs/decisions/_probe.md` を必ず削除する

### 実測結果（20260726・セッション再起動後）

**結論: 機械防御は成立している。** 全経路でゲートが発火した。前タスクの「機械の別防御を足した」という結論は裏づけられた。

| 経路 | 期待 | 実測 | 観測者 |
|---|---|---|---|
| Bash リダイレクト `echo test > docs/decisions/_probe.md` | ask | 発火（guard hook の理由文つき） | 人間 |
| `Write(./docs/knowledge/_probe.md)` | ask | 発火 | 人間 |
| `Edit(./docs/knowledge/_probe.md)` | ask | 発火（単独実行で再確認） | 人間 |
| `remind-config-docs.sh` skills 分岐（`.claude/skills/_probe/SKILL.md`） | 本文注入 | 注入された | Claude |
| `remind-config-docs.sh` config 分岐（`.claude/hooks/_probe.sh`） | 本文注入 | 注入された | Claude |
| `remind-config-docs.sh` 誤発火（`docs/knowledge/` の編集） | 無発火 | 無発火 | Claude |
| `remind-config-docs.sh` セッション 1 回制限（2 回目の編集） | 無注入 | 無注入・マーカー生成を確認 | Claude |

**前セッションの謎について**: `guard-gated-write.sh` は PreToolUse でありながら、セッション再起動後の今回は発火した。`claude-code-config.md` に記録した「セッション中に追加した PreToolUse hook が効かなかった」実測と矛盾しない — **原因はセッション中の追加に限った現象**であり、再起動後は正常。この切り分けが今回付いた。

**副次的な確認**: `validate-skill-edit.sh` も probe スキル（`description` の引用符・`metadata.version`・"When NOT to use" 見出しの欠落）を検出して Write をブロックした。実効。

### 実測で見つかった隙: 削除はゲート対象外

`guard-gated-write.sh` の対象は**書き込みリダイレクト（`>` / `>>`）と tee のみ**（`:9-12` に脅威モデルとして明記）。したがって `rm docs/knowledge/x.md` は素通りする（`permissions` の `rm -r*` / `rm -rf *` にも当たらない）。片付けの `rm -f` で実際に素通りした。

意図的な線引きではあるが、「これらは承認制のパス」という表現からは削除も含むと読める。`docs/knowledge/claude-code-config.md` に「ゲートの対象は書き込みのみ・削除は非対象」を明記する（→ タスク 2 に追加）。

**この結果が出るまで、機械防御を前提にした記述を増やさない。** → 結果が出たので解除。

## そのほかの DEFERRED 指摘（一次情報は前タスクの review-result.md）

- `validate_skills.py`: `--help` 以外の未知フラグで Traceback（`--protability` の打ち間違い等）
- `check_export_stopcontract.py`: `--verbose` が docstring の説明と一致しない / 報告の `[:120]` 切り詰めで差分の実体が見えない / 非同梱スキル名の除去が語境界を見ない / `read_body()` の戻り値注釈が実体と不一致 / `.test.tsx`・`.spec.tsx` が `STACK_WORDS` に無い / `--master` 不在時のエラー文言が export 用のまま
- 配布物 `settings.example.json` に `docs/decisions/` の ask が無い
- `~/.claude/CLAUDE.md`（global）と `.claude/skills/**` が ask の射程外
- ゲートの対象は書き込みのみで削除は非対象、を `claude-code-config.md` に明記する（20260726 の実測で追加）
- `remind-config-docs.sh` の**効果**（注入された内容を実際に守るか）を観察する。効かなければ外す
  - 20260726: **発火することは確認済み**（上の実測表）。ただし「注入された内容を実際に守るか」は発火とは別の問いで、設定・hook を触る実作業を通してしか観察できない。このタスクのタスク 2（権限の射程）が実際の観察機会になる

## 完了条件

- [x] hook / ask の実効性が確認され、結果に応じて記述または実装が訂正されている
  - 20260726 実測で全経路の発火を確認（上の実測表）。「効いていない」への訂正は不要だった。代わりに「削除は非対象」の追記がタスク 2 に発生
- [x] DEFERRED 指摘の各件が「対応済み」か「意図的に見送り（理由つき）」に確定している
  - 対応済み: Medium 4（`validate_skills.py` の Traceback・`--verbose` の仕様不一致・`[:120]` 切り詰め・hook/ask の実効性確認）/ Low 4（語境界・型注釈・`.test.tsx`・`--master` 文言）/ Info 2（`settings.example.json` の `docs/decisions`・global CLAUDE.md）
  - 意図的に見送り: **`.claude/skills/**` を ask に含めない**（master はスキル本文の編集が主活動で摩擦が大きい。export も今回は入れず、「配置先で直接編集しない」の機械化として別途判断する）／**`rm` はゲート対象外のまま**（脅威モデルが敵対者ではないため。限界を `claude-code-config.md` と配布物 `MANIFEST` に明記して閉じた）
  - **レビュー時点で未記録だった 1 件を追加検出**: 配布物 `settings.example.json` に `guard-gated-write.sh` の登録が無く、master が High として塞いだ Bash 迂回路が export 側では開いたままだった。同梱・登録して解消
- [x] `validate_skills.py` 全 PASS・`--portability` 混入 0 件（29/29 PASS・混入なし）
