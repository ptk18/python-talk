from bankaccountpy import BankAccount
import sys

obj = BankAccount()
print(obj.deposit(amount=500.0))
print(obj.transfer(recipient='Mr.Smith', amount=500.0))
print(obj.transfer(recipient='my mother', amount=40.0))
