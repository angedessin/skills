---
type: llm
---

Judge the final response, which is a code review of an uncommitted change. PASS if it points out that in check_asset_consistency.py the exit code 2 for 'no target' swallows FAIL results from other contracts, so the hook stays silent even when something is broken. FAIL otherwise.
