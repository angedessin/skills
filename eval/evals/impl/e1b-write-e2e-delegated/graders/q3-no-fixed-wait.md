---
type: regex
target: { source: file, path: e2e/search.spec.ts }
pattern: 'waitForTimeout|setTimeout'
match: not_contains
---
