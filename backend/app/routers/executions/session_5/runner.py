from restaurantpy import Restaurant
import sys

obj = Restaurant()
print(obj.add_to_menu())
print(obj.add_to_menu(dish='steak', price=250.0))
