"""The shapes subpackage: abstraction, inheritance, polymorphism."""

from .base import (
    Circle, Rectangle, Shape, Square, Triangle, largest, total_area,
)

__all__ = ["Shape", "Circle", "Rectangle", "Square", "Triangle",
           "total_area", "largest"]
