"""Integration tests for netspeed.client against a local aiohttp test server."""

from collections.abc import AsyncIterator

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from netspeed.client import run_benchmark


def _payload(size_bytes: int) -> bytes:
    return b'x' * size_bytes


@pytest.fixture
async def server() -> AsyncIterator[TestServer]:
    async def handler_ok(request: web.Request) -> web.Response:
        return web.Response(body=_payload(10_000))

    async def handler_not_found(request: web.Request) -> web.Response:
        return web.Response(status=404, body=_payload(100))

    app = web.Application()
    app.router.add_get('/ok', handler_ok)
    app.router.add_get('/missing', handler_not_found)

    test_server = TestServer(app)
    await test_server.start_server()
    yield test_server
    await test_server.close()


async def test_download_counts_bytes_and_status(server: TestServer) -> None:
    summary = await run_benchmark(
        url=f'{server.make_url("/ok")}',
        requests=3,
        concurrency=1,
        timeout_s=10.0,
    )

    assert len(summary.results) == 3
    assert all(r.status == 200 for r in summary.results)
    assert all(r.bytes == 10_000 for r in summary.results)
    assert all(r.error is None for r in summary.results)
    assert summary.total_bytes == 30_000


async def test_on_result_fires_for_each_request(server: TestServer) -> None:
    seen: list[int] = []

    await run_benchmark(
        url=f'{server.make_url("/ok")}',
        requests=4,
        concurrency=1,
        timeout_s=10.0,
        on_result=lambda r: seen.append(r.index),
    )

    assert sorted(seen) == [0, 1, 2, 3]


async def test_warmup_excluded_from_results(server: TestServer) -> None:
    summary = await run_benchmark(
        url=f'{server.make_url("/ok")}',
        requests=2,
        concurrency=1,
        timeout_s=10.0,
        warmup=2,
    )

    assert [r.index for r in summary.results] == [0, 1]
    assert summary.total_bytes == 20_000


async def test_http_error_recorded_as_failure(server: TestServer) -> None:
    summary = await run_benchmark(
        url=f'{server.make_url("/missing")}',
        requests=1,
        concurrency=1,
        timeout_s=10.0,
    )

    assert len(summary.failed) == 1
    assert summary.ok == []
    assert summary.results[0].status is None
    assert summary.results[0].error is not None
    assert '404' in summary.results[0].error


async def test_parallel_mode_collects_all_results(server: TestServer) -> None:
    summary = await run_benchmark(
        url=f'{server.make_url("/ok")}',
        requests=5,
        concurrency=3,
        timeout_s=10.0,
    )

    assert len(summary.results) == 5
    assert sorted(r.index for r in summary.results) == [0, 1, 2, 3, 4]
    assert summary.wall_s > 0
