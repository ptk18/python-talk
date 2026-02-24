class BankAccount:
    """Enhanced bank account with comprehensive query methods for conditionals"""
    
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        """Deposit money into the account"""
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self.balance += amount
        return self.balance

    def withdraw(self, amount):
        """Withdraw money from the account"""
        if amount <= 0:
            raise ValueError("Withdrawal must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        return self.balance

    def get_balance(self):
        """Get the current account balance"""
        return self.balance
    
    def get_owner(self):
        """Get the account owner name"""
        return self.owner
    
    def has_sufficient_funds(self, amount):
        """Check if account has sufficient funds for a withdrawal"""
        return self.balance >= amount
    
    def is_overdrawn(self):
        """Check if account balance is negative"""
        return self.balance < 0
    
    def is_low_balance(self, threshold=100):
        """Check if balance is below a threshold (default: 100)"""
        return self.balance < threshold
    
    def is_high_balance(self, threshold=1000):
        """Check if balance is above a threshold (default: 1000)"""
        return self.balance > threshold
    
    def get_account_info(self):
        """Get comprehensive account information"""
        return {
            "owner": self.owner,
            "balance": self.balance,
            "status": "overdrawn" if self.balance < 0 else "active"
        }


def main():
    account = BankAccount("Demo User", 100)
    print(f"Owner: {account.get_owner()}")
    print(f"Starting balance: {account.get_balance()}")
    
    # Test query methods
    print(f"Has $150? {account.has_sufficient_funds(150)}")
    print(f"Is low balance? {account.is_low_balance()}")
    print(f"Is high balance? {account.is_high_balance()}")
    
    # Transactions
    account.deposit(50)
    print(f"After deposit: {account.get_balance()}")
    
    account.withdraw(30)
    print(f"After withdrawal: {account.get_balance()}")
    
    print(f"Account info: {account.get_account_info()}")


if __name__ == "__main__":
    main()