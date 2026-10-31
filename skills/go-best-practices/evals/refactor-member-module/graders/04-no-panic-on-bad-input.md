---
type: llm
focus: trace
weight: 1
---

The panic("email is required") on reachable bad input is replaced by a returned error (sentinel or wrapped), and no panic remains on any input-reachable path