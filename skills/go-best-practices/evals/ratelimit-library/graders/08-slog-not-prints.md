---
type: llm
focus: trace
weight: 1
---

No fmt.Println, log.Print, or println in library code; if the limiter logs anything it uses slog with structured attributes
---