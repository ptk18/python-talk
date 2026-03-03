# bank_account.py

class BankAccount:
    """
    A simple bank account class.

    You can create accounts, deposit money, withdraw money, and check account status.
    Designed to work well with your NLP parser using clear method names + docstrings.
    """

    def __init__(self, owner: str, balance: int = 0):
        """
        Create a bank account.

        Phrases: create account, make account, new account, open account, start account.

        Args:
            owner: account owner name (example: "Top", "Preme").
            balance: starting balance (default 0).
        """
        if not owner:
            raise ValueError("Owner must be provided")
        if balance < 0:
            raise ValueError("Starting balance cannot be negative")
        self.owner = owner
        self.balance = balance

    # ------------------------------------------------------------
    # Money operations
    # ------------------------------------------------------------

    def deposit(self, amount: int):
        """
        Add money into the account.

        Phrases: deposit, add money, put money in, top up, increase balance, credit.

        Args:
            amount: money to add (must be > 0).
        """
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self.balance += amount
        return self.balance

    def withdraw(self, amount: int):
        """
        Take money out of the account.

        Phrases: withdraw, take out money, remove money, cash out, debit.

        Args:
            amount: money to withdraw (must be > 0).
        """
        if amount <= 0:
            raise ValueError("Withdrawal must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        return self.balance

    # ------------------------------------------------------------
    # Basic getters
    # ------------------------------------------------------------

    def get_balance(self):
        """
        Get the current balance.

        Phrases: balance, check balance, show balance, how much money, money left.
        """
        return self.balance

    def get_owner(self):
        """
        Get the owner name.

        Phrases: owner, account owner, who owns this account, show owner.
        """
        return self.owner

    def get_account_info(self):
        """
        Get account info as a dictionary.

        Phrases: account info, show account details, account summary, details, status.

        Returns:
            dict with owner, balance, and status.
        """
        return {
            "owner": self.owner,
            "balance": self.balance,
            "status": "overdrawn" if self.balance < 0 else "active"
        }

    # ------------------------------------------------------------
    # Boolean checks (useful for if/conditions later)
    # ------------------------------------------------------------

    def has_sufficient_funds(self, amount: int):
        """
        Check if the account has enough money for a withdrawal.

        Phrases: enough money, sufficient funds, can withdraw, can pay, afford.

        Args:
            amount: the amount you want to check.
        """
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        return self.balance >= amount

    def is_overdrawn(self):
        """
        Check if the account is overdrawn (balance < 0).

        Phrases: overdrawn, negative balance, below zero.
        """
        return self.balance < 0

    def is_low_balance(self, threshold: int = 100):
        """
        Check if balance is below a threshold.

        Phrases: low balance, under threshold, below limit, running low.

        Args:
            threshold: compare balance to this value (default 100).
        """
        if threshold < 0:
            raise ValueError("Threshold cannot be negative")
        return self.balance < threshold

    def is_high_balance(self, threshold: int = 1000):
        """
        Check if balance is above a threshold.

        Phrases: high balance, above threshold, above limit, a lot of money.

        Args:
            threshold: compare balance to this value (default 1000).
        """
        if threshold < 0:
            raise ValueError("Threshold cannot be negative")
        return self.balance > threshold


def main():
    # Quick demo (optional)
    acc1 = BankAccount("Top", 100)
    print("acc1 owner:", acc1.get_owner())
    print("acc1 balance:", acc1.get_balance())
    acc1.deposit(50)
    print("after deposit:", acc1.get_balance())
    acc1.withdraw(30)
    print("after withdraw:", acc1.get_balance())
    print("info:", acc1.get_account_info())


if __name__ == "__main__":
    main()