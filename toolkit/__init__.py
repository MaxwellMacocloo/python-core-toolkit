"""A toolkit of Python core-language patterns.

    from toolkit import mathops, shapes
    from toolkit.bank import BankAccount
    from toolkit.decorators import memoize, retry, timed
    from toolkit.iterators import fibonacci_gen, chunked

Subpackages
    mathops   arithmetic, recursion, number theory
    shapes    abstract base classes and polymorphism

Modules
    bank        encapsulation, custom exception hierarchies
    decorators  decorators, parameterised decorators, closures
    iterators   the iterator protocol, generators, lazy pipelines
    fileops     file I/O, CSV, JSON, a hand-written context manager
"""

__version__ = "1.0.0"

from . import bank, decorators, fileops, iterators, mathops, shapes

__all__ = ["mathops", "shapes", "bank", "decorators", "iterators", "fileops"]
