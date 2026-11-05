  「商品一覧に並び替えを足したい。まず設計して」

⏺ Skill(design-doc)
Successfully loaded skill

  Ran 2 shell commands

中規模の作業として1セッションで完了できると見積もり、設計を書く前に、コードの骨格を左右する決定について一つずつ確認します。

⏺ User answered Claude's questions:
· 商品一覧の並び替えは、どこで行いますか？（今の /api/products は q だけを受け取り、ページングなしで一致した全件を返します。リポジトリにある実装は MSW のモックだけで、実 API の有無や仕様はコードからは分かりません） → 画面側で並び替え (Recommended)

⏺ User answered Claude's questions:
· 商品一覧の並び替えの基準は、どこまで用意しますか？（並び替えは画面側で行うと決まりました。Product 型にあるのは id・name・category・price だけで、新着順や人気順に使えるデータはありません） → おすすめ順＋価格の昇降 (Recommended)

設計: 商品一覧の並び替え

目的: 検索結果を価格順に並べ替えて、商品を比べやすくします。

対象 / 対象外
- 対象: 検索結果を「標準」「価格の安い順」「価格の高い順」で並び替える機能
- 対象外:
  - API の変更
  - 商品名順、新着順、人気順
  - URL や保存への並び順の記録（今はキーワードも URL に持っていないため）
  - 既存の問題である、連続検索時に古い応答で上書きされる可能性への対応

振る舞い

┌──────────────────────────────────┬──────────────────────────────────────────────────────────┐
│               場面               │                           動き                           │
├──────────────────────────────────┼──────────────────────────────────────────────────────────┤
│ 初期値                           │ 「標準」（API が返した順）                               │
├──────────────────────────────────┼──────────────────────────────────────────────────────────┤
│ 並び順の変更                     │ 再取得せず、すぐに表示へ反映する                         │
├──────────────────────────────────┼──────────────────────────────────────────────────────────┤
│ 同じ価格の商品                   │ API が返した順のまま                                     │
├──────────────────────────────────┼──────────────────────────────────────────────────────────┤
│ 素早い連続操作                   │ 同期処理で通信もないため、競合は起きない                 │
├──────────────────────────────────┼──────────────────────────────────────────────────────────┤
│ 検索前・読み込み中・0 件・エラー │ セレクトを出さない。出ない間も選択は覚えておく           │
├──────────────────────────────────┼──────────────────────────────────────────────────────────┤
│ 再検索                           │ 選んだ並び順を保ったまま、新しい結果に適用する（論点 1） │
└──────────────────────────────────┴──────────────────────────────────────────────────────────┘

構成

- 変更するファイル: src/features/products/ProductSearch.tsx とそのテストの 2 つです。API、型、モックは変えません。
- 増える状態: ProductSearch に sort: "default" | "price-asc" | "price-desc" を useState で持ちます。
- 並び替えの処理: 描画時に [...products].sort(...) で導出し、取得結果の配列は書き換えません。
- UI: ラベル「並び替え」付きの <select> を、検索フォームの外、結果一覧の直前に置きます。

完了条件

- 全件検索の結果で、3 つの並び順それぞれの表示順がテストで確かめられる
- 並び順を変えても /api/products へのリクエストが増えない
- 同じ価格の商品が API の返した順を保つ
- 再検索しても選んだ並び順が保たれる
- 検索前、0 件、エラーのときはセレクトが出ない
- 既存の 3 テスト、test、typecheck が通る

テスト方針

- ProductSearch.test.tsx に上の条件のテストを足します。既存テストは変更しない見込みです。
- 順序の確認にはキーワードなしの全 6 件を使います。「モニター」の 2 件だと標準と高い順が同じ並びになり、違いを確かめられないためです。
- 同じ価格のケースだけ server.use で応答を差し替え、共通のハンドラは変えません。

前提

- 実 API: 一致した全件を返すものとして設計しています。リポジトリにはモックしかなく、実 API の仕様は確認できていません。
- 動作確認: main.tsx はブラウザ用のモックを起動していないため、テストで確認します。
- ブランチ: ルールは develop から feature/* を切る運用ですが、現在は master にいます。実装を始めるときに develop の有無を確認します。

却下した案

- API 側で並び替え: 全件が手元にあるなら、API の変更や再取得、競合対策の手間に見合いません。
- 商品名順: 読み仮名のデータがなく、期待どおりの五十音順にならない場合があります。
- 新着順・人気順: 必要なデータがなく、API の拡張が前提になります。

決めてほしい論点

1. 再検索時の並び順: **保持（推奨）**か、「標準」に戻すかを選んでください。価格で比べている人は、キーワードを変えても同じ順で見たいはずです。
2. 既定の並び順の名前: **「標準」（推奨）**か「おすすめ順」かを選んでください。先ほどの質問では選択肢の名前を「おすすめ順」、説明を「標準」と書いてしまい、表記が揃っていませんでした。実際は API が返した順でおすすめの根拠がないため、「標準」を推奨します。

推奨どおりでよければ「OK」とだけ返してください。承認されたら実装に入ります。

✻ Sautéed for 1m 6s · done 23:13

❯ ok

決めたことの要約です（コミットか PR の本文に写します）。

- 並び替えは画面側で行い、API、型、モックは変えない
- 並び順は「標準」（API が返した順）、「価格の安い順」、「価格の高い順」の 3 つで、同じ価格なら API の順を保つ
- 状態は ProductSearch の useState に持ち、表示順は描画時に導出する
- セレクトは結果が 1 件以上のときだけ、フォームの外に出す
- 再検索しても選んだ並び順を保つ

まずブランチを確認します。

  Ran 1 shell command

develop がまだないので、今の master から作り、そこから feature/product-sort を切ります。どちらもローカルだけの操作です。

  Read 2 files, ran 1 shell command

先にテストを書いて、実装前に失敗することを確かめます。

⏺ Bash(cat > /private/tmp/claude-501/-Users-kentaro-Desktop--lab-ai-skills-try/53fbb7f9-1fe7-4400-885b-719bf196790a/scratchpad/patch_test.py <<'EOF'
      import sys…)
       × 0 件の検索を挟んでも選んだ並び順を保つ 30ms
       × 価格の安い順・高い順に並び替え、標準に戻せる 50ms
       × 再検索しても選んだ並び順を保つ 32ms
… +12 lines
Updated src/features/products/ProductSearch.test.tsx (+128 -1)
import { render, screen } from "@testing-library/react";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { products } from "../../mocks/data";
import { server } from "../../mocks/server";
import { ProductSearch } from "./ProductSearch";

async function shownNames() {
  const list = await screen.findByRole("list", { name: "検索結果" });
  return within(list)
    .getAllByRole("listitem")
    .map((item) => item.textContent?.split("（")[0]);
}

describe("ProductSearch", () => {
  it("キーワードに一致する商品を表示する", async () => {
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "検索" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("検索に失敗しました");
    expect(screen.queryByLabelText("並び替え")).not.toBeInTheDocument();
  });

  describe("並び替え", () => {
    const apiOrder = [
      "ワイヤレスマウス",
      "メカニカルキーボード",
      "USB-C ハブ",
      "27インチモニター",
      "モニターアーム",
      "ノイズキャンセリングヘッドホン",
    ];
    const cheapestFirst = [
      "ワイヤレスマウス",
      "USB-C ハブ",
      "モニターアーム",
      "メカニカルキーボード",
      "ノイズキャンセリングヘッドホン",
      "27インチモニター",
… 102 more lines
(files that changed while this command ran, by the command or by another process; a convenience view, not a review or audit of the command)
(timeout 3m)

想定どおり、新しいテストのうち 6 件が失敗しました。残る 1 件はセレクトが出ないことの確認なので、実装前でも通ります。次に実装します。

⏺ Update(src/features/products/ProductSearch.tsx)
Added 9 lines
  | { status: "success"; products: Product[] }
  | { status: "error" };

type SortKey = "default" | "price-asc" | "price-desc";

function sortProducts(products: Product[], sort: SortKey): Product[] {
  if (sort === "default") return products;
  const direction = sort === "price-asc" ? 1 : -1;
  return [...products].sort((a, b) => direction * (a.price - b.price));
}

export function ProductSearch() {
  const [query, setQuery] = useState("");
  const [state, setState] = useState<State>({ status: "idle" });
  const [sort, setSort] = useState<SortKey>("default");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

⏺ Update(src/features/products/ProductSearch.tsx)
Added 15 lines, removed 7 lines
      {state.status === "error" && <p role="alert">検索に失敗しました</p>}
      {state.status === "success" && state.products.length === 0 && <p>該当する商品はありません</p>}
      {state.status === "success" && state.products.length > 0 && (
        <ul aria-label="検索結果">
          {state.products.map((p) => (
            <li key={p.id}>
              {p.name}（{p.category}）¥{p.price.toLocaleString()}
            </li>
          ))}
        </ul>
        <>
          <label htmlFor="sort">並び替え</label>
          <select id="sort" value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
            <option value="default">標準</option>
            <option value="price-asc">価格の安い順</option>
            <option value="price-desc">価格の高い順</option>
          </select>
          <ul aria-label="検索結果">
            {sortProducts(state.products, sort).map((p) => (
              <li key={p.id}>
                {p.name}（{p.category}）¥{p.price.toLocaleString()}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );

⏺ Bash(mise exec -- pnpm test 2>&1 | tail -25; echo "=== typecheck"; mise exec -- pnpm typecheck 2>&1 | tail -15; echo "exit=$?"; echo "=== status"; git status --short…)
> skills-eval-app@ test /Users/kentaro/Desktop/_lab/ai/skills-try
> vitest run
… +24 lines
1 file changed (binary, mode only or too large to show)
(timeout 3m)

商品一覧の並び替えを実装しました。テストは既存分と新規分を合わせて 10 件すべて通り、typecheck もエラーは出ていません。ブラウザでは確認しておらず、まだコミットもしていません。

変更内容

- src/features/products/ProductSearch.tsx: 「標準」「価格の安い順」「価格の高い順」を選ぶセレクトを追加しました。結果が 1 件以上のときだけ表示します。
- src/features/products/ProductSearch.test.tsx: 並び替えのテストを 7 件追加しました。実装前に実行し、実際の並び替えを確かめる 6 件が失敗することも確認済みです。

設計と違う点

既存のエラー表示のテストに、セレクトが出ないことの確認を 1 行足しました。設計では既存テストを変更しない見込みと書きましたが、完了条件の「エラー時はセレクトが出ない」を確かめるには、ここが最も自然だったためです。

確認しておいてほしいこと

- ブランチ: develop がなかったので master から作り、そこから切った feature/product-sort で作業しています。どちらもローカルだけで、未 push です。main もまだありません。
- tsconfig.tsbuildinfo: Git で追跡されていない生成物です。.gitignore に入っていないので、コミットには含めません。.gitignore に追加するかどうかは別途決めてください。
- .claude/ と CLAUDE.md: 未追跡のままで、今回の変更とは関係がないので、こちらも含めません。

コミットメッセージ案

ソースとテストの 2 ファイルだけをコミットする想定です。

feat: 商品検索の結果を価格で並び替えられるようにする

- 並び替えは画面側で行い、API・型・モックは変えない
- 並び順は標準（API が返した順）・価格の安い順・価格の高い順で、同じ価格なら API の順を保つ
- 状態は ProductSearch の useState に持ち、表示順は描画時に導出する
- セレクトは結果が 1 件以上のときだけ、フォームの外に出す
- 再検索しても選んだ並び順を保つ

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

この内容でコミットしてよければ教えてください。

✻ Brewed for 1m 13s · done 23:14

❯ コードをレビューして

⏺ Skill(frontend-code-review)
Successfully loaded skill

  Ran 1 shell command

対象は未コミットの2ファイルに絞り、設定ファイルや生成物は今回のレビューから外しました。担当ごとに一次レビューを並列で実行します。

⏺ 5 background agents launched (↓ to manage)
review-bug (バグ確認（差分のみ）)
review-bug (バグ確認（周辺コード込み）)
review-rules (規約確認)
review-ui-a11y (UI とアクセシビリティ確認)
review-test (テスト確認)

一次レビューの 5 体を起動しました。全員の結果が返ってから指摘をまとめ、検証役に渡します。今の時点で結果はまだ分かりません。

✻ Cooked for 32s · done 23:15

› Message from @review-rules (ctrl+o to expand)

規約担当の結果は指摘なしでした。残り 4 体の結果を待ちます。

⏺ Agent "規約確認" finished · 15s

⏺ Agent "UI とアクセシビリティ確認" finished · 15s

› Message from @review-ui-a11y (ctrl+o to expand)

UI とアクセシビリティ担当の結果も指摘なしでした。バグ担当 2 体とテスト担当の結果を待ちます。

✻ Baked for 1s · done 23:16

› Message from @review-bug (ctrl+o to expand)

差分だけを見たバグ担当も指摘なしでした。周辺コードも見るバグ担当とテスト担当の結果を待ちます。

⏺ Agent "バグ確認（差分のみ）" finished · 26s

› Message from @review-test (ctrl+o to expand)

テスト担当から指摘が 3 件届きました。判定はまだ先です。周辺コードも見るバグ担当の結果が揃ってから、まとめて検証役に渡します。

✻ Sautéed for 1s · done 23:16

⏺ Agent "テスト確認" finished · 41s

› Message from @review-bug (ctrl+o to expand)

一次レビューが全員分揃いました。指摘はテスト担当の 3 件だけで、重複はありません。検証役に 1 件ずつ確かめてもらいます。

⏺ review-verify(指摘の検証)
Backgrounded agent (↓ to manage · ctrl+o to expand)

⏺ Agent "バグ確認（周辺コード込み）" finished · 44s

検証役の結果を待っています。届いたら、確かめられた指摘だけを報告します。

✻ Crunched for 13s · done 23:16

› Message from @review-verify (ctrl+o to expand)

レビューの結果、確かめられた指摘は Medium が 1 件で、テストの穴です。実装のバグは見つからず、利用者に見える不具合もありません。

Medium

同額テストが、誤った並べ方を見逃す

- 場所: src/features/products/ProductSearch.test.tsx:113-131（データは 117-119 行、期待値は 127 行と 130 行）
- 問題: 同額の 2 件が、API の順でも名前順でも id 順でも同じ並びです。そのため、「API の順を保つ」と「名前や id で決めた順」を区別できません。
- どう壊れうるか: sortProducts の比較を次のように変えても、10 件すべて通ります。同じ価格で API の順を保つという仕様を破っても、気づけません。
  - direction * (a.price - b.price) || a.name.localeCompare(b.name)
  - direction * (a.price - b.price) || a.id.localeCompare(b.id)
- 影響の範囲: src/mocks/data.ts に同額の商品はないので、この仕様を確かめているのはこのテストだけです。今の実装（ProductSearch.tsx:15）は正しく動いています。
- 直し方: API の順を名前順・id 順と逆にします。
  - 1 件目を { id: "z", name: "同額Z", ... } に変える
  - 期待値を ["同額Z", "同額B", "高額"] と ["高額", "同額Z", "同額B"] にする
- 確かめ方: 再現しました。作業ツリーのコピーで、上の 2 つの誤実装は今のテストをすり抜け、修正後のデータでは同額テストが落ちます。正しい実装は修正後も 10 件すべて通ります。

捨てた指摘（2 件）

- 「再取得しない」のテストが、再取得を見逃す可能性: useEffect で再取得する誤実装を入れて計 813 回実行しましたが、一度もすり抜けず、問題ではないと判定されました。ただし、順序が仕様として保証されているとまでは示せていません。
- 0 件でセレクトが出ないことの検証の置き場所: 誤実装は検出でき、失敗位置もその行を直接指します。残るのはテストの分け方の好みなので、問題ではないと判定されました。

検証で別に分かったこと

- 指摘の対象外の隙間: 再取得を 300ms 遅らせる誤実装は、「再取得しない」のテストを 3 回とも通りました。検証のほうが先に終わるためです。かなり不自然な実装なので、私は今回直さなくてよいと考えます。
- node_modules のキャッシュ更新: 検証役のコピーが node_modules をシンボリックリンクで共有していたため、vitest のキャッシュが node_modules/.vitest-cache などに書き込まれました。誤実装の変換結果が含まれている可能性があります。Git には出ず、ソースの 2 ファイルも変わっていません。気になる場合は、このキャッシュを消せば作り直されます。

レビューの範囲

- 対象外: 未追跡の .claude/、CLAUDE.md、tsconfig.tsbuildinfo は今回の変更ではないので見ていません。
- 結果の保存: .steering/ がないので、review-result.md は作らず、この返答だけです。
- レビューできなかったもの: ありません。ただし、ブラウザでの動作確認はしていません。

コードは変更していません。指摘を直すかどうかを教えてください。直す場合は、同額テストのデータと期待値だけを変えます。

⏺ Agent "指摘の検証" finished · 6m 57s
