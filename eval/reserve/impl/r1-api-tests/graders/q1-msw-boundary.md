---
type: llm
focus: { source: file, path: src/api/products.test.ts }
---

PASS if the tests mock at the HTTP boundary using MSW (server.use with http handlers) rather than mocking fetch or internal modules. FAIL otherwise.
