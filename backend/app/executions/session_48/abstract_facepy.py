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

        # must match Pi capture region
        self.window_width = 800
        self.window_height = 800
        self.canvas_width = 700
        self.canvas_height = 700

    # -------------------- SCREEN --------------------

    def setup_screen(self):
        self.screen = turtle.Screen()

        # window size + position (CRITICAL)
        self.screen.setup(
            width=self.window_width,
            height=self.window_height,
            startx=50,
            starty=50
        )

        # logical drawing space
        self.screen.screensize(
            self.canvas_width,
            self.canvas_height
        )

        self.screen.bgcolor(self.bgcolor)
        self.screen.title("Abstract Face")

    def create_turtle(self):
        self.t = turtle.Turtle(visible=False)
        self.t.speed(0)
        self.t.pensize(3)

    # -------------------- HELPERS --------------------

    def draw_circle(self, x, y, radius, color):
        self.t.penup()
        self.t.goto(x, y - radius)
        self.t.pendown()
        self.t.fillcolor(color)
        self.t.begin_fill()
        self.t.circle(radius)
        self.t.end_fill()

    # -------------------- FACE --------------------

    def draw_face_outline(self):
        self.draw_circle(0, -30, 220, self.skin_color)

    def draw_eyes(self):
        for x in [-80, 80]:
            self.draw_circle(x, 40, 40, "white")
            self.draw_circle(x, 40, 18, self.eye_color)
            self.draw_circle(x + 8, 55, 5, "white")

    def draw_nose(self):
        self.t.penup()
        self.t.goto(0, 10)
        self.t.setheading(270)
        self.t.pendown()
        self.t.pencolor("#d98c5f")
        self.t.pensize(4)
        for _ in range(20):
            self.t.forward(3)
            self.t.right(2)

    def draw_mouth(self):
        self.t.penup()
        self.t.goto(-50, -100)
        self.t.setheading(-60)
        self.t.pendown()
        self.t.pensize(8)
        self.t.pencolor(self.lip_color)
        for _ in range(40):
            self.t.forward(3)
            self.t.right(3)

    def draw_blush(self):
        for x in [-110, 110]:
            self.draw_circle(x, -10, 25, self.blush_color)

    def draw_hair(self):
        self.t.penup()
        self.t.goto(-200, 150)
        self.t.setheading(60)
        self.t.pendown()
        self.t.fillcolor(self.hair_color)
        self.t.begin_fill()
        for _ in range(2):
            self.t.circle(250, 90)
            self.t.circle(120, 90)
        self.t.end_fill()

    # -------------------- ABSTRACT ELEMENTS --------------------

    def draw_abstract_elements(self):
        colors = ["#9c89b8", "#f0a6ca", "#efc3e6", "#b8bedd"]
        for _ in range(6):
            x = random.randint(-300, 300)
            y = random.randint(-250, 250)
            size = random.randint(40, 90)

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

    # -------------------- MAIN --------------------

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

        # allow stream to capture final frame
        time.sleep(2)

        # auto-exit (IMPORTANT)
        self.screen.bye()


if __name__ == "__main__":
    TurtleAbstractFace().run()
