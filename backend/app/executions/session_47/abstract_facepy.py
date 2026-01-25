import turtle
import random
import time

class TurtleAbstractFace:
    def __init__(self):
        self.bgcolor = "#f0e6dc"
        self.skin_color = "#f7c59f"
        self.eye_color = "#4b3f72"
        self.lip_color = "#c94c4c"
        self.hair_color = "#2f1b0c"
        self.blush_color = "#f7a9a8"
        self.screen = None
        self.t = None
        self.width = 1000
        self.height = 700

    def setup_screen(self):
        self.screen = turtle.Screen()
        self.screen.setup(width=self.width, height=self.height)
        self.screen.bgcolor(self.bgcolor)
        self.screen.title("Abstract Face")

    def create_turtle(self):
        self.t = turtle.Turtle(visible=False)
        self.t.speed(0)
        self.t.pensize(3)

    def draw_circle(self, x, y, radius, color):
        self.t.penup()
        self.t.goto(x, y - radius)
        self.t.pendown()
        self.t.fillcolor(color)
        self.t.begin_fill()
        self.t.circle(radius)
        self.t.end_fill()

    def draw_face_outline(self):
        # face oval
        self.t.penup()
        self.t.goto(0, -200)
        self.t.setheading(0)
        self.t.pendown()
        self.t.fillcolor(self.skin_color)
        self.t.begin_fill()
        self.t.seth(90)
        for i in range(180):
            self.t.forward(2)
            self.t.left(1)
        self.t.end_fill()

    def draw_eyes(self):
        # white eye base
        for x in [-80, 80]:
            self.draw_circle(x, 30, 40, "white")
            self.draw_circle(x, 30, 20, self.eye_color)
            # sparkle
            self.draw_circle(x + 10, 45, 5, "white")

    def draw_nose(self):
        self.t.penup()
        self.t.goto(0, -30)
        self.t.setheading(270)
        self.t.pendown()
        self.t.pencolor("#d98c5f")
        self.t.pensize(4)
        for _ in range(10):
            self.t.forward(5)
            self.t.right(3)
        for _ in range(8):
            self.t.forward(5)
            self.t.left(6)

    def draw_mouth(self):
        self.t.penup()
        self.t.goto(-50, -90)
        self.t.setheading(-60)
        self.t.pendown()
        self.t.pensize(8)
        self.t.pencolor(self.lip_color)
        for _ in range(40):
            self.t.forward(3)
            self.t.right(3)

    def draw_hair(self):
        self.t.penup()
        self.t.goto(-150, 130)
        self.t.setheading(120)
        self.t.pendown()
        self.t.fillcolor(self.hair_color)
        self.t.begin_fill()
        for _ in range(2):
            self.t.circle(200, 90)
            self.t.circle(100, 90)
        self.t.end_fill()

    def draw_blush(self):
        for x in [-100, 100]:
            self.draw_circle(x, -10, 25, self.blush_color)

    def draw_abstract_elements(self):
        # random colored geometric shapes for artistic touch
        colors = ["#9c89b8", "#f0a6ca", "#efc3e6", "#f0e6ef", "#b8bedd"]
        for _ in range(8):
            x = random.randint(-400, 400)
            y = random.randint(-250, 250)
            size = random.randint(30, 80)
            self.t.penup()
            self.t.goto(x, y)
            self.t.setheading(random.randint(0, 360))
            self.t.pendown()
            self.t.fillcolor(random.choice(colors))
            self.t.begin_fill()
            for _ in range(3):
                self.t.forward(size)
                self.t.left(120)
            self.t.end_fill()

    def draw_canvas(self):
        self.setup_screen()
        self.create_turtle()
        turtle.tracer(False)

        self.draw_abstract_elements()
        self.draw_hair()
        self.draw_face_outline()
        self.draw_eyes()
        self.draw_blush()
        self.draw_nose()
        self.draw_mouth()

        turtle.tracer(True)

    def run(self):
        self.draw_canvas()
        self.screen.update()
        time.sleep(2)
        self.screen.bye()


if __name__ == "__main__":
    TurtleAbstractFace().run()
