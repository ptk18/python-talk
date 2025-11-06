from turtle_shapespy import ShapeDrawer
import sys

obj = ShapeDrawer()
# session runner - commands will be appended below
print(obj.draw_circle(x=0, y=0, radius=50))
print(obj.fill_red(shape_func=None, args=None))
print(obj.draw_triangle(x=0, y=0, side=50))
print(obj.fill_yellow(shape_func=None, args=None))
