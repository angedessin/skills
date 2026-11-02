---
type: llm
focus: { source: file, path: src/features/products/ProductSearch.tsx }
---

PASS if, when the filtered result is empty, the component shows '該当する商品はありません'. FAIL if an empty filtered result would show nothing or an empty list.
