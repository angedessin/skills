---
type: llm
focus: { source: file, path: src/features/products/parsePriceRange.test.ts }
---

Judge these unit tests for parsePriceRange. PASS if they cover at least three kinds of uninterpretable input returning null, including an empty string and a range whose lower bound is greater than the upper bound (or the test explicitly documents a different decided behavior for that case). FAIL otherwise.
