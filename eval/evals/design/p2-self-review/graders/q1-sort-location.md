---
type: llm
focus: trace
---

Judge only what the assistant wrote: its replies, the design document, and any review findings it added. Count a point as covered if it appears anywhere in these, either in the design itself or as a finding or open question. PASS if it decides or raises where sorting happens (client or server), given that the API has no sort parameter, and notes a consequence of the choice (for example: client-side sorting breaks once paging or result limits exist, or server-side needs an API change). FAIL otherwise.
