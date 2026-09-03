# tools/isa_validate — API

Validates one artifact against its schema in `schemas/`. This is the
mechanism behind four skills' refusals: the skill does not decline because
the model remembered a rule, it declines because this script exited
non-zero and named the field. Stdlib only, no dependency required.

## CLI

```bash
isa_validate.py context-contract <path> [<path> ...]
isa_validate.py capability       <path> [<path> ...]
isa_validate.py eval-card        <path> [<path> ...]
isa_validate.py agent-package    <path> [<path> ...]
```

Options: `--esquemas DIR` to point at another `schemas/` (default: the
package's own, resolved from this file), `-q` / `--silencioso` to print
only failures — the CI form.

Each subcommand fixes the schema; nothing is inferred from the filename.

| Subcommand | Schema | Typical artifact |
|---|---|---|
| `context-contract` | `context-contract.schema.json` | one node's contract (19.1) |
| `capability` | `tool-capability.schema.json` | `<tool>.capability.yaml` (20.1) |
| `eval-card` | `eval-card.schema.json` | the release gate's card (A·G.2, 15.6) |
| `agent-package` | `agent-package.schema.json` | `agent.yaml` (32.3) |

| Exit | Means |
|---|---|
| 0 | every artifact validates |
| 1 | at least one artifact is invalid — one line per defect on stdout |
| 2 | the validator or the invocation is at fault: file unreadable, JSON or YAML it cannot parse, schema missing, or a JSON Schema keyword it does not support |

Exit 1 and exit 2 are different failures on purpose. 1 is a verdict about
the artifact; 2 means no verdict was reached, so it must never be read as
«it passed».

## Contract

- **The message is the product.** Every defect is one line, `path: what is
  wrong`, where the path is the position inside the artifact —
  `metrics/0: falta n_cases`, `idempotency: falta key`,
  `models/supervisor: 'claude-opus-4' coincide con el patron prohibido …`.
  Root-level fields report as `(raiz)`. A defect that only says «invalid»
  is a defect this script is not allowed to produce, because the caller is
  a skill that has to tell the user which number to go and get.
- **Messages are in Spanish**, ASCII, so they can be pasted straight into
  the `VALIDACIÓN:` line of a skill's output contract.
- **A keyword it does not support is exit 2, never a silent pass.** The
  supported subset is exactly what the four schemas use today: `type`
  (including a list of types), `required`, `properties`,
  `additionalProperties` (both `false` and a subschema), `minProperties`,
  `enum`, `const`, `pattern`, `not`, `oneOf`, `allOf`, `if` / `then`,
  `minimum`, `maximum`, `exclusiveMinimum`, `minLength`, `minItems`,
  `uniqueItems`, `items`, with objects and arrays nested to any depth.
  `$schema`, `$id`, `$comment`, `title`, `description`, `default`,
  `examples` and `format` are annotations and are ignored — `format:
  "date"` in the eval card is annotation, and the `pattern` next to it is
  what actually checks the shape. Add a keyword to a schema without adding
  it here and the next run stops with `palabra clave de JSON Schema sin
  soporte`, which is the point: an unchecked rule must not look checked.
- **A conditional says why it fired.** The `if` / `then` blocks of
  `tool-capability` and `agent-package` are the L4 barrier of A·H, so
  their messages carry the reason:
  `(raiz): falta approval (exigido cuando risk_tier = 'irreversible_high')`.
- **Timestamps are serialized to ISO-8601 before validating.** An eval
  card is YAML, and `baseline: 2026-07-01` comes back from
  `yaml.safe_load` as a `datetime.date`, not a string, against a schema
  that requires `"type": "string"`. Without the conversion the book's own
  card fails on a type error that has nothing to do with the gate. Dates,
  datetimes and times are converted wherever they appear, at any depth.
- **An explicit `null` counts as missing.** `fallback:` with no value
  reports `falta fallback`, because an unset limit is an unlimited limit
  and the canon does not distinguish «absent» from «declared empty».
- **YAML: PyYAML when it is installed, a small internal parser when it is
  not.** The script has no dependency, so `python3 isa_validate.py` works
  in a bare CI container. The internal parser covers what these artifacts
  use — nested maps by indentation, block and inline lists, single and
  double quotes, comments — and stops with exit 2 on anything else rather
  than guessing (anchors, inline maps, block scalars, multiple documents).
  Both paths were checked to produce identical structures for the four
  artifacts of the book. `.json` files are read with `json`.

## Boundaries

- **One artifact, one schema, no cross-file checks.** It does not resolve
  `rollback.tool` to a real manifest, does not check that every tool in
  `tools_allowed` has one, does not open the card that
  `evals.release_gate` points at, and does not verify that every L4 tool
  appears in `human_in_the_loop.required_for` (rule 5 of
  `knowledge/protocols/autonomy-ladder.md`, which is a review, not a
  field). Those are judgements for the skills and the lenses in
  `agents/isa/`.
- **It validates shape, not truth.** `n_cases: 4` validates; whether four
  cases can detect the drop the owner cares about is Step 2 of
  `/isa-eval-gate`, and no schema can hold it. Same for an `owner` that
  is a queue, an `intent` that restates the name, or an idempotency key
  built from a timestamp: the schema sees a non-empty string.
- **No `$ref`, no remote schemas.** The four schemas are self-contained;
  a `$ref` added to one of them stops the run with exit 2.
- **It writes nothing.** Read-only on the artifact and on `schemas/`.

## Consumers

- `skills/isa-eval-gate` — Step 3. The refusal to write a card with no
  sample size is this script exiting 1 with `metrics/0: falta n_cases`.
- `skills/isa-tool-manifest` — Step 4. A manifest with no idempotency key
  or no rollback does not validate, so it is not written.
- `skills/isa-context-contract` — Step 4, on the contract written as YAML
  or JSON before it is asserted in code.
- `skills/isa-scaffold-agent` — Step 5, over the emitted `agent.yaml`.
- `knowledge/patterns/context-contract.md`,
  `knowledge/patterns/tool-capability.md`,
  `knowledge/protocols/autonomy-ladder.md`,
  `knowledge/protocols/release-gate.md` — each cites this script as the
  `Checked by` of its rule.
- CI: the batch form is the intended one, one exit code for the run.

```bash
python3 tools/isa_validate/isa_validate.py -q capability \
    $(git ls-files '*.capability.yaml')
```
