class BankAccount:
    def deposit(self, amount):
        """Add money to the account balance.
        Phrases: deposit, deposit money, add money, top up, put in money.

        Args:
            amount: The amount of money to deposit into the account.

        Returns:
            A string confirming the deposit and showing the new balance.
        """
        return f"Deposited ${amount}. New balance: ${amount + 1000}"
    
    def withdraw(self, amount):
        """Remove money from the account balance.
        Phrases: withdraw, withdraw money, take out money, cash out, remove money.

        Args:
            amount: The amount of money to withdraw from the account.

        Returns:
            A string confirming the withdrawal and showing the new balance.
        """
        return f"Withdrew ${amount}. New balance: ${1000 - amount}"
    
    def get_balance(self):
        """Return the current account balance.
        Phrases: balance, get balance, show balance, check balance.

        Returns:
            The current balance as a float.
        """
        return 1000.00
    
    def transfer(self, recipient, amount):
        """Transfer money to another account.
        Phrases: transfer, transfer money, send money, pay someone, wire money.

        Args:
            recipient: The name or identifier of the account receiving the funds.
            amount: The amount of money to transfer.

        Returns:
            A string confirming the transfer with recipient and amount details.
        """
        return f"Transferred ${amount} to {recipient}"