from smarthomepy import SmartHome
import sys

obj = SmartHome()
# session runner - commands will be appended below
print(obj.turn_tv_on())
print(obj.turn_tv_on())
print(obj.turn_tv_on())
print(obj.turn_ac_off())
print(obj.turn_tv_on())
print(obj.turn_ac_off())
print(obj.get_temperature())
print(obj.is_hot())
print(obj.turn_all_on())
print(obj.turn_tv_on())
print(obj.increase_temperature(amount=10))
print(obj.turn_tv_on())
print(obj.turn_ac_off())
