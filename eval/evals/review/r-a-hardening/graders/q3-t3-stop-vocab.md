---
type: llm
---

Judge the final response, which is a code review of an uncommitted change. PASS if it points out that STOP_VOCAB in check_export_stopcontract.py only matches the plain form '止まる' and misses other ways a stop contract is written (such as '待つ' or '書き込まない'), so stop contracts can be missed. FAIL otherwise.
