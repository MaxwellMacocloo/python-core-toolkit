"""Decorators, closures, and why functools.wraps matters."""

import functools
import time


def timed(func):
    """Record how long a call took on the wrapper itself.

    @functools.wraps copies __name__, __doc__, __module__ and
    __qualname__ from the wrapped function onto the wrapper. Without it,
    every decorated function reports itself as 'wrapper', which breaks
    help(), pdb tracebacks, and any tool that introspects names.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        wrapper.last_duration = time.perf_counter() - start
        wrapper.call_count += 1
        return result

    wrapper.call_count = 0
    wrapper.last_duration = None
    return wrapper


def retry(times=3, exceptions=(Exception,), delay=0.0):
    """A decorator that takes arguments, so it needs three nested levels.

    retry(times=3) is called first and returns the actual decorator,
    which then receives the function. That is why a parameterised
    decorator is a function returning a function returning a function.
    """
    if times < 1:
        raise ValueError("times must be at least 1")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as error:
                    last_error = error
                    wrapper.attempts = attempt
                    if attempt < times and delay:
                        time.sleep(delay)
            raise last_error

        wrapper.attempts = 0
        return wrapper
    return decorator


def memoize(func):
    """Cache results by arguments.

    The cache lives in the closure, not in a global. Each decorated
    function gets its own, and it stays alive because `wrapper` holds a
    reference to the enclosing scope.
    """
    cache = {}

    @functools.wraps(func)
    def wrapper(*args):
        if args in cache:
            wrapper.hits += 1
            return cache[args]

        wrapper.misses += 1
        cache[args] = func(*args)
        return cache[args]

    wrapper.hits = 0
    wrapper.misses = 0
    wrapper.cache = cache
    wrapper.clear_cache = cache.clear
    return wrapper


def validate_positive(*arg_names):
    """Reject non-positive arguments, by parameter name.

    Uses inspect.signature to bind the call, so it works whether the
    caller passes arguments positionally or by keyword.
    """
    import inspect

    def decorator(func):
        signature = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()

            for name in arg_names:
                if name in bound.arguments:
                    value = bound.arguments[name]
                    if value <= 0:
                        raise ValueError(f"{name} must be positive, got {value}")

            return func(*args, **kwargs)
        return wrapper
    return decorator


def call_logger(log_list):
    """Append a record of every call to a caller-supplied list.

    Demonstrates a closure over a mutable argument: the decorator does
    not own the list, so a test can inspect what happened.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log_list.append(f"{func.__name__}({args}, {kwargs})")
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ------------------------------------------------------------- closures

def make_counter(start=0):
    """Return a counter function holding its own state.

    `nonlocal` is what makes this work: without it, `count += 1` would
    create a new local variable instead of rebinding the enclosing one,
    and you would get an UnboundLocalError.
    """
    count = start

    def counter():
        nonlocal count
        count += 1
        return count

    def reset():
        nonlocal count
        count = start

    counter.reset = reset
    return counter


def make_multiplier(factor):
    """The classic closure: `factor` outlives the call that created it."""
    def multiply(value):
        return value * factor
    return multiply


def make_accumulator():
    """A closure over a list, keeping a running total."""
    values = []

    def accumulate(value):
        values.append(value)
        return sum(values)

    accumulate.values = values
    return accumulate
