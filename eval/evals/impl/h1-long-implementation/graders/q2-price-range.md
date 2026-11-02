---
type: llm
focus: { source: file, path: src/features/products/searchFilters.ts }
---

PASS if this module filters by a price range where an empty (or missing) lower or upper bound means no limit on that side, and when the lower bound is greater than the upper bound the price range is not applied (or the function reports it as invalid so the caller can skip it). FAIL if empty bounds are treated as 0, or min > max silently produces an empty result.
