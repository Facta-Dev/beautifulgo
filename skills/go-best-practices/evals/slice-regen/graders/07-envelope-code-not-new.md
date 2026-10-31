---
type: llm
focus: trace
weight: 1
---

No new envelope or apperr code was invented: error mapping still goes through the existing writeWidgetErr helper and the existing apperr vocabulary (the agent did not add a second envelope writer, new stable codes, or status mappings outside httpx/apperr's contract)