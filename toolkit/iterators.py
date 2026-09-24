"""Iterators and generators, and the memory difference between them."""

import sys


class Countdown:
    """A custom iterator implementing the protocol by hand.

    Two methods make an iterator: __iter__ returns self, __next__ returns
    the next value or raises StopIteration. A for loop is exactly this
    protocol plus a try/except around StopIteration.
    """

    def __init__(self, start):
        if start < 0:
            raise ValueError("start must not be negative")
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current < 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value


class Fibonacci:
    """An iterator with a bound, so it terminates."""

    def __init__(self, limit):
        self.limit = limit
        self.count = 0
        self.a, self.b = 0, 1

    def __iter__(self):
        return self

    def __next__(self):
        if self.count >= self.limit:
            raise StopIteration
        value = self.a
        self.a, self.b = self.b, self.a + self.b
        self.count += 1
        return value


class Repeater:
    """An *iterable* that is not an iterator.

    __iter__ returns a fresh generator each call, so the object can be
    looped over repeatedly. Countdown above cannot: once exhausted it
    stays exhausted, because it returns itself.
    """

    def __init__(self, value, times):
        self.value = value
        self.times = times

    def __iter__(self):
        for _ in range(self.times):
            yield self.value


# ----------------------------------------------------------- generators

def countdown_gen(start):
    """The same countdown as a generator: five lines instead of fourteen.

    `yield` makes the function return a generator. State is held in the
    frame automatically, so there is no self.current to manage.
    """
    while start >= 0:
        yield start
        start -= 1


def fibonacci_gen(limit=None):
    """Fibonacci numbers, optionally infinite.

    With limit=None this never terminates, which is safe because a
    generator computes on demand. Pair it with itertools.islice to take a
    finite slice.
    """
    a, b = 0, 1
    count = 0
    while limit is None or count < limit:
        yield a
        a, b = b, a + b
        count += 1


def read_in_chunks(path, chunk_size=1024):
    """Yield a file in fixed-size chunks.

    The reason generators matter for files: this holds one chunk in memory
    regardless of file size. `open(path).read()` holds the whole thing.
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            yield chunk


def read_lines(path):
    """Yield stripped, non-empty lines from a file."""
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                yield stripped


def take(iterable, count):
    """Take the first `count` items from any iterable, lazily.

    Works on infinite generators, which is why it cannot just slice.
    """
    result = []
    iterator = iter(iterable)
    for _ in range(count):
        try:
            result.append(next(iterator))
        except StopIteration:
            break
    return result


def chunked(iterable, size):
    """Group an iterable into lists of `size`, the last one possibly short."""
    if size < 1:
        raise ValueError("size must be at least 1")

    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def pipeline(numbers):
    """Chained generator expressions: each stage is lazy.

    Nothing is computed until the result is iterated, and no intermediate
    list is ever built.
    """
    squared = (n * n for n in numbers)
    evens = (n for n in squared if n % 2 == 0)
    return (n + 1 for n in evens)


def memory_comparison(size=100_000):
    """Show the size difference between a list and a generator.

    The generator is a fixed ~200 bytes no matter how large `size` gets,
    because it stores a recipe rather than results.
    """
    as_list = [n * n for n in range(size)]
    as_generator = (n * n for n in range(size))

    return {
        "size": size,
        "list_bytes": sys.getsizeof(as_list),
        "generator_bytes": sys.getsizeof(as_generator),
        "ratio": sys.getsizeof(as_list) / sys.getsizeof(as_generator),
    }
