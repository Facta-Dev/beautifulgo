---
type: llm
focus: trace
weight: 1
---

The bare goroutine in StartSync now has an owner and a shutdown path: it runs under a context (the caller's ctx or an owned stop channel/WaitGroup), exits when that context is done or the owner stops it, and its errors are observed rather than discarded with _