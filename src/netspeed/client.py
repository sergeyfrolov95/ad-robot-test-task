"""Async download benchmark using aiohttp."""

import asyncio
import time
from collections.abc import Callable

import aiohttp

from netspeed.stats import RequestResult, RunSummary

CHUNK_SIZE = 64 * 1024


async def _download_once(
    session: aiohttp.ClientSession,
    url: str,
    index: int,
) -> RequestResult:
    """Stream a single GET request, counting bytes and wall time."""
    started = time.perf_counter()
    received = 0
    try:
        async with session.get(url) as resp:
            resp.raise_for_status()
            async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                received += len(chunk)
            return RequestResult(
                index=index,
                status=resp.status,
                bytes=received,
                elapsed_s=time.perf_counter() - started,
            )
    except (TimeoutError, aiohttp.ClientError) as exc:
        return RequestResult(
            index=index,
            status=None,
            bytes=received,
            elapsed_s=time.perf_counter() - started,
            error=f'{type(exc).__name__}: {exc}',
        )


async def run_benchmark(  # noqa: PLR0917 - benchmark params, keyword-called
    url: str,
    requests: int,
    concurrency: int,
    timeout_s: float,
    warmup: int = 0,
    on_result: Callable[[RequestResult], None] | None = None,
) -> RunSummary:
    """Run `requests` downloads with bounded concurrency and collect metrics.

    `on_result` fires as soon as each request completes (live progress);
    `warmup` requests run first and are not included in the summary.
    """
    timeout = aiohttp.ClientTimeout(total=timeout_s)
    connector = aiohttp.TCPConnector(limit=concurrency, limit_per_host=concurrency)
    summary = RunSummary()

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        for index in range(warmup):
            await _download_once(session, url, index)

        started = time.perf_counter()

        if concurrency <= 1:
            for index in range(requests):
                result = await _download_once(session, url, index)
                summary.results.append(result)
                if on_result is not None:
                    on_result(result)
        else:

            async def _worker(index: int) -> None:
                result = await _download_once(session, url, index)
                summary.results.append(result)
                if on_result is not None:
                    on_result(result)

            async with asyncio.TaskGroup() as tg:
                for index in range(requests):
                    tg.create_task(_worker(index))

        summary.wall_s = time.perf_counter() - started

    return summary
