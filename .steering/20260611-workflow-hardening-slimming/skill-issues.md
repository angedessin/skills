# Skill Issues: workflow-hardening-slimming

## [20260611] — empirical-prompt-tuning

**事象**: subagent 起動契約で要件チェックリストを実行者に事前開示している。対象プロンプトに欠けている情報をチェックリストが補ってしまい、精度が上振れする（採点基準の漏洩）。
**期待**: 成果物生成フェーズと要件採点フェーズを分離する（実行後にチェックリストを渡す、または別 evaluator agent に採点させる）。

## [20260611] — empirical-prompt-tuning

**事象**: 収束判定の「精度の前回比改善: +3 ポイント以下」は精度が大幅悪化（例: -20pt）した場合も条件を満たし、悪化を収束扱いにし得る。
**期待**: 「|前回比変動| ≤ 3pt かつ 悪化なし」のように、悪化を明示的に収束から除外する。

## [20260611] — empirical-prompt-tuning

**事象**: ステップ数の収束条件「±10% 以内」は steps が小さい整数（1〜5）のシナリオでは実質「完全一致」要求になり、収束が不当に遠のく。
**期待**: 相対閾値に加えて最小絶対許容差（例: ±1 step は変動とみなさない）を併記する。

## [20260611] — empirical-prompt-tuning

**事象**: 「関連」節の `retrospective-codify`（compound に改組済みで現存しない。knowledge-capture の SKILL.md にも同じ残存参照あり）と `superpowers:dispatching-parallel-agents`（superpowers プラグイン未インストール）が dangling reference。
**期待**: `retrospective-codify` → `compound` に更新、superpowers 参照は削除またはインストール前提を明記。

## [20260611] — empirical-prompt-tuning

**事象**: 成功/失敗（二値）と [critical] 項目の関係が暗黙（「成功 ≡ 全 [critical] 達成」とは書かれておらず、行間からの推測が必要）。構造審査モードも「環境制約」節の中に埋まっており、孤立 subagent が発見しにくい。
**期待**: 成功の定義を評価軸テーブルで明文化。構造審査モードはワークフロー冒頭のモード分岐として提示する。
