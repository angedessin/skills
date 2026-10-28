---
type: llm
focus: { source: file, path: src/features/products/parsePriceRange.ts }
---

PASS if this implementation converts full-width digits (and full-width separators or commas) before parsing, so that '１，０００〜５，０００' would be interpreted. FAIL otherwise.
