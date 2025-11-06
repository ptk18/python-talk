import turtle

class ShapeDrawer:
    def __init__(self):
        self.screen = turtle.Screen()
        self.screen.setup(width=900, height=700)
        self.screen.bgcolor("#f0f0f0")
        self.t = turtle.Turtle()
        self.t.speed(0)

    def fill_red(self):
        self.t.fillcolor("red")
        self.t.begin_fill()

    def fill_blue(self):
        self.t.fillcolor("blue")
        self.t.begin_fill()

    def fill_green(self):
        self.t.fillcolor("green")
        self.t.begin_fill()

    def fill_yellow(self):
        self.t.fillcolor("yellow")
        self.t.begin_fill()

    def end_fill(self):
        self.t.end_fill()

    def draw_square(self, x, y, size):
        self.t.penup()
        self.t.goto(x, y)
        self.t.pendown()
        for _ in range(4):
            self.t.forward(size)
            self.t.right(90)

    def draw_circle(self, x, y, radius):
        self.t.penup()
        self.t.goto(x, y - radius)
        self.t.pendown()
        self.t.circle(radius)

    def draw_triangle(self, x, y, side):
        self.t.penup()
        self.t.goto(x, y)
        self.t.pendown()
        for _ in range(3):
            self.t.forward(side)
            self.t.left(120)

    def draw_rectangle(self, x, y, w, h):
        self.t.penup()
        self.t.goto(x, y)
        self.t.pendown()
        for _ in range(2):
            self.t.forward(w)
            self.t.right(90)
            self.t.forward(h)
            self.t.right(90)

    def draw_scene(self):
        self.fill_red()
        self.draw_square(-200, 100, 100)
        self.end_fill()

        self.fill_blue()
        self.draw_circle(100, 100, 50)
        self.end_fill()

        self.fill_green()
        self.draw_triangle(-100, -100, 120)
        self.end_fill()

        self.fill_yellow()
        self.draw_rectangle(150, -50, 120, 80)
        self.end_fill()

def main():
    s = ShapeDrawer()
    s.draw_scene()
    s.screen.exitonclick()

if __name__ == "__main__":
    main()
