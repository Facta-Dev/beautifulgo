# Go Concurrency Patterns (digest)

Source: Rob Pike's *Go Concurrency Patterns* talk (2012,
https://go.dev/talks/2012/concurrency.slide), plus the follow-up article *Go
Concurrency Patterns: Pipelines and cancellation*
(https://go.dev/blog/pipeline) — the same lineage, one digest. Distilled;
nothing quoted verbatim. Read this before designing or reviewing a pipeline,
fan-out/fan-in, worker pool, or anything with more than two channels on the
page. ~30 rules, paraphrased faithfully, with a link back.

## The model

1. **Goroutines and channels are the whole model.** A goroutine is a function
   running concurrently; a channel is a typed pipe. "Don't communicate by
   sharing memory; share memory by communicating."
2. **Channels are typed, directional, rendezvous-first.** `chan int` (unbuffered,
   rendezvous), `chan<- int` (send-only), `<-chan int` (receive-only). Functions
   declare direction in the signature — it documents the protocol and the
   compiler enforces the protocol.
3. **Unbuffered channels are the default.** A buffered channel bounds a queue,
   it does not speed anything up; a full buffered channel blocks, which is a
   feature (backpressure) not a bug.

## Patterns from the talk

4. **Generator: a function that returns a receive-only channel** it owns and
   closes. The caller receives until closed; ownership is unambiguous: the
   producer closes, the consumer ranges.
5. **`select` is the multiplexer.** Ready in pseudo-random order when several
   are ready; a `default` case makes it non-blocking; `time.After` and
   `<-ctx.Done()` are the standard timeout and cancellation cases.
6. **Timeout the whole operation, not each step**: wrap the work in a select
   with a timeout/cancel case so a slow dependency cannot wedge a request
   forever.
7. **Quit-channel discipline from the talk**: the one who created the goroutine
   closes the quit channel; every long-running goroutine selects on it. The
   modern spelling of the same discipline is `context` — `ctx.Done()` *is* the
   quit channel; on the stack the request ctx comes from `r.Context()`.
8. **Chinese whispers / daisy-chain** (each stage channels to the next) is a
   teaching pattern; in production code it is stage pipelines (below) with
   bounded stages, and every stage must have a way to be abandoned (ctx).
9. **Fan-out/fan-in**: spawn N identical workers reading the same jobs channel;
   merge their output channels into one with a multiplexer goroutine, and make
   every merged goroutine select on `done` so the merged stream can be
   abandoned mid-stream. The blog article's exact shape.
10. **Pipelines: stages connected by channels, each stage owning its inputs.**
    Each stage should:
    - receive inbound values and channel operations until it can decide
      **abandonment** (downstream no longer wants values, or ctx canceled),
    - on early abandon, make sure downstream stages get drained or shut down
      (the article's "range over an error channel and return on done").
11. **Every stage closes its outbound channel when done**; the consumer ends by
    ranging. Closing another goroutine's channel is the cardinal error — the
    sender closes.
12. **Error propagation**: stages send errors on their own error channel (often
    `chan error` per stage, or a results struct with an embedded error), so
    failures travel down the pipeline instead of being swallowed.
13. **Bounded concurrency without a framework**: a semaphore channel
    (`chan struct{}` of size N) or a worker pool sized by `runtime.NumCPU`
    boundary considerations; the article shows fan-out of N identical stages as
    the pooling mechanism — no worker-pool library needed.
14. **`errgroup`-shaped composition is the honest upgrade** (golang.org/x/sync/errgroup):
    same semantics as the article's WaitGroup-plus-error-channel pattern with
    less plumbing. On the stack it is allowed; write the raw-channel version
    only when errgroup's shape doesn't fit.

## Cancellation discipline

15. **Cancellation is cooperative.** Goroutines check `ctx.Done()` in their
    select loops; nothing preempts a goroutine. A pipeline that ignores ctx is
    a leak under load, since each stage only stops when its input closes.
16. **Context deadline vs timeout channel**: `ctx.Done()` composes with
    `select`, composes across API boundaries, and travels with the request.
    `time.After` in a select is for a local timeout inside one stage; the
    request deadline lives in the request's ctx.
17. **`context.WithCancel` at the owner, not the workers.** The owner creates
    the ctx and its cancel; workers only receive. Cancellation flows
    downstream, never upstream.
18. **Passing a request-scoped cancellation through a background job** requires
    detached ctx handling (`context.WithoutCancel`, Go 1.21+) when work must
    survive the request — audit-log writes, the outbox insert after the
    response. Without it, a client disconnect rolls back the very write the
    request was for.
19. **`context.WithoutCancel` + WithTimeout for "do this even if the request
    dies"** work: `ctx, cancel := context.WithTimeout(context.WithoutCancel(ctx), 10*time.Second)`.

## When NOT to reach for channels

20. **State, not messages**: when two goroutines share protected state, a
    mutex beats a channel-based state server.
21. **Don't channel-ize everything.** A WaitGroup + jobs channel beats a
    "pipeline" of N goroutines each owning N goroutines owning the previous
    stage — most single-process work is a loop with a WaitGroup.
22. **Sync primitives before channel machinery.** SKILL.md §7 says
    `sync.WaitGroup`/`Mutex`/`Once` before maps of channels. The talk teaches
    the model; the wiki's "goroutine lifetimes must be clear" is the operating
    rule.
23. **Buffered channel as semaphore** (`chan struct{}` cap N) bounds concurrent
    work; acquire by send, release by receive; combine with ctx so waiters wake
    on cancel: `select { case sem <- struct{}{}: ... case <-ctx.Done(): return ctx.Err() }`.

## Correctness notes review looks for

24. **Ranging over a channel the producer never closes** hangs forever — close
    discipline is a correctness property, not style.
25. **Unbuffered `chan error` from one producer** without a consumer: send
    blocks forever — errors need an owner (buffer size, errgroup, or an
    error-collecting consumer).
26. **A deferred channel close fires at function exit** — make sure all sends
    precede it. Sends after close panic; the sender closes.
27. **Sends after close panic.** Only the sender closes; receiver ranges;
    nobody sends after the close handshake completes.
28. **`for ... range` over two channels in one loop is `select`**, with
    `ctx.Done()` as the third case — this is the shape of every long-lived
    goroutine on the stack.

## Where this digest and SKILL.md differ

- The talk is pre-context (2012): its "quit channel" is today spelled
  `context`. Where the two documents disagree on mechanism, use `context` and
  `errgroup`; the discipline is the same.
- SKILL.md §7 sync-before-channels heuristic vs the talk's channel-forward
  teaching: this digest's own §19 and §21 are the reconciliation — channels
  where ownership genuinely transfers, sync primitives where state is shared.
  On the stack, the worker loops (outbox, janitor) are the canonical owned
  loops: one owner (the composition root), one shutdown path (ctx from
  SIGTERM).

Full links: https://go.dev/talks/2012/concurrency.slide and
https://go.dev/blog/pipeline