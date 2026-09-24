"""A bank account: encapsulation, custom exceptions, operator overloading.

The balance is genuinely protected here. Every mutation goes through a
method that validates, records history, and can refuse.
"""

from datetime import datetime


class BankError(Exception):
    """Base class for every error this module raises.

    A module-level base exception lets callers write
    `except BankError` to catch anything from here, while still allowing
    `except InsufficientFundsError` for one specific case.
    """


class InsufficientFundsError(BankError):
    """Raised when a withdrawal exceeds the available balance."""

    def __init__(self, requested, available):
        # Carrying structured data on the exception is more useful to a
        # caller than making them parse the message string.
        self.requested = requested
        self.available = available
        self.shortfall = requested - available
        super().__init__(
            f"cannot withdraw {requested:.2f}: balance is {available:.2f} "
            f"(short by {self.shortfall:.2f})"
        )


class InvalidAmountError(BankError):
    """Raised for a non-positive or non-numeric amount."""


class AccountClosedError(BankError):
    """Raised when operating on a closed account."""


class BankAccount:
    """A bank account with a protected balance and a transaction log."""

    # A class attribute: shared by every instance, not per-object state.
    interest_rate = 0.05
    _account_counter = 1000

    def __init__(self, owner, balance=0.0, overdraft_limit=0.0):
        self.owner = owner
        self.overdraft_limit = float(overdraft_limit)
        self._balance = 0.0
        self._closed = False
        self._history = []

        BankAccount._account_counter += 1
        self.account_number = f"ACC{BankAccount._account_counter}"

        if balance:
            self.deposit(balance, note="opening balance")

    # ------------------------------------------------------- encapsulation

    @property
    def balance(self):
        """Read-only from outside. There is deliberately no setter.

        Assigning `account.balance = 1_000_000` raises AttributeError.
        Money can only move through deposit() and withdraw(), which
        validate and record.
        """
        return self._balance

    @property
    def history(self):
        """A copy, so a caller cannot mutate the ledger."""
        return list(self._history)

    @property
    def available(self):
        """Balance plus whatever overdraft is allowed."""
        return self._balance + self.overdraft_limit

    @property
    def is_closed(self):
        return self._closed

    # ------------------------------------------------------------ operations

    def _validate(self, amount):
        if self._closed:
            raise AccountClosedError(f"{self.account_number} is closed")
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidAmountError(f"amount must be a number, got {type(amount).__name__}")
        if amount <= 0:
            raise InvalidAmountError(f"amount must be positive, got {amount}")

    def _record(self, kind, amount, note):
        self._history.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "kind": kind,
            "amount": round(amount, 2),
            "balance": round(self._balance, 2),
            "note": note,
        })

    def deposit(self, amount, note=""):
        self._validate(amount)
        self._balance += amount
        self._record("deposit", amount, note)
        return self._balance

    def withdraw(self, amount, note=""):
        self._validate(amount)

        if amount > self.available:
            raise InsufficientFundsError(amount, self.available)

        self._balance -= amount
        self._record("withdraw", amount, note)
        return self._balance

    def transfer_to(self, other, amount, note=""):
        """Move money between accounts, atomically.

        The withdrawal is attempted first. If it raises, no deposit
        happens and neither account changed -- money cannot be created by
        a half-completed transfer.
        """
        if not isinstance(other, BankAccount):
            raise TypeError("can only transfer to another BankAccount")
        if other is self:
            raise ValueError("cannot transfer to the same account")

        self.withdraw(amount, note=note or f"transfer to {other.account_number}")
        try:
            other.deposit(amount, note=note or f"transfer from {self.account_number}")
        except BankError:
            # Put it back; the destination refused it.
            self.deposit(amount, note="transfer reversed")
            raise

        return self._balance

    def apply_interest(self):
        """Apply the class-level interest rate to a positive balance."""
        if self._balance <= 0:
            return self._balance

        interest = self._balance * self.interest_rate
        self._balance += interest
        self._record("interest", interest, f"at {self.interest_rate:.1%}")
        return self._balance

    def close(self):
        if self._balance != 0:
            raise BankError(
                f"cannot close {self.account_number} with a balance of {self._balance:.2f}"
            )
        self._closed = True

    # ----------------------------------------------------- dunder methods

    def __str__(self):
        state = " (closed)" if self._closed else ""
        return f"{self.account_number} [{self.owner}]: {self._balance:.2f}{state}"

    def __repr__(self):
        return (f"BankAccount(owner={self.owner!r}, balance={self._balance!r}, "
                f"overdraft_limit={self.overdraft_limit!r})")

    def __len__(self):
        """len(account) gives the number of transactions."""
        return len(self._history)

    def __bool__(self):
        """An account is truthy when it holds money.

        Without __bool__, __len__ would decide this, and an account with
        no transactions would be falsy regardless of its balance.
        """
        return self._balance > 0

    def __iter__(self):
        """Iterating an account yields its transactions."""
        return iter(self._history)

    def __eq__(self, other):
        if not isinstance(other, BankAccount):
            return NotImplemented
        return self.account_number == other.account_number

    def __hash__(self):
        return hash(self.account_number)

    def __lt__(self, other):
        if not isinstance(other, BankAccount):
            return NotImplemented
        return self._balance < other._balance


class SavingsAccount(BankAccount):
    """Inheritance with an overridden class attribute and a stricter rule."""

    interest_rate = 0.12
    minimum_balance = 100.0

    def __init__(self, owner, balance=0.0):
        # Savings accounts get no overdraft.
        super().__init__(owner, balance, overdraft_limit=0.0)

    def withdraw(self, amount, note=""):
        """Override: refuse a withdrawal that breaches the minimum.

        super().withdraw() still does the validation and recording, so the
        override adds a rule rather than reimplementing the method.
        """
        self._validate(amount)

        if self._balance - amount < self.minimum_balance:
            raise InsufficientFundsError(
                amount, max(0.0, self._balance - self.minimum_balance)
            )

        return super().withdraw(amount, note)
