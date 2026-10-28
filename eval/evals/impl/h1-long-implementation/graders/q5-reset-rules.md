---
type: llm
focus: { source: file, path: src/features/products/ProductSearch.tsx }
---

PASS if running a new search resets the category to 'すべて' and the sort to its default, while keeping the price range inputs as they are. FAIL if the price range is cleared, or category/sort are not reset.
