# turtle_app.py
# ============================================================
# Turtle Domain for NLP (multi-turtle)
# - TurtleApp manages many turtles
# - Methods have docstrings designed for semantic matching
# - Movement operates on active turtle (handled by backend)
# ============================================================

import turtle


class TurtleApp:
    """
    Manage multiple turtles by name.

    Notes:
    - The NLP system should map natural language to these methods.
    - Use create_turtle() to make turtles.
    - Backend tracks active turtle in state.json.
    """

    def __init__(self):
        self.turtles = {}

    # ------------------------------------------------------------
    # Turtle management
    # ------------------------------------------------------------

    def create_turtle(self, name: str):
        """
        Create a new turtle with a given name.

        Phrases: create turtle, make turtle, new turtle, add turtle,
        spawn turtle, create a turtle named, make a turtle called.

        Args:
            name: the turtle name (example: "left", "right", "top").
        """
        if not name:
            raise ValueError("name must be provided")
        if name in self.turtles:
            raise ValueError(f"Turtle '{name}' already exists")

        self.turtles[name] = turtle.Turtle()
        return f"Created turtle '{name}'"

    def select_turtle(self, name: str):
        """
        Select which turtle becomes active.

        Phrases: get turtle, select turtle, choose turtle, use turtle,
        switch to turtle, pick turtle, set active turtle.

        Args:
            name: the turtle name to activate.
        """
        if name not in self.turtles:
            raise ValueError(f"Turtle '{name}' does not exist")
        return self.turtles[name]

    def list_turtles(self):
        """
        Show all existing turtle names.

        Phrases: list turtles, show turtles, what turtles exist,
        display turtles, all turtles.
        """
        return sorted(self.turtles.keys())

    def delete_turtle(self, name: str):
        """
        Remove a turtle by name.

        Phrases: delete turtle, remove turtle, destroy turtle, drop turtle.

        Args:
            name: the turtle name to remove.
        """
        if name not in self.turtles:
            raise ValueError(f"Turtle '{name}' does not exist")
        del self.turtles[name]
        return f"Deleted turtle '{name}'"

    # ------------------------------------------------------------
    # Movement (NO name parameter anymore)
    # Backend applies these to active object
    # ------------------------------------------------------------

    def forward(self, distance: int):
        """
        Move forward.

        Phrases: forward, go forward, move forward, advance,
        step forward, go ahead, move ahead.

        Args:
            distance: how far to move forward.
        """
        turtle.forward(distance)

    def backward(self, distance: int):
        """
        Move backward.

        Phrases: back, go back, move back, backward,
        reverse, step back, go backwards.

        Args:
            distance: how far to move backward.
        """
        turtle.backward(distance)

    def left(self, angle: int):
        """
        Turn left.

        Phrases: left, turn left, rotate left, go left.

        Args:
            angle: degrees to turn left.
        """
        turtle.left(angle)

    def right(self, angle: int):
        """
        Turn right.

        Phrases: right, turn right, rotate right, go right.

        Args:
            angle: degrees to turn right.
        """
        turtle.right(angle)

    # ------------------------------------------------------------
    # Pen / drawing
    # ------------------------------------------------------------

    def penup(self):
        """
        Lift the pen so the turtle moves without drawing.

        Phrases: pen up, lift pen, stop drawing, move without drawing.
        """
        turtle.penup()

    def pendown(self):
        """
        Put the pen down so the turtle draws while moving.

        Phrases: pen down, draw, start drawing, resume drawing.
        """
        turtle.pendown()

    def color(self, color_name: str):
        """
        Set the turtle pen color.

        Phrases: set color, change color, make it red, use blue,
        pen color.

        Args:
            color_name: color name like "red", "blue", "black"
            or hex like "#ff0000".
        """
        turtle.color(color_name)

    def speed(self, value: int):
        """
        Set turtle movement speed.

        Phrases: set speed, change speed, faster, slower,
        speed up, slow down.

        Args:
            value: speed value (0 fast, 1-10 common range).
        """
        turtle.speed(value)

    def pensize(self, width: int):
        """
        Set pen thickness.

        Phrases: pen size, pen thickness, thicker line,
        thinner line, line width.

        Args:
            width: pen width.
        """
        turtle.pensize(width)

    def circle(self, radius: int):
        """
        Draw a circle.

        Phrases: draw circle, make a circle, circle.

        Args:
            radius: circle radius.
        """
        turtle.circle(radius)

    def goto(self, x: int, y: int):
        """
        Move turtle to an (x, y) position.

        Phrases: go to, move to, set position,
        jump to, teleport to.

        Args:
            x: x coordinate.
            y: y coordinate.
        """
        turtle.goto(x, y)

    def home(self):
        """
        Move turtle back to the home position (0, 0).

        Phrases: home, go home, return home,
        back to center.
        """
        turtle.home()

    def clear(self):
        """
        Clear drawings made by this turtle.

        Phrases: clear, erase, clean canvas.
        """
        turtle.clear()

    def reset(self):
        """
        Reset turtle (clears and returns to initial state).

        Phrases: reset, restart turtle, reset turtle.
        """
        turtle.reset()