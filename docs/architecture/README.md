# beautifulgo — Architecture Diagrams

Rendered with [Archify](https://github.com/tt-a1i/archify). Each entry is a standalone,
explorable HTML page (inline SVG, dark/light themes, live motion) paired with its source
JSON candidate. The set documents the backend-go stack this repo teaches: Go 1.27 stdlib
`net/http`, pgx/v5, sqlc per-slice, goose, slog, and the depguard architecture law —
hexagonal ports & adapters cut into vertical slices, with the skills and lints config as
the delivery mechanism.

| Diagram | Type | What it shows | JSON | HTML |
|---|---|---|---|---|
| c4-containers | architecture | Container view: clients → edge proxy → cmd/api hexagon + cmd/worker outbox drain, Postgres and the mail vendor, with the skills/lints framing layered on | [json](c4-containers.json) | [html](c4-containers.html) |
| services-slices | architecture | Package topology: composition root, feature slices, platform (authx / email / realtime / gen-db) and the shared kernel, wired through `Register(mux, Deps)` and ports | [json](services-slices.architecture.json) | [html](services-slices.architecture.html) |
| auth-algorithm | workflow | The auth algorithm as gated steps: signup → 6-digit code → verify → password-first login gates → JWT + rotating refresh with CAS replay defense | [json](auth-algorithm.workflow.json) | [html](auth-algorithm.workflow.html) |
| outbox-algorithm | workflow | The zero-broker outbox drain: transactional enqueue, SKIP LOCKED claim CTE, render/send, 2^n jittered backoff and dead-letter settle | [json](outbox-algorithm.workflow.json) | [html](outbox-algorithm.workflow.html) |
| auth-sequence | sequence | Full auth request chain across client, auth slices, Postgres, outbox worker and mail vendor — one transaction, code delivery, verify and login | [json](auth-sequence.sequence.json) | [html](auth-sequence.sequence.html) |
| outbox-sequence | sequence | The worker's message trace: claim with lease, send over Console/SMTP, mark_sent, retry/dead-letter, and the hourly janitor purge | [json](outbox-sequence.sequence.json) | [html](outbox-sequence.sequence.html) |
| database-dataflow | dataflow | Where identity data goes: slice use-cases writing users/sessions/code tables and enqueueing email_jobs in the same pgx transaction, out through the sender | [json](database-dataflow.dataflow.json) | [html](database-dataflow.dataflow.html) |
| runtime-lifecycle | lifecycle | Process runtime states: typed-config boot → wiring → serve → readyz gate → steady state, with the middleware gates, outbox drain loop and fail-closed endings | [json](runtime-lifecycle.lifecycle.json) | [html](runtime-lifecycle.lifecycle.html) |

Authored with Archify, sibling set of the facta backend template. The repository content
is grounded in the stack digest the skills carry (`skills/go-best-practices/references/backend-go-stack.md`)
and the depguard configuration under `lints/`.