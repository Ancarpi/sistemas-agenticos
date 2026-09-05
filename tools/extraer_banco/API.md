# tools/extraer_banco — API

Rebuilds `banco/` from `libro.md`. The book is the source; the repo is
output. Stdlib only, no PyYAML: `mapeo.yaml` is read by a deliberately small
parser (top-level scalars plus one list of two-space mappings under `entradas:`).

## CLI

```
extraer_banco.py [--libro PATH] [--destino DIR] [--mapeo PATH]
extraer_banco.py --verificar        # checks anchors, writes nothing
extraer_banco.py --resincronizar    # relocates ranges by anchor, rewrites mapeo.yaml
```

Defaults assume the author's layout: `../../../fuente/libro.md` and
`../../banco` relative to this directory.

| Exit | Means |
|---|---|
| 0 | anchors valid; the tree (or the verification) is done |
| 1 | the book moved, a required file is missing, or `mapeo.yaml` is malformed |

## Contract

- **The mapping lives once, as data**, in `mapeo.yaml`. Never in the script and
  never in the generated tree. One entry per destination file, with `bloques`
  (1-indexed **content** line ranges, fences excluded), `modulo`, `modo`, `nota`.
- **Every block carries two anchors**, `anclas` and `anclas_fin` — its expected
  first and last line. The book is a living document, so a range that no longer
  starts and ends where it claimed is a hard failure, not a warning: exit 1 and
  nothing is written. `--resincronizar` searches each anchor pair and picks the
  match nearest the recorded position, then rewrites `mapeo.yaml` and prints the
  before/after so the diff gets reviewed. It never writes the tree in the same run.
- **Four modes.** `verbatim` creates the destination from its blocks concatenated
  in book order. `patch` appends blocks to a destination already created, behind a
  comment marker naming the module. `plantilla` copies a scaffold from
  `plantillas/` — the only content in the tree that is not the book. `fragmento`
  embeds a block into `banco/COSTURAS.md` instead of a code file.
- **Extraction is byte-verbatim**, comments and typos included, because the repo
  has to match the printed page. The script adds no provenance header to any
  file; provenance lives in the generated `MAPEO.md`.
- **`patch` never merges in place.** Where the insertion point matters — the M17.2
  block that *replaces* `FastAPI()` in `servidor.py`, for one — the entry sets
  `pendiente: si`, the marker says so, and the seam is listed in `COSTURAS.md`.
  Pasting a fragment into its right place is a decision, not a text operation.
- **Generated, therefore never hand-edited:** the whole `banco/` tree
  except `README.md`, `pyproject.toml`, `conftest.py`, `docker-compose.yml`,
  and the two book artifacts translated to data by hand,
  `contratos/triage_sepa.contract.yaml` and `evals/capstone_gate.eval.yaml`.
  `MAPEO.md` and `COSTURAS.md` are rewritten on every
  run, and `.env.example` is generated too, by `tools/generar_env/` from the
  `.env` block of §0.4 — not by this script.

## Boundaries

- Blocks are located by absolute line number, so the anchors are the only
  protection against drift. If a code block is *added* to the book, ordinals
  shift and the mapping has to be re-derived by hand — the anchors will say so.
- It does not run, lint or import anything it writes. Which files actually run is
  in `banco/README.md`, and that judgement is not extractable.
- It never touches `fuente/`. Read-only on the book, always.

## Consumers

- None. It is a maintenance tool: the author runs it when the book changes, and
  `banco/README.md` documents it for readers of the repo.
