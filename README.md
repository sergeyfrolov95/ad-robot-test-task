# netspeed

Async download speed benchmark CLI. Measures download throughput by repeatedly
fetching a URL (e.g. a large test file) with [aiohttp](https://docs.aiohttp.org/)
and reporting per-request stats plus an aggregated summary.

## Features

- Streaming downloads — the response body is never loaded fully into memory
- Live per-request progress as each request completes
- Sequential requests by default (spec-compliant: 10 requests one by one)
- Optional bounded parallelism via `--concurrency` (structured concurrency, `asyncio.TaskGroup`)
- Optional `--warmup` requests to absorb DNS/TCP/TLS handshake cost before measuring
- Summary: total downloaded volume, wall time, mean/median request time,
  per-request and aggregate speed in Mbit/s and MB/s
- Per-request timeout, clean error handling, `Ctrl+C` support

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Installation

```sh
uv sync
```

## Usage

```sh
uv run netspeed <URL> [options]
```

Options:

| Option | Short | Default | Description |
|---|---|---|---|
| `--requests` | `-n` | 10 | Number of requests to run |
| `--concurrency` | `-c` | 1 | Number of parallel requests |
| `--timeout` | `-t` | 30 | Per-request timeout, seconds |
| `--warmup` | `-w` | 0 | Unmeasured warmup requests before the run |

Example:

```sh
uv run netspeed https://proof.ovh.net/files/10Mb.dat -n 3
```

Output:

```text
Request 1/3: 200     9.19 Mbit/s in  9.132s
Request 2/3: 200     9.09 Mbit/s in  9.230s
Request 3/3: 200     8.60 Mbit/s in  9.750s
--- Summary ---
Requests OK/failed : 3/0 of 3
Downloaded         : 31.46 MB
Wall time          : 28.15 s
Mean request time  : 9.371 s
Median request time: 9.230 s
Average speed      : 8.96 Mbit/s (1.12 MB/s)
Aggregate speed    : 8.94 Mbit/s (1.12 MB/s)
```

Parallel mode with warmup (3 concurrent requests):

```sh
uv run netspeed https://proof.ovh.net/files/10Mb.dat -n 10 -c 3 -w 1
```

## How it works

Each request opens a `GET` against the target URL, streams the body in 64 KB
chunks via `resp.content.iter_chunked()` and records wall time with
`time.perf_counter()`. Speed is computed as bytes/time.

Two speed metrics are reported:

- **Average speed** — mean of per-request throughputs of successful requests.
- **Aggregate speed** — all successful bytes divided by the run wall time.

In sequential mode (`-c 1`) both coincide and reflect the real channel
throughput. With `-c N > 1` requests share the channel, so per-request
throughput drops roughly N-fold while the aggregate figure shows the actual
saturated channel speed — use the aggregate metric in parallel mode.

The first request on a fresh connection includes DNS resolution plus TCP/TLS
handshake; `-w 1` runs it unmeasured so the reported times reflect pure
transfer.

Public test files you can use:

- `https://proof.ovh.net/files/10Mb.dat` (10 MB)
- `https://proof.ovh.net/files/100Mb.dat` (100 MB)
- `https://speed.cloudflare.com/__down?bytes=100000000` (100 MB)

## Development

```sh
uv sync                                  # install deps
uv run ruff check . && uv run ruff format .   # lint + format
uv run ty check                          # type check
uv run pytest                            # tests
```

## Project layout

```text
src/netspeed/
├── cli.py      # typer CLI, output formatting
├── client.py   # aiohttp benchmark runner
└── stats.py    # metrics: RequestResult, RunSummary
```