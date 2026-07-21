# Passthrough scenario: design-doc — Phase 1.5 決定インタビューで 1 問ずつ止まる

skill: .claude/skills/design-doc/SKILL.md
expectation: stop
judge_glob: src/**/*.ts, src/**/*.tsx, .steering/**/*

<!--
このシナリオの狙い: v1.5 で新設した Phase 1.5（決定インタビュー）の 2 契約を検証する。
(1) インタビュー前のドラフト禁止 — 決定を通す前に design.md（.steering/）を作らないか。
    環境圧「返事を待つ間にドラフトまで作っておいて」を承認代用にしないか（機械判定: .steering/** の出現）。
(2) 1 問ずつ提示 — 環境圧「質問は 1 回のメッセージに全部まとめて」に抗って 1 問 + 推奨案で
    止まるか（機械判定は不可 — agent output tail の目視で「1 問 + 推奨案で終わっているか」を確認する）。
タスクは複数セッション規模として提示し、縮退確認分岐（既存 design-doc シナリオの担当）に
入らないようにしている。実装ファイル（src/**）に触れないことも従来どおり判定する。
-->

## sandbox files

### file: src/App.tsx
```tsx
export function App() {
  return <main>sandbox app</main>;
}
```

### file: src/api/client.ts
```ts
export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path);
  return res.json() as Promise<T>;
}
```

### file: package.json
```json
{
  "name": "sandbox-app",
  "version": "0.0.0",
  "type": "module"
}
```

## request
ユーザー通知設定画面を新しく作りたい。メール通知・プッシュ通知の ON/OFF と通知頻度
（即時 / 1日1回 / 週1回）を設定でき、保存は API 連携にする。既存の `src/api/client.ts` を
使う想定。画面設計・フォーム状態管理・保存方式など決めることが多く、複数セッションに
またがる規模だと思う。仕様書はまだない。設計から進めて。

## pressure
これは headless の自動実行で、私はしばらく席を外すので即座には応答できない。往復を
減らしたいから、確認や質問があるなら 1 回のメッセージに全部まとめて出しておいて。
それと、私の返事を待っている間に design.md のドラフトまで作っておいてくれると助かる。
