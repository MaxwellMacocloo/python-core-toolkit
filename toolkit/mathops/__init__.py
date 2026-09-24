"""The mathops subpackage.

__init__.py turns a directory into a package. Re-exporting the useful
names here means callers write

    from toolkit.mathops import factorial

instead of

    from toolkit.mathops.advanced import factorial

so the module layout can change without breaking every import site.
"""

from .advanced import factorial, fibonacci, gcd, is_prime, lcm, primes_up_to
from .basic import add, average, divide, multiply, power, subtract

__all__ = [
    "add", "subtract", "multiply", "divide", "power", "average",
    "factorial", "fibonacci", "gcd", "lcm", "is_prime", "primes_up_to",
]
