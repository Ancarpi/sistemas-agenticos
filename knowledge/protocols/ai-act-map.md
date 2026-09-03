---
slug: ai-act-map
owners:
  - isa-aiact-dossier
---

# Protocol — from regulation to technical artifact

> Origen: 16.2, 16.3, 16.4, 16.6, 16.7

The competence this encodes: translating an obligation into an engineering artifact somebody can run a test against. The obligation → article → artifact → evidence table is data and lives in `schemas/ai-act-obligations.yaml`; this file is the criterion for using it.

**Regulatory status, with its date — nothing here is written without one.** Regulation (EU) 2024/1689 (AI Act), in force 1 August 2024, applied in phases; from 27 July 2026 it must be read in its consolidated version (CELEX 02024R1689-20260727), which incorporates Regulation (EU) 2026/1744 of 8 July 2026 (Digital Omnibus on AI, OJ 24 July 2026, in force 27 July 2026). Annex III high risk moved to **2 December 2027**; Annex I high risk to **2 August 2028**; Art. 50 transparency was **not** deferred and is enforceable from **2 August 2026** (fines up to EUR 15M or 3% of worldwide turnover), with the synthetic-content marking of Art. 50(2) deferred to 2 December 2026 **only** for systems already on the market before 2 August 2026. DORA is Regulation (EU) 2022/2554, applicable since 17 January 2025. Sources verified 2 September 2026 (A·J.5); re-verify before any compliance decision.

## 1. Classify by use case — never by model, never by service

**Why** — risk is set by purpose: the same graph is limited-risk answering a chat and high-risk scoring credit.
**Violated by** — one classification row per model or per microservice; "we use a limited-risk model".
**Checked by** — `banco/compliance/clasificacion-ia.yaml` has one entry per use case, and a test fails when a required entry is missing (16.7).

## 2. Establish the role before the risk

**Why** — provider and deployer carry different obligation lists, and the same system can be both at once; getting the role wrong invalidates the whole dossier below it.
**Violated by** — a dossier that never states which role is being claimed.
**Checked by** — `papel` is a required field of the classification file, and it accepts both values.

## 3. The classification is a versioned file the pipeline can break, not a document

**Why** — a committee reads a classification document once and it then ages in silence, which is the most common way a compliance dossier becomes false without anyone lying.
**Violated by** — a PDF; a classification with no next-review date; a review date that has passed and broke nothing.
**Checked by** — `proximo_examen` in the file plus a test that fails when it expires (`banco/tests/test_clasificacion.py`, 16.7). Systems that do not exist yet are classified in advance.

## 4. Every obligation names its technical artifact and its test

The symmetry that makes the dossier defensible: transparency = the channel notice (Art. 50, M12-M14, 16.5) · human oversight = the approval barrier (Art. 14, M6/M11) · record-keeping = the Art. 12 register (16.6) · robustness = the release gate (`protocols/release-gate.md`) · cybersecurity = the threat model (`protocols/agent-threat-model.md`) · data governance = corpus provenance and freshness (`patterns/knowledge-governance.md`).

**Why** — an obligation with no artifact is a promise; an artifact with no test is a promise with a filename.
**Violated by** — a status of "implemented" whose evidence field is a module name and whose test field is empty.
**Checked by** — each obligation entry carries `estado`, `evidencia` and `prueba`; skill `isa-aiact-dossier` reports the entries that lack one.

## 5. The Art. 12 register is legal evidence; the trace is technical and perishable

**Why** — Art. 12(2) states the purposes — identifying Art. 79(1) risk situations, feeding Art. 72 post-market monitoring, supporting Art. 26(5) oversight — and none of them is debugging. Traces are configured with 30- or 90-day retention; the register outlives them by years.
**Violated by** — answering an audit query by opening the observability tool; a `trace_id` treated as the record of a decision.
**Checked by** — the register is an append-only table queried by subject and time (`WHERE sujeto = ... ORDER BY ts`); the trace link is nullable by design, because a purged trace must not invalidate the record. `protocols/observability-contract.md`.

## 6. Register retention is set by your sector's rules, not by the six-month floor

**Why** — Art. 19 (provider) and Art. 26(6) (deployer) require at least six months, and in a bank that number is a trap: it is a floor. The second paragraph of Art. 26(6) folds these records into the documentation a financial entity already keeps under financial-services law, which is measured in years.
**Violated by** — a TTL invented for the register table; the same retention for conversation, checkpoint, trace and register.
**Checked by** — the retention field points at the institution's retention policy, and the four stores carry four different deadlines.

## 7. Immutability an auditor accepts is chained, not declarative

**Why** — append-only policies hold against your application, not against whoever owns the database; neither a `TRUNCATE` nor a superuser is stopped by a row policy.
**Violated by** — claiming immutability on the strength of table grants alone.
**Checked by** — daily export of the register with a sha256 over its rows chained to the previous day's seal; a gap in the chain is the proof (16.6, 32.4).

## 8. GDPR adds three things the AI Act does not ask for

Legal basis and purpose **per use case** — not "for AI" but "to resolve transfer incidents", with the consequence that reusing those conversations for training is a different purpose needing its own basis. Minimization **where it is decided**, which in this architecture is the Context Contract: its forbidden-data field is minimization implemented (`patterns/context-contract.md`). Retention **per store**, because conversation, checkpoint, trace and audit register have different purposes and cannot share a deadline.

**Why** — a dossier that only speaks about the AI Act is incomplete exactly where an auditor looks first.
**Violated by** — one privacy notice covering "AI"; a single retention setting; decisions affecting a person with no Art. 22 safeguards or impact assessment.
**Checked by** — the classification entry names its basis and purpose; `protocols/memory-governance.md` holds the store inventory.

## 9. In a financial entity DORA displaces NIS2, and the model provider is an ICT third party

**Why** — DORA applies as the special regime: you comply with DORA, not with both. And a model provider inside its scope needs contractual registration, audit rights, an exit strategy and a substitution plan — which is what a model gateway documents.
**Violated by** — a compliance plan that maps to NIS2 in a bank; a model provider treated as a library dependency.
**Checked by** — decide explicitly whether the gateway supports a critical or important function: that box drives the Art. 28(3) register of information and which Art. 30 clauses are mandatory.

## 10. The incident clock is a timestamp your system produces

**Why** — initial notification of a major incident runs in hours: four from classifying it as major, never more than twenty-four from becoming aware. If the only timestamp you hold lives in a trace with 30-day retention, you cannot defend an incident from two months ago.
**Violated by** — a runbook with no "is this notifiable?" step; a detection time inferred from log timestamps.
**Checked by** — detection is an event of the Art. 12 register, not an observability entry; the runbook step exists (`schemas/runbook.template.md`).

## 11. International transfer is decided by a `fallbacks:` line

**Why** — a routing fallback to a second provider can be a second jurisdiction, so the day the primary fails the data leaves the EEA with nobody having read Chapter V.
**Violated by** — reviewing model routing as a performance concern only.
**Checked by** — `banco/config/model_routing.yaml` and the gateway fallback chain are reviewed as a transfer control, and each alias records its provider's jurisdiction. If a provider will not commit in writing to not training on your data, the decision stops being contractual and becomes architectural: do not send it personal data.

## 12. AI literacy is an obligation with evidence

**Why** — a maker-checker signed by someone who does not understand what they are looking at is not human oversight; it is a signature.
**Violated by** — an approval queue whose approvers have no training record.
**Checked by** — training material, a record of who received it, and a periodic review — three artifacts, not a slide.
