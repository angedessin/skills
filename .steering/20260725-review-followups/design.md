# 設計: レビュー積み残しの解消

Status: **DRAFT — awaiting review**
Date: 20260725

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

**この結果が出るまで、機械防御を前提にした記述を増やさない。**

## そのほかの DEFERRED 指摘（一次情報は前タスクの review-result.md）

- `validate_skills.py`: `--help` 以外の未知フラグで Traceback（`--protability` の打ち間違い等）
- `check_export_stopcontract.py`: `--verbose` が docstring の説明と一致しない / 報告の `[:120]` 切り詰めで差分の実体が見えない / 非同梱スキル名の除去が語境界を見ない / `read_body()` の戻り値注釈が実体と不一致 / `.test.tsx`・`.spec.tsx` が `STACK_WORDS` に無い / `--master` 不在時のエラー文言が export 用のまま
- 配布物 `settings.example.json` に `docs/decisions/` の ask が無い
- `~/.claude/CLAUDE.md`（global）と `.claude/skills/**` が ask の射程外
- `remind-config-docs.sh` の**効果**（注入された内容を実際に守るか）を観察する。効かなければ外す

## 完了条件

- [ ] hook / ask の実効性が確認され、結果に応じて記述または実装が訂正されている
- [ ] DEFERRED 指摘の各件が「対応済み」か「意図的に見送り（理由つき）」に確定している
- [ ] `validate_skills.py` 全 PASS・`--portability` 混入 0 件
