import turtle

class ShapeDrawer:
    def __init__(self):
        self.screen = turtle.Screen()
        self.screen.setup(width=1000, height=1000)
        self.screen.bgcolor("#f0f0f0")
        self.t = turtle.Turtle()
        self.t.speed(0)
        self.x_offset = -400
        self.y_position = 0
        self.spacing = 250

    def next_position(self):
        x = self.x_offset
        self.x_offset += self.spacing
        return x, self.y_position

    def fill_red(self, shape_func, *args):
        self.t.fillcolor("red")
        self.t.begin_fill()
        shape_func(*args)
        self.t.end_fill()

    def fill_blue(self, shape_func, *args):
        self.t.fillcolor("blue")
        self.t.begin_fill()
        shape_func(*args)
        self.t.end_fill()

    def fill_green(self, shape_func, *args):
        self.t.fillcolor("green")
        self.t.begin_fill()
        shape_func(*args)
        self.t.end_fill()

    def fill_yellow(self, shape_func, *args):
        self.t.fillcolor("yellow")
        self.t.begin_fill()
        shape_func(*args)
        self.t.end_fill()

    def draw_square(self, x, y, size):
        self.t.penup()
        self.t.goto(x, y)
        self.t.pendown()
        for _ in range(4):
            self.t.forward(size)
            self.t.right(90)

    def draw_circle(self, x=-100, y=0, radius=50):
        self.t.penup()
        self.t.goto(x, y - radius)
        self.t.pendown()
        self.t.circle(radius)

    def draw_triangle(self, x=0, y=0, side=100):
        self.t.penup()
        self.t.goto(x, y)
        self.t.pendown()
        for _ in range(3):
            self.t.forward(side)
            self.t.left(120)

    def draw_rectangle(self, x=100, y=0, w=120, h=80):
        self.t.penup()
        self.t.goto(x, y)
        self.t.pendown()
        for _ in range(2):
            self.t.forward(w)
            self.t.right(90)
            self.t.forward(h)
            self.t.right(90)

    def draw_scene(self):
        x1, y = self.next_position()
        self.fill_red(self.draw_square, x1, y, 100)

        x2, y = self.next_position()
        self.fill_blue(self.draw_circle, x2, y, 50)

        x3, y = self.next_position()
        self.fill_green(self.draw_triangle, x3, y, 120)

        x4, y = self.next_position()
        self.fill_yellow(self.draw_rectangle, x4, y, 120, 80)

def main():
    s = ShapeDrawer()
    s.draw_scene()
    s.screen.exitonclick()

if __name__ == "__main__":
    main()
