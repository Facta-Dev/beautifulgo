---
paths:
  - "skills/**"
  - "lints/**"
  - "tests/**"
  - "examples/**"
  - "docs/**"
---

# Playbooks for `beautifulgo` — load on demand

Before editing a skill, linter config, test or doc, read the playbook that
governs it. Do not `@`-import a playbook: this rule is the routing entry and
the always-on instruction set stays inside the harness budget.

- [`PLAYBOOK_MASTER.md`](https://github.com/Facta-Dev/ai-coding-playbook/blob/main/PLAYBOOK_MASTER.md) — the master index, precedence
  and cross-playbook invariants (`§3` is the constitution).
- [`PLAYBOOK_BACKEND.md`](https://github.com/Facta-Dev/ai-coding-playbook/blob/main/PLAYBOOK_BACKEND.md) — the shared architecture contract.
- [`PLAYBOOK_GOLANG.md`](https://github.com/Facta-Dev/ai-coding-playbook/blob/main/PLAYBOOK_GOLANG.md) — the Go contract this repo implements.
- [`PLAYBOOK_SECURITY.md`](https://github.com/Facta-Dev/ai-coding-playbook/blob/main/PLAYBOOK_SECURITY.md) — shared contract.
- [`PLAYBOOK_TESTS.md`](https://github.com/Facta-Dev/ai-coding-playbook/blob/main/PLAYBOOK_TESTS.md) — shared contract.
- [`PLAYBOOK_URLS.md`](https://github.com/Facta-Dev/ai-coding-playbook/blob/main/PLAYBOOK_URLS.md) — shared contract.
- [`PLAYBOOK_AUDIT.md`](https://github.com/Facta-Dev/ai-coding-playbook/blob/main/PLAYBOOK_AUDIT.md) — shared contract.
- [`PLAYBOOK_CLAUDE_CODE.md`](https://github.com/Facta-Dev/ai-coding-playbook/blob/main/PLAYBOOK_CLAUDE_CODE.md) — the kit contract.

The set is split into `_PART<n>` files where needed; `PLAYBOOK_MASTER.md` and
`manifest.json` in the playbook repo map each part.
