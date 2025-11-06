import turtle
import math
import random

# ---------- Config ----------
WIDTH, HEIGHT = 900, 700
BACKGROUND = "#0b1021"
TRUNK_COLOR = "#704214"
LEAF_COLORS = ["#3FBF3F", "#2DB84D", "#1FAF62", "#7ACB5A", "#5AC46B"]

MAX_DEPTH = 10          # recursion depth
INITIAL_LENGTH = 120    # trunk length
ANGLE = 26              # base branching angle
SHRINK = 0.72           # length multiplier per level
WOBBLE = 6              # random angle wobble (degrees)
SPREAD = 0.15           # random asymmetry on branch lengths (0–0.3 recommended)
MIN_LENGTH_FOR_LEAVES = 12

# ---------- Setup ----------
screen = turtle.Screen()
screen.setup(WIDTH, HEIGHT)
screen.bgcolor(BACKGROUND)
screen.title("Recursive Tree (turtle)")

t = turtle.Turtle(visible=False)
t.speed(0)
t.penup()
t.setpos(0, -HEIGHT // 2 + 40)
t.setheading(90)
t.pendown()
t.color(TRUNK_COLOR)
turtle.tracer(0, 0)

# ---------- Helpers ----------
def set_thickness(len_seg):
    thickness = max(1, int(len_seg * 0.08))
    t.width(thickness)

def draw_leaf():
    t.dot(random.randint(4, 8), random.choice(LEAF_COLORS))

def branch(length, depth):
    if depth == 0 or length < 2:
        return

    set_thickness(length)
    t.pencolor(TRUNK_COLOR)

    t.forward(length)

    if length < MIN_LENGTH_FOR_LEAVES:
        for _ in range(random.randint(1, 3)):
            draw_leaf()

    new_length_left = length * SHRINK * (1.0 + random.uniform(-SPREAD, SPREAD))
    new_length_right = length * SHRINK * (1.0 + random.uniform(-SPREAD, SPREAD))

    t.left(ANGLE + random.uniform(-WOBBLE, WOBBLE))
    branch(new_length_left, depth - 1)
    t.right(ANGLE * 2 + random.uniform(-WOBBLE, WOBBLE))
    branch(new_length_right, depth - 1)
    t.left(ANGLE + random.uniform(-WOBBLE, WOBBLE))

    t.penup()
    t.backward(length)
    t.pendown()

def draw_ground():
    g = turtle.Turtle(visible=False)
    g.speed(0)
    g.penup()
    g.setpos(-WIDTH//2, -HEIGHT//2 + 20)
    g.pendown()
    g.color("#25331f")
    g.begin_fill()
    for _ in range(2):
        g.forward(WIDTH)
        g.right(90)
        g.forward(60)
        g.right(90)
    g.end_fill()

def main():
    draw_ground()
    branch(INITIAL_LENGTH, MAX_DEPTH)
    turtle.update()
    turtle.done()

if __name__ == "__main__":
    main()
