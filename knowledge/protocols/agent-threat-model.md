---
slug: agent-threat-model
owners:
  - isa-threat-model
  - isa-context-leak
---

# Protocol — the agent threat model

> Origen: 16.1, M26.1, M26.3, M26.4

The asset → threat → control matrix is data and lives in `schemas/threat-model.yaml`; the adversarial corpus that exercises it is `schemas/adversarial-cases.yaml`. This file is the criterion that makes a mapping useful instead of decorative.

**The two lists, always cited with their year, because they renumber between editions.** OWASP Top 10 for LLM Applications **2025** (identifiers LLM01:2025 to LLM10:2025; no later edition as of 2 September 2026) and OWASP Top 10 for Agentic Applications, published **9 December 2025** (categories ASI01 to ASI10) — the second one is the list that actually describes an agent with tools. Check the current edition's equivalent before pasting any identifier into a risk matrix (A·J.4).

## 1. Architecture is the primary security control

**Why** — a system where the model decides and the code executes, with least privilege and human approval on the irreversible, resists most attacks by design rather than by patch.
**Violated by** — a security plan whose measures are all filters and wordings; hardening a prompt instead of narrowing a permission.
**Checked by** — every mitigation must name an architectural equivalent (`protocols/policy-over-model.md`); prompt-only mitigations are recorded as unmitigated.

## 2. Model the assets, not the attacks

Six assets carry the matrix: tools, context, memory, traces, MCP server, agent.

**Why** — attack names change every edition; the asset list does not, so a per-asset matrix survives a renumbering and can be fanned out one asset at a time.
**Violated by** — a threat model organized as a list of prompt-injection variants.
**Checked by** — `schemas/threat-model.yaml` is keyed by asset; skill `isa-threat-model` walks it asset by asset.

## 3. Three columns, and the third one is the point

Risk · the line that mitigates it · **what that line does not cover**.

**Why** — a two-column OWASP mapping is a conformity declaration, and conformity declarations have never stopped an attack. The third column writes down the residual risk you are accepting.
**Violated by** — a matrix that ends at the control column; a control cited without the version or file where it lives.
**Checked by** — skill `isa-threat-model` refuses to emit a two-column matrix; every row's third column is non-empty.

## 4. Somebody signs the residual risk, by name

**Why** — a residual risk with no owner is an accepted risk nobody accepted.
**Violated by** — "risk accepted by the team"; a signature with no date.
**Checked by** — the matrix carries an owner and a date per row, and it is a blocking area of `protocols/production-checklist.md`.

## 5. What is not mapped is written down as not mapped

**Why** — the categories absent from your matrix are not covered, they are unassessed, and the difference matters to whoever reads the dossier.
**Violated by** — a matrix listing three of the ten categories and presenting itself as complete coverage.
**Checked by** — the artifact enumerates the unmapped categories of both lists explicitly.

## 6. Indirect injection is the default assumption for every ingested byte

**Why** — malicious instructions hide in *data* the agent processes: an email, a corpus PDF, an MCP tool description, the text of a ticket. It is the most dangerous class because the agent trusts its own sources.
**Violated by** — treating retrieved text, tool output or third-party metadata as instructions; one channel carrying both instructions and data.
**Checked by** — instruction/data separation and forbidden-data declaration per call (`patterns/context-contract.md`); lens `isa-context-leak`.

## 7. A tool's authoritative value is read from the record, never from the model's argument

**Why** — the argument the model writes is attacker-reachable; the record is not. This is the single line that caps most injection damage.
**Violated by** — an amount, an account owner or a risk tier taken from the tool call instead of looked up.
**Checked by** — the manifest's preconditions are evaluated against authoritative state (`patterns/tool-capability.md`); the residual risk — anything below the threshold that wakes nobody — is stated in euros in the third column.

## 8. Third-party metadata is untrusted data: allow-list, pin, review, scope

**Why** — MCP and A2A cross trust boundaries and their *descriptions* are attack surface: a tool description can induce the model to reveal context, and an Agent Card can overstate capabilities.
**Violated by** — connecting an uncontrolled MCP server to write tools; auto-accepting a changed tool description; sharing internal memory or credentials across a protocol boundary.
**Checked by** — an allow-list pinned by hash of the approved description that refuses to start when it changes (10.2); schema review, auth, scopes and PII-free logging per tool; separate credentials and end-to-end audit across systems.

## 9. Excessive agency is a design defect, not a configuration one

**Why** — permissions, tools and autonomy handed out beyond need are the precondition of every other finding in the matrix.
**Violated by** — a catalogue of eighty tools offered in one call; an agent whose scopes exceed its declared tier.
**Checked by** — dynamic tool selection by `risk_tier` and context (M20.4); `protocols/autonomy-ladder.md`; lens `isa-autonomy-drift`.

## 10. Anything that executes, browses or drives a computer runs in a real sandbox

**Why** — unbounded execution turns a content-level compromise into host access.
**Violated by** — generated code run in the app process; a browser profile carrying real session cookies; computer use combined with privileged credentials.
**Checked by** — ephemeral filesystem, non-root user, controlled egress with a domain allow-list, secrets not mounted by default, hard CPU/memory/time limits, auditable captures, and approval to cross a boundary. Computer use is a last resort for systems without an API.

## 11. Consumption is a threat: budget it

**Why** — an unbounded loop is a denial-of-service you pay for, and at night it is a billing incident.
**Violated by** — an agent with no step budget, token budget, rate limit or circuit breaker.
**Checked by** — `patterns/backend-reliability.md`; lens `isa-idempotence`.

## 12. Red team is a programme, and every finding ends as a case

**Why** — a list of clever prompts proves nothing twice; taxonomy, severity, reproducibility, owner and mitigation are what make it a control.
**Violated by** — an annual exercise with no reproducible cases; a finding closed without a regression case.
**Checked by** — findings are seeded from and returned to `schemas/adversarial-cases.yaml`, and each one becomes an eval case (`protocols/release-gate.md`, R9).
