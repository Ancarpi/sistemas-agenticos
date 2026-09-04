# tools/generar_env — API

Writes `banco/.env.example` from the `.env` block of §0.4 of `libro.md`, and
refuses to leave the two out of sync. Stdlib only. The book is the source;
`banco/.env.example` is output, like the rest of `banco/`.

## CLI

```
generar_env.py [--libro PATH] [--banco DIR]
generar_env.py --verificar     # compares, writes nothing
```

Defaults assume the author's layout: `../../../fuente/libro.md` and
`../../banco` relative to this directory.

| Exit | Means |
|---|---|
| 0 | the block was found, the file is written (or already matches) and every `os.environ` in `banco/` is declared in the book |
| 1 | the block is not in the book exactly once, a variable the tree reads is missing from the book, a line would exceed 78 columns, or `--verificar` found the file stale |

## Contract

- **The block is located by content, never by line number.** It is the `ini`
  fence whose first line starts with `OPENAI_API_BASE=`. Exactly one, or exit 1:
  a second `.env` block in the book is an ambiguity the script will not guess at.
- **Values are emptied when they are placeholders and kept when they are
  answers.** A value containing `...` or `<` is a placeholder and comes out
  blank; `ENTORNO=dev`, `LANGSMITH_TRACING=true` or
  `MODEL_ROUTING=config/model_routing.yaml` are the book's answer and stay.
  Consequence: no secret can reach the file, because the book has none.
- **Comments come across verbatim**, including the locator each variable carries.
  Their column is recomputed, and the whole file stays inside 78 columns.
- **The second half is the anti-drift half.** Every `os.environ[...]`,
  `os.environ.get(...)` and `os.getenv(...)` in `banco/` (`.venv`, `__pycache__`
  and `.pytest_cache` excluded) must name a variable the block declares. One
  that does not is printed as `FALTA EN EL LIBRO:` with the file and line that
  reads it, and the exit code is 1. A module that dies on its first line for a
  variable nobody wrote down is not a delivered file.
- **It is fixed in the book, never here.** A missing variable is a book edit
  followed by another run, exactly like the rest of `banco/`.

## Boundaries

- It only sees what the tree reads *explicitly*. A library that reads its own
  environment (the LiveKit, Deepgram, Cartesia and Tavus plugins of M13 and
  M14) is invisible to the audit: those variables are in the block because the
  book declares them, not because this script found them.
- It does not create or read a `.env`, and it never writes inside `fuente/`.

## Consumers

- `.github/workflows/promesas.yml`, in the book-gated step: `--verificar`
  alongside the extractor's three checks.
- `banco/README.md`, which names it as the only way `.env.example` changes.
