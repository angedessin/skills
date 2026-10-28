---
type: llm
focus: { source: file, path: src/features/products/ProductSearch.tsx }
---

A decision made after the design changed the default sort to 'おすすめ順' (the order the API returned). PASS if this component offers 'おすすめ順' and uses it as the default sort and as the value restored after a new search. FAIL if the default is '安い順' or 'おすすめ順' is missing.
