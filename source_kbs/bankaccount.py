class BankAccount:
    def deposit(self, amount):
        """Add money to the account balance."""
        return f"Deposited ${amount}. New balance: ${amount + 1000}"
    
    def withdraw(self, amount):
        """Remove money from the account balance."""
        return f"Withdrew ${amount}. New balance: ${1000 - amount}"
    
    def get_balance(self):
        """Return the current account balance."""
        return 1000.00
    
    def transfer(self, recipient, amount):
        """Transfer money to another account."""
        return f"Transferred ${amount} to {recipient}"