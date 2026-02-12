# parser/code/bank_account.py
# ============================================================
# BankAccount domain for docstring-similarity command mapping
# ============================================================

class BankAccount:
    """
    A simple bank account system for deposits, withdrawals, transfers, and reporting.
    """

    def __init__(self):
        """Initialize account state."""
        self._balance = 0
        self._transactions = []

    def deposit(self, amount: int):
        """
        Add money to the account balance.
        Phrases: deposit money, add money, top up, put in money.

        Args:
            amount: amount of money to add.
        """
        if amount <= 0:
            return "Amount must be positive"
        self._balance += amount
        self._transactions.append({"type": "deposit", "amount": amount})
        return f"Deposited {amount}. New balance: {self._balance}"

    def withdraw(self, amount: int):
        """
        Remove money from the account balance.
        Phrases: withdraw money, take out money, cash out, remove money.

        Args:
            amount: amount of money to withdraw.
        """
        if amount <= 0:
            return "Amount must be positive"
        if amount > self._balance:
            return "Insufficient funds"
        self._balance -= amount
        self._transactions.append({"type": "withdrawal", "amount": amount})
        return f"Withdrew {amount}. New balance: {self._balance}"

    def get_balance(self):
        """
        Get the current account balance.
        Phrases: get balance, show balance, check balance.
        """
        return {"balance": self._balance}

    def get_transactions(self, limit: int = 10):
        """
        Get recent transactions with an optional limit.
        Phrases: show transactions, list transactions, recent activity.

        Args:
            limit: number of most recent transactions to return (default 10).
        """
        return self._transactions[-limit:]

    def transfer(self, amount: int, recipient: str):
        """
        Send money to another person/account.
        Phrases: transfer money, send money, pay someone, wire money.

        Args:
            amount: amount of money to send.
            recipient: name of the receiver.
        """
        if amount <= 0:
            return "Amount must be positive"
        if amount > self._balance:
            return "Insufficient funds"
        self._balance -= amount
        self._transactions.append({"type": "transfer", "amount": amount, "recipient": recipient})
        return f"Transferred {amount} to {recipient}. New balance: {self._balance}"


# ------------------------------------------------------------
# Suggested tests + expected generated_code
# ------------------------------------------------------------
# "deposit 500"            -> bankaccount.deposit(500)
# "add money 200"          -> bankaccount.deposit(200)
# "withdraw 50"            -> bankaccount.withdraw(50)
# "send 100 to bob"        -> bankaccount.transfer(100, 'bob')
# "transfer 300 to alice"  -> bankaccount.transfer(300, 'alice')
# "get balance"            -> bankaccount.get_balance()
# "show transactions limit 3" -> bankaccount.get_transactions(3)
