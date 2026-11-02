---
type: llm
---

PASS if the final response proposes saving, as reusable knowledge, that numeric input containing commas (like 10,000) becomes NaN with Number() and must have the commas removed (or be validated) before conversion. FAIL otherwise.
