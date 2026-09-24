"""Recursive and number-theoretic functions."""

from ..decorators import memoize


def factorial(n):
    """Return n! iteratively.

    Iteration rather than recursion because Python's recursion limit is
    1000 by default, so a recursive version raises RecursionError on
    inputs a loop handles without trouble.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError(f"n must be an integer, got {type(n).__name__}")
    if n < 0:
        raise ValueError(f"factorial is undefined for negative n, got {n}")

    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


@memoize
def fibonacci(n):
    """Return the nth Fibonacci number, memoised.

    Naive recursion here is O(2^n) -- fib(35) makes about 30 million
    calls. The memoize decorator makes it O(n) by caching each result, so
    every subproblem is solved once.
    """
    if n < 0:
        raise ValueError("n must not be negative")
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def gcd(a, b):
    """Greatest common divisor, by Euclid's algorithm."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def lcm(a, b):
    """Lowest common multiple."""
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // gcd(a, b)


def is_prime(n):
    """Trial division up to the square root."""
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 2
    return True


def primes_up_to(limit):
    """Sieve of Eratosthenes: every prime below `limit`."""
    if limit < 2:
        return []

    sieve = [True] * limit
    sieve[0] = sieve[1] = False

    for n in range(2, int(limit ** 0.5) + 1):
        if sieve[n]:
            # Start at n*n: smaller multiples already have a smaller factor.
            for multiple in range(n * n, limit, n):
                sieve[multiple] = False

    return [n for n, prime in enumerate(sieve) if prime]
