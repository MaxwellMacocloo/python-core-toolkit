"""File and directory operations, plus a context manager written by hand."""

import csv
import json
import os
import shutil
from pathlib import Path


class ManagedFile:
    """A context manager implemented with __enter__ and __exit__.

    This is what `with open(...)` does underneath. __exit__ runs even when
    the block raises, which is the whole point -- the file closes on the
    error path too.

    Returning False from __exit__ lets the exception propagate. Returning
    True would swallow it, which is almost never what you want.
    """

    def __init__(self, path, mode="r", encoding="utf-8"):
        self.path = Path(path)
        self.mode = mode
        self.encoding = None if "b" in mode else encoding
        self.handle = None
        self.closed_cleanly = False

    def __enter__(self):
        self.handle = open(self.path, self.mode, encoding=self.encoding)
        return self.handle

    def __exit__(self, exc_type, exc_value, traceback):
        if self.handle:
            self.handle.close()
            self.closed_cleanly = True
        return False  # never suppress the exception


def write_text(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def append_line(path, line):
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def count_lines(path):
    """Count lines without loading the file into memory."""
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        return sum(1 for _ in handle)


def word_frequencies(path, top_n=10):
    """Return the most common words in a text file."""
    from collections import Counter

    counter = Counter()
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            words = (w.strip(".,!?;:\"'()[]").lower() for w in line.split())
            counter.update(w for w in words if w)

    return counter.most_common(top_n)


# ------------------------------------------------------------------- csv

def write_csv(path, rows, fieldnames=None):
    """Write a list of dicts as CSV.

    newline="" is required on Windows. Without it, the csv module's own
    \\r\\n gets translated again and every row ends up separated by a
    blank line.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = fieldnames or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return path


def read_csv(path):
    with open(path, "r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def stream_csv(path):
    """Yield CSV rows one at a time, for files too large to hold."""
    with open(path, "r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            yield row


# ------------------------------------------------------------------ json

def write_json(path, data, indent=2):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=indent, default=str), encoding="utf-8")
    return path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ------------------------------------------------------------ filesystem

def directory_summary(path):
    """Walk a directory tree, counting files and bytes per extension."""
    root = Path(path)
    summary = {}
    total_files = 0
    total_bytes = 0

    for current, _dirs, files in os.walk(root):
        for name in files:
            file_path = Path(current) / name
            try:
                size = file_path.stat().st_size
            except OSError:
                continue

            suffix = file_path.suffix.lower() or "(no extension)"
            entry = summary.setdefault(suffix, {"files": 0, "bytes": 0})
            entry["files"] += 1
            entry["bytes"] += size
            total_files += 1
            total_bytes += size

    return {
        "root": str(root),
        "total_files": total_files,
        "total_bytes": total_bytes,
        "by_extension": dict(sorted(summary.items(),
                                    key=lambda kv: kv[1]["bytes"],
                                    reverse=True)),
    }


def copy_tree(source, destination):
    """Copy a directory tree, replacing the destination if present."""
    source, destination = Path(source), Path(destination)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return destination


def find_files(path, pattern="*"):
    """Return every matching file under a directory, recursively."""
    return sorted(p for p in Path(path).rglob(pattern) if p.is_file())
