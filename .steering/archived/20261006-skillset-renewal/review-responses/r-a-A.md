<!-- results-review-b-ra.json / r-a-hardening / without / 0.61 USD / 138s -->

未コミットの変更全体をレビューして、指摘は 10 件ありました。重要度の高い順に並べています。私の側では修正もテスト実行もしていません。

### 先に直すべきもの

1. **`scripts/check_export_stopcontract.py:191`: 古い master と比べて「問題なし」と出ることがある**
   `--master` の既定は、スクリプトがあるチェックアウトの `.claude/skills` です。skill-test の手順どおり export worktree の `scripts/` から実行すると、比較対象が export ブランチに残った古い master のコピーになります。その結果、main 側の新しい停止条件（debug や adr の「このターンでは Step 6 に進まない」など）が見えず、「実質同一」と判定されます。fail-closed で防ぎたかった誤判定そのものです。
   対策：master の場所を明示的に必須にするか、実際の master を指しているかを検証する。

2. **`scripts/check_export_stopcontract.py:108`: スキル名を部分一致で消している**
   `s.replace(n, "")` は単語全体ではなく文字列の一部も消します。`adr` や `debug` のような短い名前だと、`debug-x` や `docs/decisions/adr...` の一部まで消えます。停止先が変わった差分も「無害」と判定されてしまいます。
   対策：単語境界を付けた正規表現で置き換える。

3. **`scripts/check_export_stopcontract.py:88`: 改行コードが CRLF だと frontmatter を取り除けない**
   正規表現 `^---\n` は LF の改行しか想定していません。CRLF で保存された export 側の SKILL.md では frontmatter が本文として残り、`modified:` 行の停止語が実質的な差分として報告されます。
   対策：`\r?\n` にするか、読み込み時に改行を正規化する。

4. **`.claude/skills/rule-audit/SKILL.md:41`（56 行目も同じ）: 片方だけ更新されている**
   移動や置換の手順では knowledge ファイルを素のパスで参照するようになりました。一方、監査の入力は今も CLAUDE.md の `@参照` しか見ていません。このため skill-design-patterns.md などが孤立ファイル扱いになったり、素のパスで書いた参照のリンク切れを見落としたりします。

5. **`docs/starter-kit.md:88`: 配置手順の ask に `docs/decisions/**` が抜けている**
   settings.json と README には入っています。この手順どおりに adr スキルを配置すると、`docs/decisions/` への書き込みを止める仕組みがなくなります。

### CLI の堅牢性

6. **`scripts/validate_skills.py:190`**：`--help` は先頭の引数のときしか認識されません。`--portability --help` や `-v` を渡すと `Path(arg).iterdir()` で例外になり、トレースバックで落ちます。`-` で始まる未知の引数は、パスとして扱う前にまとめて拒否してください。
7. **`scripts/check_deploy_drift.py:235`**：`if args.target:` では空文字が「引数なし」と同じ扱いになります。`$DEPLOY` が未設定のまま実行すると、全配置先をチェックするモードに切り替わります。`is not None` で判定し、空文字は明示的にエラーにするのがよいです。
8. **`scripts/check_deploy_drift.py:215`**：argparse に移行した際、`--help` から詳しい使い方の説明（`__doc__`）が消えました。`description=__doc__` と `RawDescriptionHelpFormatter` を使えば元に戻せます。

### 細かいもの

9. **`scripts/check_export_stopcontract.py:81`**：`read_body` の戻り値の型注釈が `list[str]` ですが、実際は `list[tuple[int, str]]` を返しています。212 行目には中身のない f-string もあります。
10. **`gitdiff-write-test.txt` と `gitshow-write-test.txt`**：作業用のファイルが未追跡のままリポジトリ直下に残っています。grep の結果に混ざりますし、`git add .` でコミットされるおそれがあります。

必要なら直します。1〜3 と 6〜10 はスクリプトの修正とファイルの削除なので、すぐ対応できます。4 と 5 は `.claude/` と `docs/` への書き込みになるので、CLAUDE.md の規約に従い、承認をもらってから手を入れます。
