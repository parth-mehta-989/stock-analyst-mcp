"""Thread-pool helpers for parallelizing I/O-bound work.

Benchmarked: 5 sequential yfinance get_info() calls take 2.80s;
ThreadPoolExecutor brings that to 0.76s (3.7x speedup).
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")

_DEFAULT_WORKERS = 8


def parallel_map(
    fn: Callable[[T], R],
    items: List[T],
    max_workers: int = _DEFAULT_WORKERS,
    label: str = "",
) -> List[R]:
    """Apply *fn* to each item in parallel, returning results in input order.

    Failed items are silently skipped (logged at DEBUG).
    """
    if not items:
        return []
    workers = min(max_workers, len(items))
    results: List[R | None] = [None] * len(items)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_idx = {pool.submit(fn, item): idx for idx, item in enumerate(items)}
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                logger.debug("parallel_map %s item %s failed: %s", label, items[idx], e)

    return [r for r in results if r is not None]


def parallel_map_dict(
    fn: Callable[[T], R],
    items: List[T],
    max_workers: int = _DEFAULT_WORKERS,
    label: str = "",
) -> Dict[T, R]:
    """Apply *fn* to each item in parallel, returning {item: result} dict.

    Failed items are omitted from the dict (logged at DEBUG).
    """
    if not items:
        return {}
    workers = min(max_workers, len(items))
    out: Dict[T, R] = {}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_item = {pool.submit(fn, item): item for item in items}
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                out[item] = future.result()
            except Exception as e:
                logger.debug("parallel_map_dict %s key %s failed: %s", label, item, e)

    return out
