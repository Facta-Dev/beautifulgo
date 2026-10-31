# beautifulgo — Architecture Diagrams

Rendered with [Archify](https://github.com/tt-a1i/archify). Each entry is a standalone,
explorable HTML page (inline SVG, dark/light themes, live motion) paired with its source
JSON candidate. The set documents the backend-go stack this repo teaches: chi routing
(`go-chi/chi/v5`, net/http-native), pgx/v5 behind PgBouncer, sqlc per-slice, golang-migrate,
River durable jobs, go-redis, slog, OpenTelemetry + Prometheus, and the depguard
architecture law — hexagonal ports & adapters cut into vertical slices, with the skills,
lints config, contract tests and CI gates as the delivery mechanism.

| Diagram | Type | What it shows | JSON | HTML |
|---|---|---|---|---|
| c4-containers | architecture | Container view: clients → K8s ingress → cmd/api hexagon + cmd/worker River worker, Postgres behind PgBouncer, Redis via go-redis and the mail vendor, with the skills/lints framing layered on — plus the CI contract gates (check.yml's lints / check / examples jobs) and the non-waivable clause that makes the depguard edges unbreakable | [json](c4-containers.json) | [html](c4-containers.html) |
| services-slices | architecture | Package topology: wire composition root, feature slices, platform (authx / email / realtime) and internal/gen/db, and the shared kernel, wired through `Register(chi.Router, Deps)` and ports — slice boundaries read as walls, each labeled with the depguard gate (slice-isolation, platform-no-features, the domain-pure allow-list) that CI runs via check-lints.sh and tests/contracts | [json](services-slices.architecture.json) | [html](services-slices.architecture.html) |
| auth-algorithm | workflow | The auth algorithm as gated steps: signup → 6-digit code → river.AddTx email job → verify → password-first login gates → JWT + rotating refresh with CAS replay defense | [json](auth-algorithm.workflow.json) | [html](auth-algorithm.workflow.html) |
| outbox-algorithm | workflow | Durable email delivery on River: same-transaction `river.AddTx` enqueue, worker fetch, retries with backoff to discard, unique + periodic schedules — the hand-rolled drain shown as the not-built-here example | [json](outbox-algorithm.workflow.json) | [html](outbox-algorithm.workflow.html) |
| auth-sequence | sequence | Full auth request chain across client, auth slices, Postgres, the River worker and the mail vendor — one transaction, code delivery, verify and login | [json](auth-sequence.sequence.json) | [html](auth-sequence.sequence.html) |
| outbox-sequence | sequence | The River worker's message trace: same-transaction enqueue, at-least-once fetch, render/send, ack → completed, backoff → discarded, and the PeriodicJobs janitor purge | [json](outbox-sequence.sequence.json) | [html](outbox-sequence.sequence.html) |
| database-dataflow | dataflow | Where identity data goes: slice use-cases writing users/sessions/code tables and enqueuing river jobs in the same pgx transaction, out through the sender | [json](database-dataflow.dataflow.json) | [html](database-dataflow.dataflow.html) |
| runtime-lifecycle | lifecycle | Process runtime states: typed-config boot → wire composition → serve → readyz gate → steady state, with the middleware gates, the River drain and fail-closed endings | [json](runtime-lifecycle.lifecycle.json) | [html](runtime-lifecycle.lifecycle.html) |

Authored with Archify, sibling set of the facta backend template. The repository content
is grounded in the stack digest the skills carry (`skills/go-best-practices/references/backend-go-stack.md`)
and the depguard configuration under `lints/`.