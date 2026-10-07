"""netspeed — async download speed benchmark CLI."""

import asyncio
from typing import Annotated

import typer

from netspeed.client import run_benchmark
from netspeed.stats import RequestResult, RunSummary

app = typer.Typer(
    name='netspeed',
    help='Measure download speed by repeatedly fetching a URL.',
    no_args_is_help=True,
    add_completion=False,
)


def _on_result(result: RequestResult, total: int) -> None:
    if result.error is not None:
        typer.echo(f'Request {result.index + 1}: FAILED ({result.error})', err=True)
        return
    typer.echo(
        f'Request {result.index + 1}/{total}:'
        f' {result.status} {result.mbit_per_s:8.2f} Mbit/s in {result.elapsed_s:6.3f}s'
    )


def _print_summary(summary: RunSummary, requests: int) -> None:
    typer.echo('--- Summary ---')
    typer.echo(f'Requests OK/failed : {len(summary.ok)}/{len(summary.failed)} of {requests}')
    typer.echo(f'Downloaded         : {summary.total_bytes / 1_000_000:.2f} MB')
    typer.echo(f'Wall time          : {summary.wall_s:.3f} s')
    typer.echo(f'Mean request time  : {summary.mean_elapsed_s:.3f} s')
    typer.echo(f'Median request time: {summary.median_elapsed_s:.3f} s')
    typer.echo(
        f'Average speed      : {summary.mean_speed_mbit_per_s:.2f} Mbit/s'
        f' ({summary.mean_speed_mbit_per_s / 8:.2f} MB/s)'
    )
    typer.echo(
        f'Aggregate speed    : {summary.aggregate_mbit_per_s:.2f} Mbit/s'
        f' ({summary.aggregate_mbit_per_s / 8:.2f} MB/s)'
    )


@app.command()
def measure(
    url: Annotated[str, typer.Argument(help='URL of a large file to download.')],
    requests: Annotated[
        int,
        typer.Option('--requests', '-n', min=1, help='Number of requests.'),
    ] = 10,
    concurrency: Annotated[
        int,
        typer.Option('--concurrency', '-c', min=1, help='Parallel requests.'),
    ] = 1,
    timeout: Annotated[
        float,
        typer.Option('--timeout', '-t', min=0.1, help='Per-request timeout, s.'),
    ] = 30.0,
    warmup: Annotated[
        int,
        typer.Option('--warmup', '-w', min=0, help='Unmeasured warmup requests.'),
    ] = 0,
) -> None:
    """Run the benchmark against URL and print per-request stats and summary."""
    try:
        summary = asyncio.run(
            run_benchmark(
                url=url,
                requests=requests,
                concurrency=concurrency,
                timeout_s=timeout,
                warmup=warmup,
                on_result=lambda result: _on_result(result, requests),
            )
        )
    except KeyboardInterrupt:
        typer.echo('Aborted.', err=True)
        raise typer.Exit(code=130) from None

    if not summary.ok:
        typer.echo('Error: all requests failed.', err=True)
        raise typer.Exit(code=1)

    _print_summary(summary, requests)


def main() -> None:
    app()


if __name__ == '__main__':
    main()
