---
type: llm
focus: trace
weight: 1
---

Persistence goes through the declared port, not around it: the new query is added to ports.go's WidgetStore as a method (or the existing ListBySize method is used), the use case calls the port, and postgres.go is the only file touching db/pgx output — the agent did not declare a new interface elsewhere or inject *pgxpool.Pool into the use case