# Python Core Toolkit

An installable package covering the core language: packages and
subpackages, the four OOP pillars, decorators and closures, the iterator
protocol, generators, custom exception hierarchies, and file I/O.

**140 passing tests.**

```bash
pip install -r requirements.txt
python demo.py                      # walk through everything
python demo.py --section generators # one section
pytest -v                           # 140 tests
```

## Layout

```
python-core-toolkit/
├── demo.py                      runnable walkthrough, six sections
├── toolkit/
│   ├── __init__.py              package docstring + re-exports
│   ├── bank.py                  encapsulation, exception hierarchy
│   ├── decorators.py            decorators, parameterised decorators, closures
│   ├── iterators.py             iterator protocol, generators, lazy pipelines
│   ├── fileops.py               file I/O, CSV, JSON, context manager
│   ├── mathops/                 subpackage
│   │   ├── __init__.py          re-exports from basic + advanced
│   │   ├── basic.py             arithmetic
│   │   └── advanced.py          recursion, number theory
│   └── shapes/                  subpackage
│       ├── __init__.py
│       └── base.py              ABC + four concrete shapes
└── tests/                       140 tests in 3 files
```

## The four OOP pillars

Each one is demonstrated by something that actually fails when violated.

**Abstraction** — `Shape` is an `ABC` with `@abstractmethod`. Instantiating
it raises, and so does a subclass that forgets a method:

```python
Shape("nothing")
# TypeError: Can't instantiate abstract class Shape without an implementation...

class Blob(Shape):
    def area(self): return 1.0
    # perimeter() missing

Blob("blob")   # TypeError as well — caught at instantiation, not at call time
```

**Inheritance** — two levels deep:

```python
Square.__mro__   # Square -> Rectangle -> Shape -> ABC -> object
```

`Square` passes one side as both dimensions, so it inherits `area()` and
`perimeter()` unchanged.

**Polymorphism** — `total_area` never checks a type:

```python
def total_area(shapes):
    return sum(shape.area() for shape in shapes)
```

A test defines a brand-new `Hexagon` class inside the test body and
`total_area` handles it with no edit. That is the property worth testing.

**Encapsulation** — a validating property over a private attribute:

```python
circle = Circle(5)
circle.radius = -1
# ValueError: radius must be positive, got -1
assert circle.radius == 5.0      # the failed assignment changed nothing
```

The setter runs for the assignment inside `__init__` too, so `Circle(0)`
fails at construction. A bare public attribute cannot do that.

## The bank account

`balance` is a property with **no setter**, so money can only move through
`deposit()` and `withdraw()`, which validate and record:

```python
account.balance = 1_000_000
# AttributeError: property 'balance' of 'BankAccount' object has no setter
```

`history` returns a **copy**, so a caller cannot rewrite the ledger.

The exception carries structured data rather than making callers parse a
message string:

```python
except InsufficientFundsError as error:
    error.requested   # 150
    error.available   # 100
    error.shortfall   # 50
```

A three-level hierarchy (`BankError` → `InsufficientFundsError`) lets
callers pick their specificity: catch one case, or anything from the
module.

`transfer_to` withdraws before depositing and reverses itself if the
destination refuses, so a half-completed transfer cannot create money.
There is a test asserting both balances are untouched after a failure.

Two dunder methods worth noting:

```python
def __len__(self):  return len(self._history)   # transaction count
def __bool__(self): return self._balance > 0    # has money
```

Without `__bool__`, `__len__` would decide truthiness, and an account
with a full history but zero balance would read as truthy.

## Decorators

| Decorator | Shows |
|---|---|
| `@timed` | `functools.wraps`; state stored on the wrapper |
| `@retry(times=3)` | A decorator taking arguments — three nested levels |
| `@memoize` | A cache living in the closure, not a global |
| `@validate_positive("width")` | `inspect.signature` to bind args by name |
| `@call_logger(log)` | A closure over a caller-supplied mutable |

**Why `functools.wraps` matters**, with a test to prove it:

```python
@timed
def compute_total(values):
    """Add up some values."""
    return sum(values)

compute_total.__name__   # 'compute_total', not 'wrapper'
compute_total.__doc__    # 'Add up some values.'
```

Without it every decorated function reports itself as `wrapper`, which
breaks `help()`, pdb tracebacks, and anything that introspects names.

**Why a parameterised decorator needs three levels**: `retry(times=3)` is
called first and returns the decorator, which then receives the function.
So it is a function returning a function returning a function.

**`@validate_positive` binds by signature**, so it works whether the
caller passes positionally or by keyword, and it checks defaults too:

```python
@validate_positive("width", "height")
def area(width, height=1): ...

area(-3, 4)          # ValueError: width must be positive
area(3, height=0)    # ValueError: height must be positive
```

**Memoisation, measured**: naive recursive `fibonacci(35)` is O(2^n) —
roughly 30 million calls. With `@memoize` it returns in 42 microseconds
from 36 cache misses. A test pins the exact hit/miss counts for
`fibonacci(30)`: **31 misses, 28 hits, 59 calls total**, because each
`n >= 2` misses on `fib(n-1)` and hits on `fib(n-2)`.

**Closures and `nonlocal`**:

```python
def make_counter(start=0):
    count = start
    def counter():
        nonlocal count      # without this: UnboundLocalError
        count += 1
        return count
    return counter
```

`count += 1` without `nonlocal` would create a new local instead of
rebinding the enclosing one.

## Iterators and generators

**The protocol by hand** — `__iter__` returns self, `__next__` returns a
value or raises `StopIteration`. A `for` loop is exactly this plus a
try/except.

**Iterator vs iterable**, the distinction that trips people up:

```python
countdown = Countdown(3)     # __iter__ returns self
list(countdown)              # [3, 2, 1, 0]
list(countdown)              # []  <- exhausted, permanently

repeater = Repeater("x", 3)  # __iter__ returns a fresh generator
list(repeater)               # ['x', 'x', 'x']
list(repeater)               # ['x', 'x', 'x']  <- still works
```

**A generator does the same job in a third of the code**, because `yield`
keeps state in the frame automatically — no `self.current` to manage.

**Memory is the real argument for generators:**

| Items | List | Generator | Ratio |
|---|---|---|---|
| 1,000 | 8,856 bytes | 200 bytes | 44x |
| 100,000 | 800,984 bytes | 200 bytes | **4,005x** |

The generator does not grow. It stores a recipe, not results. A test
asserts the list grows 50x+ between those two sizes while the generator
stays byte-identical.

**An infinite generator is safe when consumed lazily:**

```python
take(fibonacci_gen(), 12)   # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
```

`fibonacci_gen()` with no limit never terminates, which is fine because
nothing is computed until something pulls.

## A context manager written by hand

```python
class ManagedFile:
    def __enter__(self):
        self.handle = open(self.path, self.mode)
        return self.handle

    def __exit__(self, exc_type, exc_value, traceback):
        if self.handle:
            self.handle.close()
        return False   # never suppress the exception
```

`__exit__` runs on the error path too — that is the entire point of
`with`. Returning `False` lets the exception propagate; returning `True`
would swallow it. There is a test for each case.

## Two Python behaviours worth knowing

**`bool` is a subclass of `int`.** `BankAccount.deposit(True)` would
otherwise add 1.00 to the balance, so the validator excludes it
explicitly:

```python
if not isinstance(amount, (int, float)) or isinstance(amount, bool):
    raise InvalidAmountError(...)
```

**Python refuses huge int-to-string conversions.** Since 3.11 there is a
4300-digit cap as a denial-of-service guard, and `2000!` has 5736 digits:

```python
result = factorial(2000)     # fine — the arithmetic is never the problem
str(result)                  # ValueError: Exceeds the limit (4300 digits)

sys.set_int_max_str_digits(10_000)
len(str(result))             # 5736
```

Only rendering it as text is restricted.

`factorial` is also iterative rather than recursive: Python's default
recursion limit is 1000 frames, so a recursive version raises
`RecursionError` on inputs a loop handles without trouble.

## Why `__init__.py` re-exports

```python
from toolkit.mathops import factorial            # what callers write
from toolkit.mathops.advanced import factorial   # what it maps to
```

The module layout can change without breaking every import site. A test
asserts `mathops.factorial is advanced.factorial`, and another checks
every name in `__all__` actually exists.

## Test breakdown

| File | Tests | Covers |
|---|---|---|
| `tests/test_mathops.py` | 50 | arithmetic, recursion, number theory, package structure |
| `tests/test_oop.py` | 46 | abstraction, inheritance, polymorphism, encapsulation, dunders, bank |
| `tests/test_decorators_iterators.py` | 44 | decorators, closures, iterators, generators, file I/O |

Two independent implementations cross-check each other: the Sieve of
Eratosthenes and trial division must agree on every prime below 1000.
Similarly `gcd(a,b) * lcm(a,b) == a * b` is asserted as an identity rather
than against hardcoded values.
