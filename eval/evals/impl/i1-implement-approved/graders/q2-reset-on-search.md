---
type: llm
focus: { source: file, path: src/features/products/ProductSearch.tsx }
---

PASS if running a new search resets the selected category to 'すべて' (for example the submit handler sets the category state back). FAIL otherwise.
