# bank_account.py

class BankAccount:
    """
    A simple bank account class.

    You can create accounts, deposit money, withdraw money, and check account status.
    Designed to work well with your NLP parser using clear method names + docstrings.
    """

    def __init__(self, owner: str, balance: int):
        """
        Create a bank account.

        Phrases: create account, make account, new account, open account, start account,
        create bank account, make bank account, open a bank account, start a bank account,
        create an account for, make an account for, open account for, start account for.

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

        Phrases: deposit, add money, put money in, top up, increase balance, credit,
        deposit money, add money to account, put money into account, add funds,
        put funds in, increase the balance, add cash, deposit cash.

        Args:
            amount: money to add (must be > 0).
        """
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self.balance += amount
        # print(self.balance)
        print("Deposit: ", amount)
        print("Current Balance: ", self.balance)
        # return self.balance

    def withdraw(self, amount: int):
        """
        Take money out of the account.

        Phrases: withdraw, take out money, remove money, cash out, debit,
        withdraw money, take money out, remove money from account, pull money out,
        decrease balance, deduct money, pay out, withdraw cash.


        Args:
            amount: money to withdraw (must be > 0).
        """
        if amount <= 0:
            raise ValueError("Withdrawal must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        print("Withdrawn: ", amount)
        print("Current Balance: ", self.balance)
        # return self.balance

    # ------------------------------------------------------------
    # Basic getters
    # ------------------------------------------------------------

    def get_balance(self):
        """
        Get the current balance.

        Phrases: balance, check balance, show balance, how much money, money left,
        current balance, account balance, what is the balance, show me the balance,
        tell me the balance, how much is in the account, how much money is in the account,
        remaining balance, available balance, what is my balance, check account balance.

        """
        print("Current Balance: ", self.balance)
        # return self.balance

    def get_owner(self):
        """
        Get the owner name.

        Phrases: owner, account owner, who owns this account, show owner,
        who is the owner, who owns the account, account holder, show account owner,
        tell me the owner, who does this account belong to, whose account is this.

        """
        print(self.owner)
        # return self.owner

    def get_account_info(self):
        """
        Get account info as a dictionary.

        Phrases: account info, show account details, account summary, details, status,
        account information, show account info, show account information, show details,
        show summary, bank account summary, bank account details, show account status,
        account overview, show everything about account, account report.


        Returns:
            dict with owner, balance, and status.
        """
        print("owner", self.owner)
        print("balance", self.balance)
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

        Phrases: enough money, sufficient funds, can withdraw, can pay, afford,
        has enough money, do I have enough money, does the account have enough money,
        enough balance, enough funds, can afford this, can this account pay,
        can I withdraw this amount, is there enough money, is there enough balance,
        sufficient balance, enough money to withdraw, enough money to pay.

        Args:
            amount: the amount you want to check.
        """
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        print(self.balance >= amount)
        # return self.balance >= amount

    def is_overdrawn(self):
        """
        Check if the account is overdrawn (balance < 0).

        Phrases: overdrawn, negative balance, below zero, below 0, less than zero,
        less than 0, balance below zero, balance below 0, account below zero,
        account below 0, is account below zero, is account below 0, is balance negative,
        does the account have negative balance, is this account overdrawn.

        """
        print(self.balance < 0)
        
        # return self.balance < 0

    def is_low_balance(self, threshold: int = 100):
        """
        Check if balance is below a threshold.

        Phrases: low balance, under threshold, below limit, running low,
        below amount, less than amount, below, under, balance is low,
        is balance low, is the balance below, is the account below,
        below threshold, under amount, lower than, less than, balance under limit,
        account running low, account below threshold.


        Args:
            threshold: compare balance to this value (default 100).
        """
        if threshold < 0:
            raise ValueError("Threshold cannot be negative")
        print(self.balance < threshold)
        # return self.balance < threshold

    def is_high_balance(self, threshold: int = 1000):
        """
        Check if balance is above a threshold.

        Phrases: high balance, above threshold, above limit, a lot of money,
        balance is high, is balance high, is the balance above, is the account above,
        above amount, higher than, greater than, more than, balance above threshold,
        account above threshold, account has a lot of money, large balance.

        Args:
            threshold: compare balance to this value (default 1000).
        """
        if threshold < 0:
            raise ValueError("Threshold cannot be negative")
        print(self.balance > threshold)
        # return self.balance > threshold
    
