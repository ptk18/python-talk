import turtle
import random

class TurtleTree:
    def __init__(self):
        self.branch_angle = 25
        self.shrink_factor = 0.72
        self.initial_length = 120
        self.min_length = 6
        self.pensize_start = 12
        self.leaf_threshold = 14
        self.background = "#0b1021"
        self.trunk_color = "#6b4226"
        self.leaf_colors = ["#2ecc71", "#27ae60", "#1abc9c", "#16a085", "#58d68d"]
        self.width = 900
        self.height = 700
        self.start_y = -300
        self.screen = None
        self.t = None

    def setup_screen(self):
        self.screen = turtle.Screen()
        self.screen.setup(800, 800, 50, 50)
        self.screen.screensize(700, 700)
        self.screen.bgcolor(self.background)
        self.screen.title("Turtle Canvas")

    def create_turtle(self):
        self.t = turtle.Turtle(visible=False)
        self.t.speed(0)
        self.t.left(90)
        self.t.penup()
        self.t.goto(0, self.start_y)
        self.t.pendown()

    def set_color_for_length(self, length):
        if length <= self.leaf_threshold:
            self.t.pencolor(random.choice(self.leaf_colors))
        else:
            self.t.pencolor(self.trunk_color)

    def draw_branch(self, length):
        pensize = max(1, int(self.pensize_start * (length / self.initial_length)))
        self.t.pensize(pensize)
        self.set_color_for_length(length)
        self.t.forward(length)

    def draw_tree(self, length):
        if length < self.min_length:
            return
        self.draw_branch(length)
        self.t.left(self.branch_angle)
        self.draw_tree(length * self.shrink_factor)
        self.t.right(2 * self.branch_angle)
        self.draw_tree(length * self.shrink_factor)
        self.t.left(self.branch_angle)
        self.t.backward(length)

    def draw_leaves_floor(self, count=120, radius=2):
        old_speed = self.t.speed()
        self.t.speed(0)
        self.t.penup()
        for _ in range(count):
            x = random.randint(-self.width // 2 + 20, self.width // 2 - 20)
            y = random.randint(self.start_y + 10, self.start_y + 120)
            self.t.goto(x, y)
            self.t.pendown()
            self.t.pencolor(random.choice(self.leaf_colors))
            self.t.dot(radius + random.randint(0, 2))
            self.t.penup()
        self.t.speed(old_speed)

    def draw_canvas(self):
        self.setup_screen()
        self.create_turtle()
        turtle.tracer(False)
        self.draw_tree(self.initial_length)
        self.draw_leaves_floor()
        turtle.tracer(True)

    def run(self):
        self.draw_canvas()
        self.screen.exitonclick()


if __name__ == "__main__":
    TurtleTree().run()
