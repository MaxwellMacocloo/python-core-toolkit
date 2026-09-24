"""Basic arithmetic, with the error handling the course covered."""


def add(a, b):
    """Return the sum of two numbers."""
    return a + b


def subtract(a, b):
    """Return a minus b."""
    return a - b


def multiply(a, b):
    """Return the product of two numbers."""
    return a * b


def divide(a, b):
    """Return a divided by b.

    Raises ZeroDivisionError with a clearer message than the built-in one.
    Catching and re-raising loses nothing here because the caller still
    gets a ZeroDivisionError.
    """
    if b == 0:
        raise ZeroDivisionError(f"cannot divide {a} by zero")
    return a / b


def power(base, exponent):
    return base ** exponent


def average(numbers):
    """Return the arithmetic mean.

    An empty sequence raises rather than returning 0: the average of
    nothing is undefined, and returning 0 would hide the caller's bug.
    """
    values = list(numbers)
    if not values:
        raise ValueError("cannot average an empty sequence")
    return sum(values) / len(values)
