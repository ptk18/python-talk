class BankAccount:
    def __init__(self, balance=1000):
        """Create a new bank account.
        Phrases: create account, open account, new account.

        Args:
            balance: The initial balance of the account.
        """
        self.balance = balance

    def deposit(self, amount):
        """Add money to the account balance.
        Phrases: deposit, deposit money, add money, top up, put in money.

        Args:
            amount: The amount of money to deposit into the account.

        Returns:
            A string confirming the deposit and showing the new balance.
        """
        self.balance += amount
        return f"Deposited ${amount}. New balance: ${self.balance}"

    def withdraw(self, amount):
        """Remove money from the account balance.
        Phrases: withdraw, withdraw money, take out money, cash out, remove money.

        Args:
            amount: The amount of money to withdraw from the account.

        Returns:
            A string confirming the withdrawal and showing the new balance.
        """
        if amount > self.balance:
            return f"Insufficient funds. Current balance: ${self.balance}"
        self.balance -= amount
        return f"Withdrew ${amount}. New balance: ${self.balance}"

    def get_balance(self):
        """Return the current account balance.
        Phrases: balance, get balance, show balance, check balance.

        Returns:
            The current balance as a float.
        """
        return self.balance

    def transfer(self, recipient, amount):
        """Transfer money to another account.
        Phrases: transfer, transfer money, send money, pay someone, wire money.

        Args:
            recipient: The name or identifier of the account receiving the funds.
            amount: The amount of money to transfer.

        Returns:
            A string confirming the transfer with recipient and amount details.
        """
        if amount > self.balance:
            return f"Insufficient funds. Current balance: ${self.balance}"
        self.balance -= amount
        return f"Transferred ${amount} to {recipient}. New balance: ${self.balance}"