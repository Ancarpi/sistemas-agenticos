---
slug: context-contract
owners:
  - isa-context-contract
  - isa-context-leak
  - isa-scaffold-agent
---

# Pattern — the Context Contract, in its three scopes

> Origen: 19.1, 22.1, 22.3, 23.1

The unit of design is not the agent: it is one model call. The contract exists in three scopes — per call (19.1), per channel (22.1) and per boundary between agents (23.1) — and the three are the same idea at three radii. The JSON Schema of the per-call contract is `schemas/context-contract.schema.json`.

## 1. Every node that calls a model declares a contract

**Why** — it is not aesthetic documentation, it is a security interface: a new developer adding a context source must do it against the contract, the way an API is not changed without reviewing compatibility.
**Violated by** — a node that builds its prompt from whatever happens to be in state; a contract declared for the main agent and not for the summarizer, the router or the judge.
**Checked by** — the contract is a typed object constructed next to the node, not prose; lens `isa-context-leak` reports model calls with no declared contract.

## 2. Eight fields per call, and none of them is optional

| Field | The design question it answers |
|---|---|
| Objective | What must this call decide or produce? |
| Instructions | Which rules have authority over the output? |
| Allowed data | Which fragments of state, memory or RAG may it see? |
| Forbidden data | What never enters the call? |
| Visible tools | Which capabilities are offered, and why? |
| Output | Which schema validates the response? |
| Limits | How much may it spend, and how long may it take? |
| Fallback | What happens when it fails? |

**Why** — each field removes one silent failure mode: an objective removes scope creep, forbidden data removes the leak, visible tools remove excessive agency, limits remove the runaway loop, fallback removes the hang.
**Violated by** — a contract with allowed data and no forbidden data; unbounded limits; `fallback: null`.
**Checked by** — `schemas/context-contract.schema.json` makes node, objective, allowed data, visible tools, both token limits, latency budget and fallback required; `tools/isa_validate/isa_validate.py` exits non-zero. Skill `isa-context-contract` rejects allowed data declared without forbidden data.

## 3. Allow-list the state keys; do not deny-list the fields

**Why** — a deny-list is a promise about data that does not exist yet, so the next state key added is visible by default.
**Violated by** — passing the whole state object and stripping known-bad keys.
**Checked by** — the contract lists allowed keys explicitly; forbidden patterns are the second barrier, not the first.

## 4. Forbidden data is GDPR minimization, implemented

**Why** — minimization has to be enforced where the decision is taken about what enters a call; anywhere else it is a policy document.
**Violated by** — an identifier resolved to a full value before the call because "the model needs context"; a masked answer built from an unmasked prompt.
**Checked by** — identifiers in state, values rehydrated inside the authorized tool and not returned to the context (19.3, `protocols/memory-governance.md`); lens `isa-context-leak`.

## 5. Instructions and data never share a channel

**Why** — if retrieved text arrives in the same slot as the system rules, an instruction hidden in a PDF has the same authority as yours (`protocols/agent-threat-model.md`).
**Violated by** — concatenating retrieved chunks into the system prompt; a ticket body interpolated into instructions.
**Checked by** — allowed data enters as data with its provenance; the instructions field is the only authority slot. Lens `isa-context-leak`.

## 6. Visible tools are decided per call, not per agent

**Why** — a tool that is not offered cannot be misused, and narrowing the offer for one turn is cheaper and stronger than any wording.
**Violated by** — one tool list for the whole graph; triage able to see a write tool.
**Checked by** — the contract's visible-tools field is applied at the call site (M4 request override); lens `isa-autonomy-drift` compares it against declared tiers.

## 7. A channel declares a Conversation Contract

Seven elements: identity (how it introduces itself), scope (what it can and cannot do), data (what it will ask for and why), actions (what it executes), citations (how it justifies regulated answers), escalation (when a human takes over), memory (what it remembers, and how to erase it).

**Why** — these are the promises visible to the user and the non-negotiable rules of the surface; unwritten, each channel invents its own and one of them will invent wrong.
**Violated by** — a channel with no AI disclosure (Art. 50 is enforceable from 2 August 2026, `protocols/ai-act-map.md`); a scope that permits personalized financial advice by omission; asking for a PIN because nobody wrote down that it must never be asked.
**Checked by** — the disclosure text is centralized and its delivery is recorded per surface (16.5); the contract is a reviewed artifact per channel.

## 8. A boundary between agents declares a Handoff Contract, and `authority` is its load-bearing field

Fields: from, to, task, **authority** (`recommend` / `prepare` / `execute` / `approve`), facts, assumptions, open questions, permitted tools, forbidden actions, required output schema, return-to.

**Why** — without a contract, agents pass whole conversations and each specialist re-interprets the world: latency, contradictions and context leaks. `authority` is what stops a recommending agent from being read as an executing one.
**Violated by** — a handoff that forwards the message history; a receiving agent that infers its own authority; no return-to, so control is lost.
**Checked by** — the typed handoff object crosses the boundary (`banco/src/core/contratos.py`); lens `isa-autonomy-drift` checks that the authority granted does not exceed the receiver's declared tier.

## 9. Escalation to a human is a contract too, not a dead end

The packet carries: conversation and customer ids, a typed reason, verified facts, unresolved questions, tools used, proposed next action, risk flags, trace link.

**Why** — escalating is not failing; escalating badly is — with no summary, no trace, no priority, and the user forced to repeat everything.
**Violated by** — a handoff to a human consisting of the transcript; a summary the human cannot correct.
**Checked by** — the packet is a typed object (22.3); the human's correction returns to the eval dataset (`protocols/release-gate.md`, R9).
