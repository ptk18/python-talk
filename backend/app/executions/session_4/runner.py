from smarthomepy import SmartHome
import sys

obj = SmartHome()
# session runner - commands will be appended below
print(obj.turn_ac_off())
print(obj.turn_ac_off())
print(obj.get_temperature())
print(obj.set_temperature(value=10))
print(obj.get_temperature())
print(obj.get_temperature())
print(obj.divide(a=4, b=5))
print(obj.add(a=2, b=3))
