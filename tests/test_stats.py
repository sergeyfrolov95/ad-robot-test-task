"""Unit tests for pure metric logic in netspeed.stats."""

import pytest

from netspeed.stats import RequestResult, RunSummary


def _result(
    index: int,
    elapsed_s: float,
    bytes_count: int = 1_000_000,
    error: str | None = None,
) -> RequestResult:
    return RequestResult(
        index=index,
        status=None if error else 200,
        bytes=bytes_count,
        elapsed_s=elapsed_s,
        error=error,
    )


class TestRequestResult:
    def test_mb_per_s_and_mbit_per_s(self) -> None:
        result = _result(index=0, elapsed_s=1.0, bytes_count=1_000_000)

        assert result.mb_per_s == pytest.approx(1.0)
        assert result.mbit_per_s == pytest.approx(8.0)

    def test_zero_elapsed_is_safe(self) -> None:
        result = _result(index=0, elapsed_s=0.0, bytes_count=1_000_000)

        assert result.mb_per_s == 0.0
        assert result.mbit_per_s == 0.0


class TestRunSummary:
    def test_ok_failed_split(self) -> None:
        summary = RunSummary(
            results=[
                _result(0, 1.0),
                _result(1, 2.0, error='TimeoutError: '),
                _result(2, 3.0),
            ]
        )

        assert [r.index for r in summary.ok] == [0, 2]
        assert [r.index for r in summary.failed] == [1]
        assert summary.total_bytes == 2_000_000

    def test_mean_elapsed_s(self) -> None:
        summary = RunSummary(results=[_result(0, 1.0), _result(1, 2.0), _result(2, 6.0)])

        assert summary.mean_elapsed_s == pytest.approx(3.0)

    def test_mean_elapsed_s_empty(self) -> None:
        assert RunSummary().mean_elapsed_s == 0.0

    def test_median_odd(self) -> None:
        summary = RunSummary(results=[_result(0, 1.0), _result(1, 2.0), _result(2, 6.0)])

        assert summary.median_elapsed_s == pytest.approx(2.0)

    def test_median_even(self) -> None:
        summary = RunSummary(
            results=[_result(0, 1.0), _result(1, 2.0), _result(2, 4.0), _result(3, 8.0)]
        )

        assert summary.median_elapsed_s == pytest.approx(3.0)

    def test_median_empty(self) -> None:
        assert RunSummary().median_elapsed_s == 0.0

    def test_mean_speed_mbit_per_s(self) -> None:
        summary = RunSummary(results=[_result(0, 1.0, 1_000_000), _result(1, 2.0, 1_000_000)])

        assert summary.mean_speed_mbit_per_s == pytest.approx((8.0 + 4.0) / 2)

    def test_aggregate_mbit_per_s(self) -> None:
        summary = RunSummary(results=[_result(0, 1.0, 1_000_000), _result(1, 1.0, 1_000_000)])
        summary.wall_s = 1.0

        assert summary.aggregate_mbit_per_s == pytest.approx(16.0)

    def test_aggregate_zero_wall_safe(self) -> None:
        summary = RunSummary(results=[_result(0, 1.0, 1_000_000)])
        summary.wall_s = 0.0

        assert summary.aggregate_mbit_per_s == 0.0
