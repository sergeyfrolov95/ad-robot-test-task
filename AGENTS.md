# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

`netspeed` — an async download speed benchmark CLI built with aiohttp and typer.
Package managed with uv, src-layout.

## Commands

```sh
uv sync                                   # install dependencies
uv run netspeed --help                    # run the CLI
uv run ruff check . && uv run ruff format .   # lint + format (must pass)
uv run ty check                           # type check (must pass)
uv run pytest                             # run tests
```

Always run ruff and ty after changing code. Zero warnings expected.

## Conventions

- Python 3.12+, modern syntax: `X | Y` unions, `@dataclass(slots=True)`,
  built-in generics, PEP 695 generics (`def f[T](...)`).
- Single quotes everywhere (enforced by ruff).
- No relative imports — use absolute imports (`from netspeed.client import ...`).
- Prefix file-local helpers with `_`.
- No one-liner `if` statements — always split onto two lines.
- Early returns / guard clauses: handle errors first, happy path last.
- No bare `except:`; catch specific exceptions (`aiohttp.ClientError`,
  `TimeoutError`) and let domain errors surface.
- No comments unless they explain a non-obvious decision.
- Docstrings only where they add value (public API, non-obvious logic).

## Architecture notes

- `client.py` holds all aiohttp logic. One `ClientSession` per benchmark run,
  never per request. Responses are streamed via `iter_chunked` — never call
  `resp.read()` on potentially large bodies.
- Concurrency is bounded by `TCPConnector(limit=N, limit_per_host=N)`;
  parallel mode uses `asyncio.TaskGroup` (structured concurrency).
- `stats.py` is pure data + derived metrics, no I/O — keep it that way so it
  stays trivially testable.
- `cli.py` is the only place that prints; use `typer.echo`.
- Wall-clock timings use `time.perf_counter()`.

## Commits

Never commit automatically. Stage and propose changes; the user commits.
