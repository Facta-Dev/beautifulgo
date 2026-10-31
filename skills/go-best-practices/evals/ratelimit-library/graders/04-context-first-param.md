---
type: llm
focus: trace
weight: 1
---

Wait takes ctx context.Context as its first parameter and checks ctx.Done() (select) rather than polling with time.Sleep or ignoring the context
---