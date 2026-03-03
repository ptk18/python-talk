from accountant import Accountant

# create accountant for Suriya call it acc1
acc1 = Accountant(owner_name="Suriya")
# spend 1200 rent
acc1.add_expense(amount=1200, category='rent')
# add note lunch with friend
acc1.add_note(note='lunch with friend')
# set monthly limit rent 10000
acc1.set_budget(category='rent', amount=10000)
# food
acc1.set_budget(category='food', amount=3000)
