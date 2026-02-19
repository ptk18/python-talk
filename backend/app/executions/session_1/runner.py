from smarthome import SmartHome
import sys

obj = SmartHome()
print(obj.turn_on(device='tv'))
print(obj.turn_on(device='light'))
