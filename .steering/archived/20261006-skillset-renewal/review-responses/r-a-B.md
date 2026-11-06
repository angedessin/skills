<!-- results-review-b-ra.json / r-a-hardening / with / 3.92 USD / 400s -->

レビューが終わりました。前回は自己レビューで代わりにしていましたが、今回はフレッシュエージェント3体（impl / correctness / security）が最後まで走りました。Medium 以上の問題は **11件（High 5 / Medium 6）** です。結果は `.steering/20260725-skillset-hardening/review-result.md` に書き、Status は `OPEN` のままにしています。

> **design 同期を先にやってください。** impl の Axis 1 に、APPROVED の design.md と実装が食い違う High が3件あります。OPEN のままマージする前提にしないでください。

## High（5件）

| # | 問題 | 場所 | 再現 |
|---|---|---|---|
| 1 | 課金を承認するときの見積が実費の半分になる（`× 2 回` のままで、`--runs 4` が反映されていない）。design.md:133 の修正が入っていない | `skill-test/SKILL.md:36,39` | ✅ 確認 |
| 2 | 停止契約の比較が、停止語彙を含む行しか見ていない。design-doc と adr の「止まって待つ」の文を消しても「差分なし」で exit 0 になる | `check_export_stopcontract.py:39-51,94-100` | ✅ 確認 |
| 3 | 比較が0件でも「master と実質同一」と出て exit 0 になる（偽グリーン） | `check_export_stopcontract.py:230-276` | ✅ 確認 |
| 4 | allow にある `git diff*` / `git log*` / `git show*` に `--output=` を付けると、確認なしで書き込める。今回足した ask はこれで素通りになる | `settings.json:7-9` | git の機能としては確認。確認プロンプトが出ずに通るかは未確認 |
| 5 | `git diff*` は前方一致なので `git difftool -x <cmd>` にもマッチし、任意のコマンドを実行できる | `settings.json:7` | 同上 |

4・5 は既存の allow の問題ですが、今回の差分で入れた機械的な防御を無効にするので High にしています。

## Medium（6件）

- **design.md と実装の食い違い（実装側の Axis 1）**
  - design.md に無い変更（ask の追加、ターン境界、Step の再構成）を入れたのに、design.md を先に更新していません。
  - 「既知差分として登録する」と決めましたが、スクリプトに登録の仕組みがありません。
- **配布手順**: `docs/starter-kit.md:88-89` に `docs/decisions/` の ask と3形式での列挙がありません。
- **ドリフト検査の偽グリーン**: `check_deploy_drift.py` は SKILL.md が無いスキル（SKIP）を「ドリフトなし」と数えます。✅ 再現しました。
- **ask の効き方（推論）**
  - ask が効くのは Edit/Write だけで、Bash からの書き込みには効きません。
  - パスの `./` がカレントディレクトリ基準で解釈されるなら、サブディレクトリから起動したときに効きません（未確認）。

ほかに Low が15件、Info が9件あります（同じ指摘の統合9件、誤検知0件）。

## その他

- **未追跡ファイル**: ルートの `gitshow-write-test.txt` と `gitdiff-write-test.txt` は、`--output` での書き込みを試した残骸のようです。どこにも記録が無く、`git add -A` するとコミットに混ざります。消すか記録するか決めてください。こちらでは触っていません。
- **レビューできなかったもの**
  - test / perf / a11y / ui は対象ファイルが無いので回していません。
  - export worktree は sandbox で読み取りが禁止されていてレビューできていません。
  - `pnpm audit` はネットワークが遮断されていて実行できていません。
- **sandbox で動かなかったもの**: 素の `git` と `python3` は xcrun のキャッシュを書けずに失敗します。代わりに `/usr/local/bin/git` と `/usr/bin/python3` を使いました。
- **後片付け**: `.codify-needed` を作り、レビュー用に `.tmp/` に置いた一時パッチは消しました。

## 次のステップ
- [ ] design 同期（`design-doc` で方針を転換するか、APPROVED を追認する）
- [ ] 指摘を修正する（High 1〜3 はスクリプトと SKILL.md の修正で済みます。4・5 は allow を `Bash(git diff)` と `Bash(git diff *)` の列挙に変え、deny に `--output` / `difftool` を足す方針がよいと思います）
- [ ] 人が確かめる：新しいセッションで `git log --output=…` が確認プロンプトなしで通るか、ask が実際に出るか
- [ ] 修正後に、指摘があった軸だけ再レビューする
- [ ] knowledge-capture → PR → compound（`.codify-needed` あり）→ steering archive

修正に入るなら、どこから手を付けるか指示してください。
