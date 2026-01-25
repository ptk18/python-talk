import turtle
import random

class TurtleHomeAndTrees:
    def __init__(self):
        self.bgcolor = "#87ceeb"
        self.ground_color = "#2ecc71"
        self.house_color = "#ffcc66"
        self.roof_color = "#cc6633"
        self.door_color = "#663300"
        self.window_color = "#99ccff"
        self.trunk_color = "#6b4226"
        self.leaf_color = "#228B22"
        self.screen = None
        self.t = None
        self.width = 1000
        self.height = 700

    def setup_screen(self):
        self.screen = turtle.Screen()
        self.screen.setup(width=self.width, height=self.height)
        self.screen.bgcolor(self.bgcolor)
        self.screen.title("Home with Trees")

    def create_turtle(self):
        self.t = turtle.Turtle(visible=False)
        self.t.speed(0)
        self.t.pensize(2)

    def draw_rectangle(self, width, height, color):
        self.t.fillcolor(color)
        self.t.begin_fill()
        for _ in range(2):
            self.t.forward(width)
            self.t.left(90)
            self.t.forward(height)
            self.t.left(90)
        self.t.end_fill()

    def draw_ground(self):
        self.t.penup()
        self.t.goto(-500, -250)
        self.t.pendown()
        self.t.fillcolor(self.ground_color)
        self.t.begin_fill()
        self.t.forward(1000)
        self.t.left(90)
        self.t.forward(250)
        self.t.left(90)
        self.t.forward(1000)
        self.t.left(90)
        self.t.forward(250)
        self.t.left(90)
        self.t.end_fill()

    def draw_house(self):
        # House base
        self.t.penup()
        self.t.goto(-100, -250)
        self.t.setheading(0)
        self.t.pendown()
        self.draw_rectangle(200, 150, self.house_color)

        # Roof
        self.t.fillcolor(self.roof_color)
        self.t.begin_fill()
        self.t.goto(-120, -100)
        self.t.goto(0, 0)
        self.t.goto(120, -100)
        self.t.goto(-120, -100)
        self.t.end_fill()

        # Door
        self.t.penup()
        self.t.goto(-30, -250)
        self.t.setheading(0)
        self.t.pendown()
        self.draw_rectangle(60, 80, self.door_color)

        # Windows
        for x in [-80, 40]:
            self.t.penup()
            self.t.goto(x, -160)
            self.t.setheading(0)
            self.t.pendown()
            self.draw_rectangle(40, 40, self.window_color)

    def draw_tree(self, x, y, size=1.0):
        self.t.penup()
        self.t.goto(x, y)
        self.t.setheading(90)
        self.t.pendown()

        # trunk
        self.t.fillcolor(self.trunk_color)
        self.t.begin_fill()
        for _ in range(2):
            self.t.forward(40 * size)
            self.t.right(90)
            self.t.forward(10 * size)
            self.t.right(90)
        self.t.end_fill()

        # leaves (3 stacked triangles)
        self.t.fillcolor(self.leaf_color)
        self.t.begin_fill()
        self.t.goto(x - 25 * size, y + 40 * size)
        self.t.goto(x + 5 * size, y + 90 * size)
        self.t.goto(x + 35 * size, y + 40 * size)
        self.t.goto(x - 25 * size, y + 40 * size)
        self.t.end_fill()

    def draw_many_trees(self, count=8):
        for _ in range(count):
            x = random.randint(-450, 450)
            y = random.randint(-250, -150)
            size = random.uniform(0.8, 1.3)
            self.draw_tree(x, y, size)

    def draw_canvas(self):
        self.setup_screen()
        self.create_turtle()
        turtle.tracer(False)
        self.draw_ground()
        self.draw_house()
        self.draw_many_trees()
        turtle.tracer(True)

    def run(self):
        self.draw_canvas()
        self.screen.exitonclick()


if __name__ == "__main__":
    TurtleHomeAndTrees().run()
