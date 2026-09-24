"""Abstract base classes and the four OOP pillars.

Every shape here demonstrates something specific:

* Abstraction   -- Shape cannot be instantiated; subclasses must implement
* Inheritance   -- Circle, Rectangle, Square derive from Shape
* Polymorphism  -- the same total_area() loop handles any shape
* Encapsulation -- _radius is private, exposed through a validating property
"""

from abc import ABC, abstractmethod
from math import isclose, pi


class Shape(ABC):
    """Abstract base class for every shape.

    ABC plus @abstractmethod means `Shape()` raises TypeError. A subclass
    that forgets to implement `area` also fails at instantiation rather
    than silently inheriting a broken method.
    """

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def area(self):
        """Return the enclosed area."""

    @abstractmethod
    def perimeter(self):
        """Return the boundary length."""

    def describe(self):
        """Concrete method on an abstract class.

        Subclasses inherit this and it calls their area() and perimeter()
        through polymorphic dispatch -- the base class does not need to
        know which shape it is working with.
        """
        return (f"{self.name}: area={self.area():.2f}, "
                f"perimeter={self.perimeter():.2f}")

    # --- dunder methods: making objects behave like built-in types ---

    def __str__(self):
        """Readable, for users. This is what print() calls."""
        return self.describe()

    def __repr__(self):
        """Unambiguous, for developers. This is what the REPL shows.

        The convention is that eval(repr(obj)) should rebuild the object.
        """
        return f"{type(self).__name__}(name={self.name!r})"

    def __eq__(self, other):
        """Two shapes are equal when their areas are.

        Defining __eq__ without __hash__ makes the class unhashable, so
        __hash__ is defined too -- otherwise these could not go in a set.
        """
        if not isinstance(other, Shape):
            return NotImplemented
        return isclose(self.area(), other.area())

    def __hash__(self):
        return hash(round(self.area(), 9))

    def __lt__(self, other):
        """Ordering by area, so sorted() works on a list of shapes."""
        if not isinstance(other, Shape):
            return NotImplemented
        return self.area() < other.area()


class Circle(Shape):
    """A circle, with a validating property over a private attribute."""

    def __init__(self, radius):
        super().__init__("Circle")
        self.radius = radius  # goes through the setter below

    @property
    def radius(self):
        """Encapsulation: the attribute is read through a property.

        `_radius` is private by convention. The property lets the class
        validate on every assignment, including the one in __init__, which
        a bare public attribute cannot do.
        """
        return self._radius

    @radius.setter
    def radius(self, value):
        if value <= 0:
            raise ValueError(f"radius must be positive, got {value}")
        self._radius = float(value)

    @property
    def diameter(self):
        """A computed property: derived, never stored, never stale."""
        return self._radius * 2

    def area(self):
        return pi * self._radius ** 2

    def perimeter(self):
        return 2 * pi * self._radius

    def __repr__(self):
        return f"Circle(radius={self._radius!r})"


class Rectangle(Shape):
    def __init__(self, width, height):
        super().__init__("Rectangle")
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        self.width = float(width)
        self.height = float(height)

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)

    @property
    def is_square(self):
        return isclose(self.width, self.height)

    def __repr__(self):
        return f"Rectangle(width={self.width!r}, height={self.height!r})"


class Square(Rectangle):
    """Two levels of inheritance: Square -> Rectangle -> Shape.

    Square passes one side as both dimensions, so it inherits area() and
    perimeter() unchanged and only overrides the name.
    """

    def __init__(self, side):
        super().__init__(side, side)
        self.name = "Square"

    @property
    def side(self):
        return self.width

    def __repr__(self):
        return f"Square(side={self.width!r})"


class Triangle(Shape):
    def __init__(self, a, b, c):
        super().__init__("Triangle")
        sides = sorted([float(a), float(b), float(c)])

        if sides[0] <= 0:
            raise ValueError("all sides must be positive")
        # The triangle inequality: the two shorter sides must exceed the longest.
        if sides[0] + sides[1] <= sides[2]:
            raise ValueError(f"sides {a}, {b}, {c} cannot form a triangle")

        self.a, self.b, self.c = float(a), float(b), float(c)

    def area(self):
        """Heron's formula."""
        s = self.perimeter() / 2
        return (s * (s - self.a) * (s - self.b) * (s - self.c)) ** 0.5

    def perimeter(self):
        return self.a + self.b + self.c

    def __repr__(self):
        return f"Triangle(a={self.a!r}, b={self.b!r}, c={self.c!r})"


# ------------------------------------------------------------ polymorphism

def total_area(shapes):
    """Sum the areas of any mix of shapes.

    This function never checks a type. It calls .area() and each object
    supplies its own implementation -- that is polymorphism. Adding a new
    shape class requires no change here.
    """
    return sum(shape.area() for shape in shapes)


def largest(shapes):
    """Return the shape with the greatest area, using __lt__."""
    if not shapes:
        raise ValueError("no shapes given")
    return max(shapes)
