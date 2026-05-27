# Testing Patterns — フロントエンド開発での実践知識

このファイルは `knowledge-capture` スキルが蓄積する実践知識の格納場所。
CLAUDE.md から `@docs/knowledge/testing-patterns.md` で参照される。

---

## MSW vs vi.mock

ネットワーク呼び出しをするモジュールは `vi.mock` でモックしない。HTTP 境界のみ MSW でモックする。

```typescript
// ✅ Good: MSW で HTTP 境界のみモック
server.use(http.get('/api/user', () => HttpResponse.json({ id: 1 })))

// ❌ Bad: vi.mock で API モジュールをモック（HTTP 契約が破れても気づかない）
vi.mock('../api/user', () => ({ getUser: vi.fn().mockResolvedValue({ id: 1 }) }))
```

**例外**: DB・ファイルシステム・外部 SDK（HTTP を使わない I/O）は vi.mock で OK。

---

## RTL クエリ優先順位

`getByRole > getByLabelText > getByText > getByTestId`

```typescript
// ✅ Good
screen.getByRole('button', { name: /sign in/i })
screen.getByLabelText('Email')

// ❌ Bad
screen.getByTestId('submit-btn')
container.querySelector('.btn-primary')
```

---

※ このファイルは開発が進むにつれ knowledge-capture スキルによって更新される。
