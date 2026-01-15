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
print(obj.add(a=7, b=8))
print(obj.add(a=43, b=62))
print(obj.divide(a=30, b=3))
print(obj.add(a=44, b=33))
print(obj.multiply(a=3, b=4))
print(obj.add(a=4, b=6))
print(obj.add(a=768, b=899))
print(obj.add(a=4, b=5))
