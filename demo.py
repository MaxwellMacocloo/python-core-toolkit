"""Walk through every part of the toolkit.

    python demo.py
    python demo.py --section oop
    python demo.py --section generators
"""

import argparse
import sys
import time

from toolkit import mathops, shapes
from toolkit.bank import BankAccount, InsufficientFundsError, SavingsAccount
from toolkit.decorators import make_counter, make_multiplier, memoize, retry, timed
from toolkit.iterators import (
    Countdown, Repeater, chunked, countdown_gen, fibonacci_gen,
    memory_comparison, pipeline, take,
)


def banner(title):
    print()
    print("=" * 66)
    print(f"  {title}")
    print("=" * 66)


def section_packages():
    banner("PACKAGES AND SUBPACKAGES")
    print(f"  toolkit version: {mathops.__name__} via toolkit/__init__.py")
    print(f"  add(5, 10)     = {mathops.add(5, 10)}")
    print(f"  divide(10, 4)  = {mathops.divide(10, 4)}")
    print(f"  factorial(10)  = {mathops.factorial(10):,}")
    print(f"  gcd(48, 18)    = {mathops.gcd(48, 18)}")
    print(f"  lcm(4, 6)      = {mathops.lcm(4, 6)}")
    print(f"  primes < 30    = {mathops.primes_up_to(30)}")
    print()
    print("  __init__.py re-exports, so this works:")
    print("    from toolkit.mathops import factorial")
    print("  rather than:")
    print("    from toolkit.mathops.advanced import factorial")


def section_oop():
    banner("THE FOUR OOP PILLARS")

    print("  Abstraction: Shape() cannot be instantiated")
    try:
        shapes.Shape("nothing")
    except TypeError as error:
        print(f"    TypeError: {str(error)[:62]}")

    print()
    print("  Inheritance: Square -> Rectangle -> Shape -> ABC")
    print(f"    MRO: {' -> '.join(c.__name__ for c in shapes.Square.__mro__[:4])}")

    print()
    print("  Polymorphism: one loop, four different area() implementations")
    figures = [shapes.Circle(3), shapes.Rectangle(4, 5),
               shapes.Square(4), shapes.Triangle(3, 4, 5)]
    for figure in figures:
        print(f"    {figure}")
    print(f"    total area: {shapes.total_area(figures):.2f}")
    print(f"    largest   : {shapes.largest(figures)!r}")

    print()
    print("  Encapsulation: the property validates every assignment")
    circle = shapes.Circle(5)
    try:
        circle.radius = -1
    except ValueError as error:
        print(f"    ValueError: {error}")
    print(f"    radius unchanged: {circle.radius}")

    print()
    print("  Dunder methods")
    print(f"    Square(2) == Rectangle(1, 4) : {shapes.Square(2) == shapes.Rectangle(1, 4)}  (equal areas)")
    print(f"    repr(Circle(2.5))            : {shapes.Circle(2.5)!r}")
    print(f"    sorted by area               : {[type(s).__name__ for s in sorted(figures)]}")


def section_bank():
    banner("ENCAPSULATION AND CUSTOM EXCEPTIONS")

    account = BankAccount("Ama Mensah", 1000, overdraft_limit=200)
    print(f"  {account}")
    print(f"  available (balance + overdraft): {account.available:.2f}")

    account.deposit(500, note="salary")
    account.withdraw(1600, note="rent")
    print(f"  after deposit and overdrawn withdrawal: {account}")

    print()
    print("  The balance has no setter:")
    try:
        account.balance = 1_000_000
    except AttributeError as error:
        print(f"    AttributeError: {error}")

    print()
    print("  The exception carries structured data, not just a message:")
    try:
        BankAccount("Kofi", 100).withdraw(150)
    except InsufficientFundsError as error:
        print(f"    requested={error.requested} available={error.available} "
              f"shortfall={error.shortfall}")

    print()
    print("  A failed transfer leaves both accounts untouched:")
    source, target = BankAccount("Ama", 100), BankAccount("Kofi", 50)
    try:
        source.transfer_to(target, 500)
    except InsufficientFundsError:
        print(f"    source={source.balance:.2f} target={target.balance:.2f} (unchanged)")

    print()
    print("  Inheritance overrides the class attribute and adds a rule:")
    print(f"    BankAccount.interest_rate    = {BankAccount.interest_rate:.0%}")
    print(f"    SavingsAccount.interest_rate = {SavingsAccount.interest_rate:.0%}")
    savings = SavingsAccount("Yayra", 1000)
    savings.apply_interest()
    print(f"    after interest: {savings}")
    try:
        SavingsAccount("Nana", 150).withdraw(100)
    except InsufficientFundsError:
        print(f"    minimum balance of {SavingsAccount.minimum_balance:.0f} enforced")

    print()
    print(f"  len(account) = {len(account)} transactions")
    print(f"  bool(account) = {bool(account)} (balance-based, not history-based)")
    print("  transaction log:")
    for entry in list(account)[:3]:
        print(f"    {entry['kind']:<9} {entry['amount']:>9.2f} -> "
              f"{entry['balance']:>9.2f}  {entry['note']}")


def section_decorators():
    banner("DECORATORS AND CLOSURES")

    @timed
    def slow_sum(n):
        """Add up the first n integers."""
        return sum(range(n))

    slow_sum(1_000_000)
    print(f"  @timed: {slow_sum.__name__}() took {slow_sum.last_duration:.4f}s")
    print(f"  @functools.wraps kept the name and docstring:")
    print(f"    __name__ = {slow_sum.__name__!r}")
    print(f"    __doc__  = {slow_sum.__doc__!r}")

    print()
    attempts = {"n": 0}

    @retry(times=3)
    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise ConnectionError("transient")
        return "connected"

    print(f"  @retry(times=3): {flaky()} after {attempts['n']} attempts")

    print()
    print("  Memoisation on naive recursive Fibonacci:")
    mathops.fibonacci.clear_cache()
    mathops.fibonacci.hits = mathops.fibonacci.misses = 0

    start = time.perf_counter()
    value = mathops.fibonacci(35)
    elapsed = time.perf_counter() - start

    print(f"    fibonacci(35) = {value:,} in {elapsed:.6f}s")
    print(f"    cache: {mathops.fibonacci.misses} misses, {mathops.fibonacci.hits} hits")
    print(f"    without the cache this is O(2^n): about 30 million calls")

    print()
    print("  Closures keep their own state:")
    counter, other = make_counter(), make_counter(100)
    print(f"    counter(): {[counter() for _ in range(3)]}")
    print(f"    a second counter is independent: {other()}")
    double, triple = make_multiplier(2), make_multiplier(3)
    print(f"    make_multiplier(2)(5) = {double(5)}, (3)(5) = {triple(5)}")


def section_generators():
    banner("ITERATORS AND GENERATORS")

    print("  A hand-written iterator (14 lines):")
    print(f"    list(Countdown(5)) = {list(Countdown(5))}")

    print()
    print("  The same thing as a generator (5 lines):")
    print(f"    list(countdown_gen(5)) = {list(countdown_gen(5))}")

    print()
    print("  An iterator is exhausted after one pass:")
    countdown = Countdown(3)
    print(f"    first pass : {list(countdown)}")
    print(f"    second pass: {list(countdown)}  <- empty")

    print()
    print("  An iterable returning a fresh generator can be reused:")
    repeater = Repeater("x", 3)
    print(f"    first pass : {list(repeater)}")
    print(f"    second pass: {list(repeater)}  <- still works")

    print()
    print("  An infinite generator is safe when consumed lazily:")
    print(f"    take(fibonacci_gen(), 12) = {take(fibonacci_gen(), 12)}")

    print()
    print("  Chained generators stay lazy; no intermediate list is built:")
    print(f"    pipeline(range(10)) = {list(pipeline(range(10)))}")

    print()
    print(f"  chunked(range(7), 3) = {list(chunked(range(7), 3))}")

    print()
    print("  Memory: a list holds results, a generator holds a recipe")
    for size in (1_000, 100_000):
        result = memory_comparison(size)
        print(f"    {size:>7,} items: list {result['list_bytes']:>9,} bytes  "
              f"generator {result['generator_bytes']:>3} bytes  "
              f"({result['ratio']:>6,.0f}x)")
    print("    The generator does not grow. That is the whole point.")


def section_exceptions():
    banner("EXCEPTION HANDLING")

    print("  A specific handler before a general one:")
    for a, b in [(10, 2), (10, 0)]:
        try:
            print(f"    divide({a}, {b}) = {mathops.divide(a, b)}")
        except ZeroDivisionError as error:
            print(f"    ZeroDivisionError: {error}")

    print()
    print("  try / except / else / finally, in execution order:")
    for value in ("42", "abc"):
        print(f"    parsing {value!r}")
        try:
            number = int(value)
        except ValueError as error:
            print(f"      except : {error}")
        else:
            print(f"      else   : parsed {number} (runs only when nothing raised)")
        finally:
            print(f"      finally: always runs")

    print()
    print("  A custom exception hierarchy lets callers choose how specific")
    print("  to be: 'except InsufficientFundsError' for one case, or")
    print("  'except BankError' for anything from the module.")


SECTIONS = {
    "packages": section_packages,
    "oop": section_oop,
    "bank": section_bank,
    "decorators": section_decorators,
    "generators": section_generators,
    "exceptions": section_exceptions,
}


def main():
    parser = argparse.ArgumentParser(description="toolkit demo")
    parser.add_argument("--section", choices=sorted(SECTIONS),
                        help="run only one section")
    args = parser.parse_args()

    if args.section:
        SECTIONS[args.section]()
    else:
        for run in SECTIONS.values():
            run()

    print()


if __name__ == "__main__":
    main()
