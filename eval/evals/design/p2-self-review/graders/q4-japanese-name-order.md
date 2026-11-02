---
type: llm
focus: trace
---

Judge only what the assistant wrote: its replies, the design document, and any review findings it added. Count a point as covered if it appears anywhere in these, either in the design itself or as a finding or open question. PASS if it addresses how names are ordered for Japanese text (for example localeCompare with the ja locale, or how kana, kanji and alphanumerics are ordered), rather than assuming a plain string comparison. FAIL otherwise.
