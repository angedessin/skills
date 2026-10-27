---
type: llm
focus: { source: file, path: e2e/search.spec.ts }
---

The app's /api/products endpoint only exists in unit tests (MSW runs in Node), not in the dev server. PASS if this spec provides the API responses itself (for example with page.route) or states in a comment that it assumes a backend serving /api/products. FAIL if it silently assumes the API exists.
