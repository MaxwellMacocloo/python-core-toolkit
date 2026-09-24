"""Tests for the mathops subpackage."""

import pytest

from toolkit import mathops
from toolkit.mathops import advanced, basic


# ------------------------------------------------------------------- basic

@pytest.mark.parametrize("a,b,expected", [(2, 3, 5), (-1, 1, 0), (0, 0, 0), (2.5, 2.5, 5.0)])
def test_add(a, b, expected):
    assert basic.add(a, b) == expected


def test_subtract_and_multiply():
    assert basic.subtract(10, 4) == 6
    assert basic.multiply(6, 7) == 42


def test_divide():
    assert basic.divide(10, 4) == 2.5


def test_divide_by_zero_raises_with_a_useful_message():
    with pytest.raises(ZeroDivisionError, match="cannot divide 10 by zero"):
        basic.divide(10, 0)


def test_power():
    assert basic.power(2, 10) == 1024
    assert basic.power(9, 0.5) == 3.0


def test_average():
    assert basic.average([1, 2, 3, 4]) == 2.5
    assert basic.average(range(1, 101)) == 50.5


def test_average_of_empty_raises():
    """Returning 0 would hide the caller's bug."""
    with pytest.raises(ValueError, match="empty sequence"):
        basic.average([])


# ---------------------------------------------------------------- factorial

@pytest.mark.parametrize("n,expected", [(0, 1), (1, 1), (5, 120), (10, 3628800)])
def test_factorial(n, expected):
    assert advanced.factorial(n) == expected


def test_factorial_rejects_negative():
    with pytest.raises(ValueError, match="undefined for negative"):
        advanced.factorial(-1)


def test_factorial_rejects_non_integer():
    with pytest.raises(TypeError, match="must be an integer"):
        advanced.factorial(3.5)


def test_factorial_handles_large_input_without_recursion_error():
    """A recursive implementation would blow the 1000-frame stack here.

    Printing the result needs one extra step: since 3.11, Python refuses
    int-to-string conversions beyond 4300 digits as a denial-of-service
    guard, and 2000! has 5736 of them. The arithmetic is never the
    problem -- only rendering it as text.
    """
    import sys

    result = advanced.factorial(2000)
    assert result > 0

    with pytest.raises(ValueError, match="Exceeds the limit"):
        str(result)

    sys.set_int_max_str_digits(10_000)
    try:
        assert len(str(result)) == 5736
    finally:
        sys.set_int_max_str_digits(4300)  # restore the default


# --------------------------------------------------------------- fibonacci

@pytest.mark.parametrize("n,expected", [
    (0, 0), (1, 1), (2, 1), (3, 2), (10, 55), (20, 6765), (50, 12586269025),
])
def test_fibonacci(n, expected):
    assert advanced.fibonacci(n) == expected


def test_fibonacci_is_memoised():
    """Without the cache, fib(30) is roughly 2.7 million calls."""
    advanced.fibonacci.clear_cache()
    advanced.fibonacci.hits = 0
    advanced.fibonacci.misses = 0

    advanced.fibonacci(30)

    # 31 distinct subproblems (0..30), each computed exactly once.
    assert advanced.fibonacci.misses == 31

    # Every n >= 2 makes two recursive calls: fib(n-1) misses the cache
    # the first time, fib(n-2) is already in it. That is 29 values of n
    # (2..30) contributing one hit each, minus the single top-level call
    # that started as a miss -- 28 hits, 59 calls in total.
    assert advanced.fibonacci.hits == 28
    assert advanced.fibonacci.hits + advanced.fibonacci.misses == 59


def test_fibonacci_rejects_negative():
    with pytest.raises(ValueError):
        advanced.fibonacci(-5)


# ------------------------------------------------------------- number theory

@pytest.mark.parametrize("a,b,expected", [
    (12, 18, 6), (48, 18, 6), (17, 5, 1), (0, 5, 5), (-12, 18, 6),
])
def test_gcd(a, b, expected):
    assert advanced.gcd(a, b) == expected


@pytest.mark.parametrize("a,b,expected", [(4, 6, 12), (3, 5, 15), (0, 5, 0)])
def test_lcm(a, b, expected):
    assert advanced.lcm(a, b) == expected


def test_gcd_lcm_identity():
    """gcd(a,b) * lcm(a,b) == a * b, for positive integers."""
    for a, b in [(12, 18), (8, 20), (7, 13)]:
        assert advanced.gcd(a, b) * advanced.lcm(a, b) == a * b


@pytest.mark.parametrize("n,expected", [
    (0, False), (1, False), (2, True), (3, True), (4, False),
    (17, True), (25, False), (97, True), (7919, True), (7920, False),
])
def test_is_prime(n, expected):
    assert advanced.is_prime(n) is expected


def test_primes_up_to():
    assert advanced.primes_up_to(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    assert advanced.primes_up_to(2) == []
    assert advanced.primes_up_to(0) == []


def test_sieve_agrees_with_trial_division():
    """Two independent implementations must produce the same answer."""
    sieved = advanced.primes_up_to(1000)
    by_trial = [n for n in range(1000) if advanced.is_prime(n)]
    assert sieved == by_trial


def test_prime_counting_function():
    # There are 168 primes below 1000, and 1229 below 10000.
    assert len(advanced.primes_up_to(1000)) == 168
    assert len(advanced.primes_up_to(10_000)) == 1229


# ------------------------------------------------------------------ package

def test_subpackage_reexports_flatten_the_import_path():
    """__init__.py re-exports, so callers skip the module name."""
    assert mathops.factorial is advanced.factorial
    assert mathops.add is basic.add


def test_all_declares_the_public_surface():
    for name in mathops.__all__:
        assert hasattr(mathops, name), f"{name} in __all__ but not defined"
