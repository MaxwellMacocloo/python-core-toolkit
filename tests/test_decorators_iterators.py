"""Tests for decorators, closures, iterators, generators and file ops."""

import pytest

from toolkit import iterators
from toolkit.decorators import (
    call_logger, make_accumulator, make_counter, make_multiplier, memoize,
    retry, timed, validate_positive,
)
from toolkit.fileops import (
    ManagedFile, count_lines, read_csv, read_json, word_frequencies,
    write_csv, write_json, write_text,
)
from toolkit.iterators import (
    Countdown, Fibonacci, Repeater, chunked, countdown_gen, fibonacci_gen,
    memory_comparison, pipeline, take,
)


# -------------------------------------------------------------- decorators

def test_functools_wraps_preserves_identity():
    """Without @wraps the name would be 'wrapper', breaking help() and pdb."""
    @timed
    def compute_total(values):
        """Add up some values."""
        return sum(values)

    assert compute_total.__name__ == "compute_total"
    assert compute_total.__doc__ == "Add up some values."


def test_timed_records_duration_and_count():
    @timed
    def work():
        return sum(range(1000))

    work()
    work()

    assert work.call_count == 2
    assert work.last_duration > 0


def test_retry_succeeds_after_transient_failures():
    attempts = {"count": 0}

    @retry(times=3)
    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ConnectionError("not yet")
        return "ok"

    assert flaky() == "ok"
    assert attempts["count"] == 3


def test_retry_gives_up_and_reraises_the_last_error():
    @retry(times=2)
    def always_fails():
        raise ValueError("permanent")

    with pytest.raises(ValueError, match="permanent"):
        always_fails()


def test_retry_only_catches_listed_exceptions():
    """An unlisted exception must propagate immediately, not be retried."""
    calls = {"count": 0}

    @retry(times=3, exceptions=(ConnectionError,))
    def wrong_error():
        calls["count"] += 1
        raise TypeError("not retryable")

    with pytest.raises(TypeError):
        wrong_error()

    assert calls["count"] == 1  # tried once, not three times


def test_retry_rejects_invalid_times():
    with pytest.raises(ValueError, match="at least 1"):
        retry(times=0)


def test_memoize_caches_by_arguments():
    calls = {"count": 0}

    @memoize
    def slow_double(n):
        calls["count"] += 1
        return n * 2

    assert slow_double(5) == 10
    assert slow_double(5) == 10
    assert slow_double(6) == 12

    assert calls["count"] == 2   # 5 computed once, 6 computed once
    assert slow_double.hits == 1
    assert slow_double.misses == 2


def test_each_memoized_function_gets_its_own_cache():
    """The cache lives in the closure, not in a shared global."""
    @memoize
    def first(n):
        return n

    @memoize
    def second(n):
        return n * 10

    first(1)
    assert len(first.cache) == 1
    assert len(second.cache) == 0


def test_validate_positive_works_for_positional_and_keyword_calls():
    @validate_positive("width", "height")
    def area(width, height=1):
        return width * height

    assert area(3, 4) == 12
    assert area(width=3, height=4) == 12

    with pytest.raises(ValueError, match="width must be positive"):
        area(-3, 4)

    with pytest.raises(ValueError, match="height must be positive"):
        area(3, height=0)


def test_validate_positive_checks_defaults():
    @validate_positive("scale")
    def scaled(value, scale=-1):
        return value * scale

    with pytest.raises(ValueError, match="scale must be positive"):
        scaled(10)


def test_call_logger_writes_to_the_caller_s_list():
    log = []

    @call_logger(log)
    def greet(name):
        return f"hi {name}"

    greet("Ama")
    greet("Kofi")

    assert len(log) == 2
    assert "greet" in log[0]


def test_decorators_stack():
    @timed
    @memoize
    def square(n):
        return n * n

    assert square(4) == 16
    assert square(4) == 16
    assert square.call_count == 2  # timed saw both calls


# ----------------------------------------------------------------- closures

def test_counter_holds_its_own_state():
    counter = make_counter()
    assert [counter(), counter(), counter()] == [1, 2, 3]


def test_counters_are_independent():
    a, b = make_counter(), make_counter(100)
    a()
    a()
    assert a() == 3
    assert b() == 101


def test_counter_reset():
    counter = make_counter()
    counter()
    counter()
    counter.reset()
    assert counter() == 1


def test_multiplier_captures_its_factor():
    double, triple = make_multiplier(2), make_multiplier(3)
    assert double(5) == 10
    assert triple(5) == 15


def test_accumulator_keeps_a_running_total():
    accumulate = make_accumulator()
    assert accumulate(10) == 10
    assert accumulate(5) == 15
    assert accumulate(-3) == 12


# ---------------------------------------------------------------- iterators

def test_countdown_iterator():
    assert list(Countdown(5)) == [5, 4, 3, 2, 1, 0]


def test_countdown_rejects_negative_start():
    with pytest.raises(ValueError):
        Countdown(-1)


def test_an_iterator_is_exhausted_after_one_pass():
    """__iter__ returning self means the object cannot be reused."""
    countdown = Countdown(3)
    assert list(countdown) == [3, 2, 1, 0]
    assert list(countdown) == []       # nothing left


def test_an_iterable_can_be_looped_more_than_once():
    """Repeater.__iter__ returns a fresh generator every call."""
    repeater = Repeater("x", 3)
    assert list(repeater) == ["x", "x", "x"]
    assert list(repeater) == ["x", "x", "x"]   # still works


def test_stopiteration_ends_the_loop():
    iterator = iter(Countdown(1))
    assert next(iterator) == 1
    assert next(iterator) == 0

    with pytest.raises(StopIteration):
        next(iterator)


def test_fibonacci_iterator():
    assert list(Fibonacci(10)) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


# --------------------------------------------------------------- generators

def test_generator_matches_the_hand_written_iterator():
    """Same output, a third of the code."""
    assert list(countdown_gen(5)) == list(Countdown(5))


def test_infinite_generator_is_safe_when_taken_lazily():
    """fibonacci_gen() never terminates; take() stops pulling."""
    assert take(fibonacci_gen(), 10) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


def test_take_handles_a_short_iterable():
    assert take(countdown_gen(2), 100) == [2, 1, 0]


def test_bounded_generator_terminates():
    assert list(fibonacci_gen(limit=5)) == [0, 1, 1, 2, 3]


def test_chunked_groups_with_a_short_final_batch():
    assert list(chunked(range(7), 3)) == [[0, 1, 2], [3, 4, 5], [6]]
    assert list(chunked([], 3)) == []


def test_chunked_rejects_bad_size():
    with pytest.raises(ValueError, match="at least 1"):
        list(chunked(range(5), 0))


def test_generator_pipeline_is_lazy():
    """Nothing runs until iteration; no intermediate list is built."""
    result = pipeline(range(10))

    import types
    assert isinstance(result, types.GeneratorType)

    # squares: 0,1,4,9,16,25,36,49,64,81 -> evens: 0,4,16,36,64 -> +1
    assert list(result) == [1, 5, 17, 37, 65]


def test_generator_uses_constant_memory():
    """The headline result: a generator does not grow with the data."""
    small = memory_comparison(1_000)
    large = memory_comparison(100_000)

    # The list grows 100x; the generator does not grow at all.
    assert large["list_bytes"] > small["list_bytes"] * 50
    assert large["generator_bytes"] == small["generator_bytes"]
    assert large["ratio"] > 1000


# ----------------------------------------------------------------- file ops

def test_managed_file_closes_on_success(tmp_path):
    path = write_text(tmp_path / "sample.txt", "hello")

    manager = ManagedFile(path)
    with manager as handle:
        assert handle.read() == "hello"

    assert manager.closed_cleanly is True
    assert manager.handle.closed is True


def test_managed_file_closes_on_exception(tmp_path):
    """__exit__ runs on the error path too -- that is the whole point."""
    path = write_text(tmp_path / "sample.txt", "hello")

    manager = ManagedFile(path)
    with pytest.raises(RuntimeError):
        with manager as handle:
            handle.read()
            raise RuntimeError("boom")

    assert manager.closed_cleanly is True
    assert manager.handle.closed is True


def test_managed_file_does_not_swallow_exceptions():
    """__exit__ returns False, so the error propagates."""
    assert ManagedFile("x").__exit__(RuntimeError, RuntimeError("e"), None) is False


def test_count_lines(tmp_path):
    path = write_text(tmp_path / "lines.txt", "a\nb\nc\n")
    assert count_lines(path) == 3


def test_word_frequencies(tmp_path):
    path = write_text(tmp_path / "words.txt",
                      "the cat sat on the mat. The cat purred!")
    frequencies = dict(word_frequencies(path, top_n=3))

    assert frequencies["the"] == 3   # case-insensitive
    assert frequencies["cat"] == 2   # punctuation stripped


def test_csv_round_trip(tmp_path):
    rows = [
        {"name": "Ama", "score": "88"},
        {"name": "Kofi", "score": "61"},
    ]
    path = write_csv(tmp_path / "scores.csv", rows)

    assert read_csv(path) == rows


def test_csv_has_no_blank_lines_between_rows(tmp_path):
    """newline='' is required on Windows, or every row gets a blank line."""
    path = write_csv(tmp_path / "scores.csv", [{"a": "1"}, {"a": "2"}])
    text = path.read_text(encoding="utf-8")

    assert "\n\n" not in text.replace("\r\n", "\n")


def test_stream_csv_yields_rows_lazily(tmp_path):
    import types
    path = write_csv(tmp_path / "scores.csv", [{"a": "1"}, {"a": "2"}])

    from toolkit.fileops import stream_csv
    stream = stream_csv(path)

    assert isinstance(stream, types.GeneratorType)
    assert len(list(stream)) == 2


def test_json_round_trip(tmp_path):
    data = {"students": ["Ama", "Kofi"], "average": 74.5, "passed": True}
    path = write_json(tmp_path / "data.json", data)

    assert read_json(path) == data


def test_read_in_chunks(tmp_path):
    path = write_text(tmp_path / "big.txt", "x" * 2500)

    chunks = list(iterators.read_in_chunks(path, chunk_size=1000))
    assert [len(c) for c in chunks] == [1000, 1000, 500]
    assert "".join(chunks) == "x" * 2500


def test_read_lines_skips_blanks(tmp_path):
    path = write_text(tmp_path / "lines.txt", "one\n\n  \ntwo\n")
    assert list(iterators.read_lines(path)) == ["one", "two"]


def test_directory_summary(tmp_path):
    from toolkit.fileops import directory_summary

    write_text(tmp_path / "a.txt", "hello")
    write_text(tmp_path / "b.txt", "world!")
    write_json(tmp_path / "c.json", {"k": "v"})

    summary = directory_summary(tmp_path)

    assert summary["total_files"] == 3
    assert summary["by_extension"][".txt"]["files"] == 2
    assert summary["by_extension"][".json"]["files"] == 1
    assert summary["total_bytes"] > 0


def test_find_files_matches_a_pattern(tmp_path):
    from toolkit.fileops import find_files

    write_text(tmp_path / "a.txt", "x")
    write_text(tmp_path / "nested" / "b.txt", "y")
    write_text(tmp_path / "c.md", "z")

    assert len(find_files(tmp_path, "*.txt")) == 2
    assert len(find_files(tmp_path)) == 3
