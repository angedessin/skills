# Design: consistency-audit-fixes

Created: 20260703
Status: **APPROVED**
Approved: 20260703

> 設計素材: 2026-07-03 の悲観監査（会話内）で検出した 13 所見。grep による機械的裏取り済み

## Goal

悲観監査で検出した「片側だけ直した」系の反映漏れ・矛盾を一括修正する。主犯は 3 系統 — (a) 6 月の Next.js 除去の取りこぼし（review-security / impl-review）、(b) オーケストレーターだけに入った diff 合算修正がサブスキルに未還元（単独利用で silent failure）、(c) 重要度の採点契約が呼び出し側にしか無い。放置すると配置先での誤指摘・レビュー空振り・サマリー件数の恣意性として実害になる。

## Scope

### In scope（High 3 + Medium 5 + 安価な Low 3 = 11 所見）

**High:**
1. **review-security の Next.js 残骸除去** — Axis 3 の `NEXT_PUBLIC_` 例 4 箇所を「ビルドツールのクライアント公開プレフィックス（例: `VITE_` / `NEXT_PUBLIC_`）」に中立化。判断軸（シークレットのクライアントバンドル混入検知）は不変
2. **サブスキル 7 本の diff 取りこぼし修正** — スコープ節の `git diff --name-only HEAD` を「未コミット + ベースブランチからのコミット済みの合算」に置換（frontend-code-review Phase 1 と同じ考え方を各本文にインライン — 自己完結原則のため相互参照にしない）。対象: impl-review / test-review / review-{security,performance,a11y,correctness,ui}
3. **重要度尺度の契約化** — frontend-code-review のディスパッチテンプレートに尺度定義を明記（High = 実害・セキュリティ・データ破壊 / Medium = バグの温床・保守性の毀損 / Low = 軽微・様式 / Info = 情報）。サブスキル 7 本には手を入れない（単独利用時は件数集計しないため、契約はディスパッチ時にのみ発生 — 修正 1 箇所で閉じる）

**Medium:**
4. **impl-review Axis 4 の RSC 例中立化** — `'use server'`/`'use client'`/`app/` パス例を、フレームワーク非依存の React パターン（useEffect deps・過剰 state）中心に置換。SSR/RSC 観点は「プロジェクトが RSC を使う場合」の条件付き 1 行に縮退（論点1 の「SSR 観点は中立で残す」と整合）
5. **tdd の E2E 導線撤去** — 本文 L102 の「E2E=§e2e」を削除し「E2E は `e2e` スキル」に置換。references/patterns.md の §e2e 節冒頭に「E2E の作成・レビューは e2e スキルが担当」の委譲注記を追加（節自体は履歴として温存）
6. **CLAUDE.md セッション開始チェックの codify 対応** — find を `\( -name '.capture-needed' -o -name '.codify-needed' \) -not -path '*/archived/*'` に拡張し、`.codify-needed` があれば compound を促す手順を 1 行追加（steering spec.md の主張と整合させる）
7. **knowledge-capture 決定木の @追記を条件付きに** — L80 の「+ CLAUDE.md に @参照を追記」を「常時参照させたい知識のみ @、必要時に読む導線はプレーンパス（Step 5 の注意と同じ基準）」に修正
8. **feature-pipeline の記述追従** — Phase 2 に impl-from-design のモード選択スキップ分岐（Markdown 成果物）を反映、Phase 5 のセクション列挙に Deploy を追加

**Low（1 行修正で済むもののみ）:**
9. **knowledge-capture の再実行ガード** — Step 1 のフラグ確認に「`capture_done` が既にあれば、再実行の必要がない旨を伝えて確認する」を追加（feature-pipeline 判定表エッジ対策）
10. **debug の書き先曖昧性解消** — 「複数のアクティブタスクがある場合は調査対象と最も関連するタスクを選ぶ（判断できなければユーザーに確認）」を追記（impl-review Axis 1 と同じ規約）
11. **starter-kit の version 巻き戻し防止** — source-commit 記録例に「version はコピー元の値を保つ（例の "1.0" で上書きしない）」の注記

### Out of scope

- フラグの gitignore と複数マシン問題（所見 10）— 単一マシン運用では実害なし。複数マシン化したら再検討
- Playwright spec のフルモードレビュー空白（所見 13）— e2e 設計時に「実需が出たら e2e-agent 追加」と意思決定済みの既知の負債
- feature-pipeline 判定表の構造的再設計 — 所見 9 は knowledge-capture 側の 1 行ガードで実用上塞がる

## Constraints

- 判断軸は変えない（表現の中立化・契約の明文化・縮退の追加のみ）
- 修正したスキルは version を minor バンプ（判断・手順の変更があるもののみ。例示の中立化だけなら据え置き…とせず、単独利用の挙動が変わる 2 と 9 と 10、集計契約が変わる 3 相当のスキルはバンプ）
- 絵文字なし / validate 19/19 PASS を維持
- サブスキルの diff 合算はコマンドを各本文にインライン（オーケストレーターへの相互参照にすると単体コピー時に壊れる — 自己完結原則）

## Acceptance criteria

- [ ] `NEXT_PUBLIC_` / `'use server'` / `'use client'` / `app/` パス例が全スキル本文から消えている（grep ゼロ。中立表現での言及は可）
- [ ] サブスキル 7 本のスコープがコミット済み変更を含む合算 diff になっている（単独利用の silent failure 解消）
- [ ] frontend-code-review のディスパッチテンプレートに重要度尺度（High/Medium/Low/Info の基準）が定義されている
- [ ] tdd 本文から自前 §e2e への導線が消え、patterns.md §e2e に委譲注記がある
- [ ] CLAUDE.md のセッション開始手順が capture/codify 両フラグに対応し、spec.md の主張と一致している
- [ ] knowledge-capture: 決定木の @追記が条件付き・capture_done の再実行ガードがある
- [ ] feature-pipeline: モード選択スキップ分岐と Deploy セクションが記述に反映されている
- [ ] validate 19/19 PASS・アストラル面絵文字なし

## Approach

全 11 修正は「判断軸の変更なし・表現と契約の整合」なので、監査時の grep 結果を正として該当行をピンポイント修正する。diff 合算（2）は 7 ファイルに同一の 3 行パターンをインライン展開する — 共通化（オーケストレーター参照）は単体コピー時の自己完結を壊すため意図的に重複させる（エンジン＋カートリッジ契約の「本文はドリフトゼロ」は再コピーで担保）。重要度尺度（3）はサブスキルでなくディスパッチテンプレート側に置く — 契約が発生するのはオーケストレーション時のみで、修正 1 箇所で 7 エージェント全てに効く。

## Key components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| review-security 改訂 | `.claude/skills/review-security/SKILL.md` | Axis 3 中立化 + スコープ合算（1, 2）。version 1.1 |
| サブスキル 6 本のスコープ改訂 | impl-review / test-review / review-{performance,a11y,correctness,ui} | スコープ合算（2）。各 version バンプ |
| impl-review Axis 4 改訂 | `.claude/skills/impl-review/SKILL.md` | RSC 例中立化（4。2 と同時に version 1.1） |
| frontend-code-review 改訂 | `.claude/skills/frontend-code-review/SKILL.md` | ディスパッチテンプレートに重要度尺度（3）。version 1.1 |
| tdd 改訂 | `.claude/skills/tdd/SKILL.md` + `references/patterns.md` | E2E 導線撤去 + 委譲注記（5）。version 1.1 |
| CLAUDE.md | `CLAUDE.md` | codify フラグ対応（6） |
| knowledge-capture 改訂 | `.claude/skills/knowledge-capture/SKILL.md` | 決定木条件付き @ + 再実行ガード（7, 9）。version 1.2 |
| feature-pipeline 改訂 | `.claude/skills/feature-pipeline/SKILL.md` | Phase 2/5 の記述追従（8）。version 1.1 |
| debug 改訂 | `.claude/skills/debug/SKILL.md` | 書き先の判定基準（10）。version 1.1 |
| starter-kit.md | `docs/starter-kit.md` | version 巻き戻し防止の注記（11） |

## Data flow

修正のみ（新しいフローなし）。単独利用時のサブスキルのスコープ決定だけ変わる:

```
旧: git diff --name-only HEAD（未コミットのみ — コミット済みを取りこぼす）
新: 未コミット（HEAD との diff）+ コミット済み（ベースブランチとの merge-base からの diff）を合算
    合算が空 → レビューしたい範囲をユーザーに確認（silent failure の禁止）
```

## Test strategy

- 構造検証: `scripts/validate_skills.py` 19/19 PASS + アストラル面チェック
- 残骸ゼロ確認: 監査時と同じ grep（NEXT_PUBLIC / use client / use server / §e2e 導線 / HEAD-only スコープ）が全てゼロ or 意図した中立表現のみになることを機械確認
- 挙動検証: empirical は実施しない（確立済み方針）。配置先での実利用が実地検証

## Open questions

すべて 20260703 の承認時に推奨案で確定（Next.js 語彙の扱いは「固有名の例を消して判断軸は中立表現・条件付きで残す」ことをユーザーと確認済み）:

- [x] **重要度尺度の置き場**: ディスパッチテンプレート（オーケストレーター側 1 箇所）で確定
- [x] **diff 合算の意図的重複**: 7 ファイルへのインライン展開で確定（合算ロジック変更時は 8 箇所同時修正のトレードオフを受け入れ）
- [x] **impl-review の SSR/RSC**: 条件付き 1 行への縮退で確定（RSC を使うプロジェクトでは判断軸が生き、具体例は配置先カートリッジで足す）

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| diff 合算をオーケストレーター参照で共通化 | 単体コピー時に frontend-code-review が無いと壊れる（自己完結原則違反）。重複はマスター再コピーで同期される設計 |
| 重要度尺度をサブスキル 7 本の出力形式に追加 | 単独利用では集計が発生せず、7 ファイルの保守点だけ増える。契約はディスパッチ時にのみ生じる |
| tdd references の §e2e 節を削除 | カートリッジは配置先所有の層。マスター example から節を消すより委譲注記で導線だけ塞ぐ方が低リスク |
| Low 所見も含め全 13 件を修正 | 所見 10（マルチマシン）は環境前提が変わるまで不要、所見 13 は意思決定済みの負債。スコープ肥大を避ける |
