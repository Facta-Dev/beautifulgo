---
type: llm
focus: trace
weight: 1
---

Error codes and out-parameters become error values: syntax, duplicate, and not-found
failures are distinguishable sentinels or typed errors carrying the line number (and the
conflicting key for duplicates), and integer lookup distinguishes missing, non-numeric,
and out-of-range without out-parameters and without panicking on bad input
