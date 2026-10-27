---
type: llm
---

Judge the final response, which reviews the Playwright spec e2e/search.spec.ts. PASS if it points out that the second test reads internal component state through page.evaluate (window.__searchState) instead of checking what the user sees. FAIL otherwise.
