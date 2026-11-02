---
type: llm
focus: { source: file, path: src/features/products/searchFilters.ts }
---

PASS if this module sorts by price ascending and descending, orders products with the same price by id ascending, keeps the API order for a 'recommended' (おすすめ順) option, and does not mutate the input array. FAIL if any of these is missing.
