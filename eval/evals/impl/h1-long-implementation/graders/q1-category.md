---
type: llm
focus: { source: file, path: src/features/products/searchFilters.ts }
---

PASS if this module has a function that builds the category list from products (unique, in order of appearance) and a function that filters by category where 'すべて' (or an equivalent all value) keeps every product. FAIL otherwise.
