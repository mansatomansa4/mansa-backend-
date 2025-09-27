import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache_between_tests():
    """Ensure throttle counters (stored in cache) don't leak between tests.

    DRF's SimpleRateThrottle stores state in the default cache. Without clearing,
    an earlier test that exhausts a rate (e.g. anon throttle) can cause later
    unrelated tests to unexpectedly receive HTTP 429 responses.
    """
    cache.clear()
    yield
    cache.clear()
