from turtle_shapespy import ShapeDrawer
import sys

obj = ShapeDrawer()
# session runner - commands will be appended below
print(obj.draw_circle(x=0, y=0, radius=50))
print(obj.fill_red())
print(obj.draw_rectangle(x=0, y=0, w=100, h=50))
print(obj.fill_blue())
