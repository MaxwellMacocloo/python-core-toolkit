"""Tests for the OOP pillars: shapes and the bank account."""

import pytest

from toolkit.bank import (
    AccountClosedError, BankAccount, BankError, InsufficientFundsError,
    InvalidAmountError, SavingsAccount,
)
from toolkit.shapes import Circle, Rectangle, Shape, Square, Triangle, largest, total_area


# --------------------------------------------------------------- abstraction

def test_abstract_base_cannot_be_instantiated():
    with pytest.raises(TypeError, match="abstract"):
        Shape("nothing")


def test_incomplete_subclass_cannot_be_instantiated():
    """Forgetting an abstract method fails at instantiation, not at call time."""
    class Blob(Shape):
        def area(self):
            return 1.0
        # perimeter() deliberately missing

    with pytest.raises(TypeError, match="abstract"):
        Blob("blob")


# --------------------------------------------------------------------- area

def test_circle_area_and_perimeter():
    circle = Circle(3)
    assert circle.area() == pytest.approx(28.2743, abs=1e-4)
    assert circle.perimeter() == pytest.approx(18.8496, abs=1e-4)
    assert circle.diameter == 6.0


def test_rectangle_and_square():
    assert Rectangle(4, 5).area() == 20
    assert Rectangle(4, 5).perimeter() == 18
    assert Square(4).area() == 16
    assert Square(4).side == 4


def test_triangle_area_by_herons_formula():
    # The 3-4-5 right triangle has area 6.
    assert Triangle(3, 4, 5).area() == pytest.approx(6.0)


# --------------------------------------------------------------- inheritance

def test_square_inherits_two_levels():
    square = Square(5)
    assert isinstance(square, Square)
    assert isinstance(square, Rectangle)
    assert isinstance(square, Shape)


def test_square_inherits_rectangle_behaviour():
    """Square overrides nothing but the name; area() comes from Rectangle."""
    assert Square(6).is_square is True
    assert Rectangle(6, 7).is_square is False


def test_mro_order():
    assert [c.__name__ for c in Square.__mro__][:4] == [
        "Square", "Rectangle", "Shape", "ABC"
    ]


# -------------------------------------------------------------- polymorphism

def test_total_area_accepts_any_mix_of_shapes():
    """The function never checks a type; each object supplies area()."""
    mixed = [Circle(1), Rectangle(2, 3), Square(2), Triangle(3, 4, 5)]
    expected = Circle(1).area() + 6 + 4 + 6
    assert total_area(mixed) == pytest.approx(expected)


def test_a_new_shape_needs_no_change_to_total_area():
    """Adding a shape class requires no edit to the polymorphic function."""
    class Hexagon(Shape):
        def __init__(self, side):
            super().__init__("Hexagon")
            self.side = side

        def area(self):
            return 1.5 * (3 ** 0.5) * self.side ** 2

        def perimeter(self):
            return 6 * self.side

    shapes = [Square(2), Hexagon(1)]
    assert total_area(shapes) == pytest.approx(4 + 2.598076, abs=1e-5)


def test_describe_dispatches_to_the_subclass():
    """A concrete method on the abstract class calls the subclass's area()."""
    assert Square(3).describe() == "Square: area=9.00, perimeter=12.00"


def test_largest_uses_dunder_lt():
    shapes = [Square(2), Circle(3), Rectangle(1, 1)]
    assert largest(shapes) is shapes[1]


def test_shapes_are_sortable():
    shapes = sorted([Circle(3), Square(1), Rectangle(2, 2)])
    areas = [s.area() for s in shapes]
    assert areas == sorted(areas)


# ------------------------------------------------------------- encapsulation

def test_circle_radius_is_validated_on_assignment():
    circle = Circle(5)
    with pytest.raises(ValueError, match="radius must be positive"):
        circle.radius = -1

    # The failed assignment left the object untouched.
    assert circle.radius == 5.0


def test_circle_rejects_bad_radius_in_constructor():
    """The property setter runs for the __init__ assignment too."""
    with pytest.raises(ValueError, match="radius must be positive"):
        Circle(0)


def test_triangle_enforces_the_triangle_inequality():
    with pytest.raises(ValueError, match="cannot form a triangle"):
        Triangle(1, 2, 10)


# ------------------------------------------------------------ dunder methods

def test_equality_compares_area():
    assert Square(2) == Rectangle(1, 4)      # both area 4
    assert Square(2) != Square(3)


def test_equality_with_a_non_shape_returns_notimplemented():
    """Returning NotImplemented lets Python fall back, rather than crashing."""
    assert Square(2).__eq__("not a shape") is NotImplemented
    assert (Square(2) == "not a shape") is False


def test_shapes_are_hashable():
    """__eq__ without __hash__ would make these unusable in a set."""
    assert len({Square(2), Rectangle(1, 4), Square(3)}) == 2


def test_repr_is_reconstructable():
    circle = Circle(2.5)
    assert repr(circle) == "Circle(radius=2.5)"
    assert eval(repr(circle)).area() == circle.area()


# --------------------------------------------------------------- bank basics

def test_deposit_and_withdraw():
    account = BankAccount("Ama", 500)
    assert account.balance == 500

    account.deposit(250)
    assert account.balance == 750

    account.withdraw(100)
    assert account.balance == 650


def test_balance_has_no_setter():
    """The whole point of the property: money cannot be assigned directly."""
    account = BankAccount("Ama", 500)
    with pytest.raises(AttributeError):
        account.balance = 1_000_000

    assert account.balance == 500


def test_history_is_a_copy():
    """Returning the list itself would let a caller rewrite the ledger."""
    account = BankAccount("Ama", 500)
    account.history.append({"kind": "forged"})

    assert len(account.history) == 1  # only the opening deposit


def test_overdraft_limit_extends_available_balance():
    account = BankAccount("Ama", 100, overdraft_limit=200)
    assert account.available == 300

    account.withdraw(250)
    assert account.balance == -150


def test_insufficient_funds_carries_structured_data():
    """A caller should not have to parse the message string."""
    account = BankAccount("Ama", 100)

    with pytest.raises(InsufficientFundsError) as info:
        account.withdraw(150)

    assert info.value.requested == 150
    assert info.value.available == 100
    assert info.value.shortfall == 50


@pytest.mark.parametrize("amount", [0, -50])
def test_non_positive_amounts_are_rejected(amount):
    account = BankAccount("Ama", 100)
    with pytest.raises(InvalidAmountError, match="must be positive"):
        account.deposit(amount)


def test_non_numeric_amount_is_rejected():
    account = BankAccount("Ama", 100)
    with pytest.raises(InvalidAmountError, match="must be a number"):
        account.deposit("100")


def test_booleans_are_rejected_as_amounts():
    """bool is a subclass of int, so it needs excluding explicitly."""
    account = BankAccount("Ama", 100)
    with pytest.raises(InvalidAmountError):
        account.deposit(True)


# ----------------------------------------------------------- exception tree

def test_specific_exceptions_are_catchable_by_the_base():
    """The module-level base class is what makes this work."""
    account = BankAccount("Ama", 100)

    with pytest.raises(BankError):
        account.withdraw(500)

    with pytest.raises(BankError):
        account.deposit(-1)

    assert issubclass(InsufficientFundsError, BankError)
    assert issubclass(InvalidAmountError, BankError)
    assert issubclass(BankError, Exception)


def test_closed_account_refuses_operations():
    account = BankAccount("Ama", 100)
    account.withdraw(100)
    account.close()

    with pytest.raises(AccountClosedError):
        account.deposit(50)


def test_cannot_close_an_account_holding_money():
    account = BankAccount("Ama", 100)
    with pytest.raises(BankError, match="cannot close"):
        account.close()


# --------------------------------------------------------------- transfers

def test_transfer_moves_money_between_accounts():
    source = BankAccount("Ama", 1000)
    target = BankAccount("Kofi", 0)

    source.transfer_to(target, 400)

    assert source.balance == 600
    assert target.balance == 400


def test_failed_transfer_leaves_both_accounts_unchanged():
    """Money must not be created or destroyed by a half-done transfer."""
    source = BankAccount("Ama", 100)
    target = BankAccount("Kofi", 50)

    with pytest.raises(InsufficientFundsError):
        source.transfer_to(target, 500)

    assert source.balance == 100
    assert target.balance == 50


def test_transfer_to_self_is_rejected():
    account = BankAccount("Ama", 100)
    with pytest.raises(ValueError, match="same account"):
        account.transfer_to(account, 50)


def test_transfer_to_non_account_is_rejected():
    account = BankAccount("Ama", 100)
    with pytest.raises(TypeError):
        account.transfer_to("Kofi", 50)


# ------------------------------------------------------- class attributes

def test_interest_uses_the_class_attribute():
    account = BankAccount("Ama", 1000)
    account.apply_interest()
    assert account.balance == pytest.approx(1050.0)


def test_savings_overrides_the_class_attribute():
    assert BankAccount.interest_rate == 0.05
    assert SavingsAccount.interest_rate == 0.12

    savings = SavingsAccount("Kofi", 1000)
    savings.apply_interest()
    assert savings.balance == pytest.approx(1120.0)


def test_savings_enforces_a_minimum_balance():
    savings = SavingsAccount("Kofi", 150)

    with pytest.raises(InsufficientFundsError):
        savings.withdraw(100)  # would leave 50, below the 100 minimum

    savings.withdraw(50)  # leaves exactly 100
    assert savings.balance == 100


def test_savings_has_no_overdraft():
    savings = SavingsAccount("Kofi", 500)
    assert savings.overdraft_limit == 0.0


def test_account_numbers_are_unique():
    accounts = [BankAccount(f"Owner {i}") for i in range(5)]
    assert len({a.account_number for a in accounts}) == 5


# --------------------------------------------------------- bank dunders

def test_len_counts_transactions():
    account = BankAccount("Ama", 100)  # opening deposit
    account.deposit(50)
    account.withdraw(25)
    assert len(account) == 3


def test_bool_reflects_balance_not_transaction_count():
    """Without __bool__, __len__ would decide truthiness."""
    empty = BankAccount("Ama", 0)
    assert len(empty) == 0
    assert bool(empty) is False

    funded = BankAccount("Kofi", 100)
    assert bool(funded) is True

    funded.withdraw(100)
    assert len(funded) == 2      # has history
    assert bool(funded) is False  # but no money


def test_iterating_an_account_yields_transactions():
    account = BankAccount("Ama", 100)
    account.deposit(50)

    kinds = [entry["kind"] for entry in account]
    assert kinds == ["deposit", "deposit"]


def test_accounts_sort_by_balance():
    accounts = [BankAccount("A", 300), BankAccount("B", 100), BankAccount("C", 200)]
    assert [a.balance for a in sorted(accounts)] == [100, 200, 300]


def test_account_equality_is_by_number_not_balance():
    a = BankAccount("Ama", 100)
    b = BankAccount("Ama", 100)
    assert a != b          # same owner and balance, different accounts
    assert a == a
