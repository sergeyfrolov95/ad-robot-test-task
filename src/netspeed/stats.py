"""Aggregated metrics for a benchmark run."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class RequestResult:
    """Outcome of a single download request."""

    index: int
    status: int | None
    bytes: int
    elapsed_s: float
    error: str | None = None

    @property
    def mb_per_s(self) -> float:
        """Throughput in MB/s (10^6 bytes per second)."""
        if self.elapsed_s <= 0:
            return 0.0
        return self.bytes / self.elapsed_s / 1_000_000

    @property
    def mbit_per_s(self) -> float:
        """Throughput in Mbit/s."""
        return self.mb_per_s * 8


@dataclass(slots=True)
class RunSummary:
    """Aggregated results of a benchmark run."""

    results: list[RequestResult] = field(default_factory=list)
    wall_s: float = 0.0

    @property
    def ok(self) -> list[RequestResult]:
        return [r for r in self.results if r.error is None]

    @property
    def failed(self) -> list[RequestResult]:
        return [r for r in self.results if r.error is not None]

    @property
    def total_bytes(self) -> int:
        return sum(r.bytes for r in self.ok)

    @property
    def mean_elapsed_s(self) -> float:
        ok = self.ok
        if not ok:
            return 0.0
        return sum(r.elapsed_s for r in ok) / len(ok)

    @property
    def median_elapsed_s(self) -> float:
        times = sorted(r.elapsed_s for r in self.ok)
        if not times:
            return 0.0
        mid = len(times) // 2
        if len(times) % 2:
            return times[mid]
        return (times[mid - 1] + times[mid]) / 2

    @property
    def mean_speed_mbit_per_s(self) -> float:
        """Average per-request throughput across successful requests, Mbit/s."""
        ok = self.ok
        if not ok:
            return 0.0
        return sum(r.mbit_per_s for r in ok) / len(ok)

    @property
    def aggregate_mbit_per_s(self) -> float:
        """Channel throughput: all successful bytes over the run wall time, Mbit/s.

        Equals per-request speed in sequential mode; the honest figure when
        requests run in parallel.
        """
        if self.wall_s <= 0:
            return 0.0
        return self.total_bytes * 8 / self.wall_s / 1_000_000
