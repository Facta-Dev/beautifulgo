---
type: llm
focus: trace
weight: 1
---

domain.go stays I/O-free: the Priority rule lives in domain.go as a typed constant set plus a validity check, and domain.go imports only stdlib (+ internal/shared if present) — no net/http, database/sql, pgx, internal/gen, or platform import was added to it