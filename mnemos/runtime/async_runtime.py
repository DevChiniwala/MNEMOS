# -*- coding: utf-8 -*-
"""Concurrent execution utilities for I/O bound operations."""

import concurrent.futures
from typing import Callable, Iterable, List, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def run_concurrently(
    func: Callable[[T], R],
    items: Iterable[T],
    max_workers: int = 4,
) -> List[R]:
    """Run a function concurrently over a list of items using thread pool."""
    results: List[R] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(func, item) for item in items]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    return results
