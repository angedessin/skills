<!-- results-review-c-rb.json / r-b-deploy-integrity / with / 3.55 USD / 1300s -->

レビューの結果、確かめられた指摘は 8 件でした。一番重いのは 1 件目です。今の作業ツリーのように export worktree が無い環境では、追加した assets モードが契約違反を一度も差し戻しません。

8 件とも、作業ツリーを `$TMPDIR` にコピーして再現しています（8 件目だけはコードを読んで確かめました）。行番号は実ファイルのものです。

## High

**1. (f) の「対象不在 exit 2」が (a)〜(e) の違反を隠し、hook が素通しする**
- 場所: `scripts/check_asset_consistency.py:76-78`（`die()` → `sys.exit(2)`）、`:341-355`、`.claude/hooks/validate-skill-edit.sh:53-54`
- (f) は最後に走ります。export worktree が無い環境や、`git` が失敗する環境（`:107-113` は失敗すると `[]` を返す）では、(f) が `die()` します。このとき先に FAIL が出ていても exit 1 まで届きません。hook は rc が 1 以外なら素通しにします。
- 再現:
  - 未分類の `.claude/hooks/x.sh` を追加: FAIL (b)(c) が出るのに checker は rc=2、hook は rc=0
  - `HOOK_REGISTRATIONS` のキーを書き換え: FAIL (a) が出るのに同じく rc=2 / rc=0
- 次の記述とも食い違っています: docstring `:43`、README.md:216、design.md:202 の「違反は exit 1」
- 直し方の方向: (f) の対象不在は SKIP 扱いにし、FAIL が 1 件でもあれば exit 1 を優先する

## Medium

**2. (f) が FAIL の間は、関係ない assets 編集もすべて差し戻される**
- 場所: `check_asset_consistency.py:274-312`、hook `:45-61`
- 再現: master の `guard-env-read.sh` に 1 行足し、README に空行を足すと rc=2 で差し戻されました。
- design.md:97 の手順は「main で直す → export へ merge」です。この手順どおりに進めると、merge するまで README・starter-kit・deploy_skills.py の編集がすべて止まります。
- 差し戻しの文言は、export を直接直す方向に読めます（ここは推定です）。
- 直し方の方向: hook からは (f) を警告にとどめる。または、編集したファイルに関係する契約だけで差し戻す

**3. (f) の「意図的な除外か要確認」の注記が、既定の出力に出ない**
- 場所: `check_asset_consistency.py:315, 348-350`
- この注記は、PASS のときは `--verbose` を付けないと出ません。hook も `validate:assets` も `--verbose` を付けていません。
- decisions.md:38 は、FAIL を下げる代わりに「注記として毎回目に入る」ことを前提にしています。この前提が成り立っていません。

## Low

**4. hook のパス判定がそろっていない**
- 場所: hook `:38-41`
- README などは `$PROJECT_ROOT/...` との厳密一致なので、`/tmp` と `/private/tmp` の違いや、末尾の `/` で判定から漏れます。
- 逆に hooks は `*/.claude/hooks/*.sh` なので、別リポジトリやサブディレクトリのファイルでも差し戻します。
- design.md:218 は `*/README.md` のまま更新されていません。

**5. `.claude/settings.json` を編集しても assets モードが起動しない**
- 場所: hook `:35-43`
- 分類していない deny を足すと、checker は FAIL (e) を出します。それでも hook は rc=0 です。

**6. 例外の扱い**
- 場所: `check_asset_consistency.py:69-71` と `:243`
- `MASTER_ONLY_HOOKS` を消すと ImportError で exit 2 になり、素通しします。
- SyntaxError や JSON の破損では、Traceback が「契約違反」の見出しで差し戻されます。

**7. hook が PASS 行とサマリまで AI に返している**
- 場所: hook `:55-59`
- `docs/knowledge/claude-code-config.md:139` の「診断行だけを返す」に反しています。

**8. README.md:219 の説明が古い**
- 「SKILL.md 編集時の `validate_skills.py` 自動実行」のままで、assets モードのことが書かれていません。

## その他
- **捨てた指摘:** 0 件です。5 件目は、根拠として挙がった「README の主張」が誤りでした。実際にその主張があるのは hook のコメント `:12-13` です。
- **環境の制約:** 素の `git` は sandbox 内で xcrun が失敗するため、`/usr/local/bin/git` を使いました。PATH 先頭にある anaconda の `python3` と `jq` もこの sandbox では動かないので、再現はコピーした作業ツリーで CLT の python3 と `/usr/bin/jq` に差し替えて行いました。
- **判断できなかったこと:** `docs/starter-kit.md` への書き込みが事前に承認されたものか（CLAUDE.md の規則）は、差分からは分かりませんでした。

同じ内容を `.steering/20260726-deploy-integrity/review-result.md` に書きました。コードは直していません。どれから直すか決めてください。
