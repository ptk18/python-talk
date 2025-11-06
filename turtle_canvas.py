import turtle
import random

BRANCH_ANGLE = 25
SHRINK_FACTOR = 0.72
INITIAL_LENGTH = 120
MIN_LENGTH = 6
PENSIZE_START = 12
LEAF_THRESHOLD = 14
BACKGROUND = "#0b1021"
TRUNK_COLOR = "#6b4226"
LEAF_COLORS = ["#2ecc71", "#27ae60", "#1abc9c", "#16a085", "#58d68d"]
WIDTH = 900
HEIGHT = 700
START_Y = -300

def setup_screen():
    screen = turtle.Screen()
    screen.setup(width=WIDTH, height=HEIGHT)
    screen.bgcolor(BACKGROUND)
    screen.title("Turtle Canvas")
    return screen

def create_turtle():
    t = turtle.Turtle(visible=False)
    t.speed(0)
    t.left(90)
    t.penup()
    t.goto(0, START_Y)
    t.pendown()
    return t

def set_color_for_length(t, length):
    if length <= LEAF_THRESHOLD:
        t.pencolor(random.choice(LEAF_COLORS))
    else:
        t.pencolor(TRUNK_COLOR)

def draw_branch(t, length):
    pensize = max(1, int(PENSIZE_START * (length / INITIAL_LENGTH)))
    t.pensize(pensize)
    set_color_for_length(t, length)
    t.forward(length)

def draw_tree(t, length, angle, factor):
    if length < MIN_LENGTH:
        return
    draw_branch(t, length)
    t.left(angle)
    draw_tree(t, length * factor, angle, factor)
    t.right(2 * angle)
    draw_tree(t, length * factor, angle, factor)
    t.left(angle)
    t.backward(length)

def draw_leaves_floor(t, count=120, radius=2):
    old_speed = t.speed()
    t.speed(0)
    t.penup()
    for _ in range(count):
        x = random.randint(-WIDTH//2 + 20, WIDTH//2 - 20)
        y = random.randint(START_Y + 10, START_Y + 120)
        t.goto(x, y)
        t.pendown()
        t.pencolor(random.choice(LEAF_COLORS))
        t.dot(radius + random.randint(0, 2))
        t.penup()
    t.speed(old_speed)

def draw_canvas():
    screen = setup_screen()
    t = create_turtle()
    turtle.tracer(False)
    draw_tree(t, INITIAL_LENGTH, BRANCH_ANGLE, SHRINK_FACTOR)
    draw_leaves_floor(t)
    turtle.tracer(True)
    return screen

def main():
    screen = draw_canvas()
    screen.exitonclick()

if __name__ == "__main__":
    main()
