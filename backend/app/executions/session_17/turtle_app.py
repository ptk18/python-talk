# turtle_app.py
# ============================================================
# Turtle Domain for NLP (multi-turtle)
# - TurtleApp manages many turtles
# - Methods have docstrings designed for semantic matching
# ============================================================

import turtle


class TurtleApp:
    """
    Manage multiple turtles by name.

    Notes:
    - The NLP system should map natural language to these methods.
    - Use create_turtle() to make turtles.
    - Use get_turtle() / select_turtle() to choose which turtle to use.
    """

    def __init__(self):
        self.turtles = {}

    # ------------------------------------------------------------
    # Turtle management (IMPORTANT: get_turtle must NOT sound like movement)
    # ------------------------------------------------------------

    def create_turtle(self, name: str):
        """
        Create a new turtle with a given name.

        Phrases: create turtle, make turtle, new turtle, add turtle, spawn turtle, create a turtle named, make a turtle called.

        Args:
            name: the turtle name (example: "left", "right", "top").
        """
        if not name:
            raise ValueError("name must be provided")
        if name in self.turtles:
            raise ValueError(f"Turtle '{name}' already exists")
        self.turtles[name] = turtle.Turtle()
        return f"Created turtle '{name}'"

    def get_turtle(self, name: str):
        """
        Retrieve a turtle by name.

        Phrases: get turtle, select turtle, choose turtle, use turtle named, switch to turtle, pick turtle, set active turtle.

        Args:
            name: the turtle name to retrieve.
        """
        if not name:
            raise ValueError("name must be provided")
        if name not in self.turtles:
            raise ValueError(f"Turtle '{name}' does not exist")
        return self.turtles[name]

    def list_turtles(self):
        """
        Show all existing turtle names.

        Phrases: list turtles, show turtles, what turtles exist, display turtles, all turtles.
        """
        return sorted(self.turtles.keys())

    def delete_turtle(self, name: str):
        """
        Remove a turtle by name.

        Phrases: delete turtle, remove turtle, destroy turtle, drop turtle.

        Args:
            name: the turtle name to remove.
        """
        if not name:
            raise ValueError("name must be provided")
        if name not in self.turtles:
            raise ValueError(f"Turtle '{name}' does not exist")
        del self.turtles[name]
        return f"Deleted turtle '{name}'"

    # ------------------------------------------------------------
    # Movement wrappers (these are what NL should match to)
    # ------------------------------------------------------------

    def turtle_forward(self, name: str, distance: int):
        """
        Move a named turtle forward by a distance.

        Phrases: forward, go forward, move forward, advance, step forward, go ahead, move ahead.

        Args:
            name: turtle name.
            distance: how far to move forward.
        """
        return self.get_turtle(name).forward(distance)

    def turtle_backward(self, name: str, distance: int):
        """
        Move a named turtle backward by a distance.

        Phrases: back, go back, move back, backward, reverse, step back, go backwards.

        Args:
            name: turtle name.
            distance: how far to move backward.
        """
        return self.get_turtle(name).backward(distance)

    def turtle_left(self, name: str, angle: int):
        """
        Turn a named turtle left by an angle (degrees).

        Phrases: left, turn left, rotate left, go left.

        Args:
            name: turtle name.
            angle: degrees to turn left.
        """
        return self.get_turtle(name).left(angle)

    def turtle_right(self, name: str, angle: int):
        """
        Turn a named turtle right by an angle (degrees).

        Phrases: right, turn right, rotate right, go right.

        Args:
            name: turtle name.
            angle: degrees to turn right.
        """
        return self.get_turtle(name).right(angle)

    # ------------------------------------------------------------
    # Pen / drawing
    # ------------------------------------------------------------

    def penup(self, name: str):
        """
        Lift the pen so the turtle moves without drawing.

        Phrases: pen up, lift pen, stop drawing, move without drawing.

        Args:
            name: turtle name.
        """
        return self.get_turtle(name).penup()

    def pendown(self, name: str):
        """
        Put the pen down so the turtle draws while moving.

        Phrases: pen down, draw, start drawing, resume drawing.

        Args:
            name: turtle name.
        """
        return self.get_turtle(name).pendown()

    def set_color(self, name: str, color_name: str):
        """
        Set the turtle pen color.

        Phrases: set color, change color, make it red, use blue, pen color.

        Args:
            name: turtle name.
            color_name: color name like "red", "blue", "black" or hex like "#ff0000".
        """
        return self.get_turtle(name).color(color_name)

    def set_speed(self, name: str, value: int):
        """
        Set turtle movement speed.

        Phrases: set speed, change speed, faster, slower, speed up, slow down.

        Args:
            name: turtle name.
            value: speed value (0 fast, 1-10 common range).
        """
        return self.get_turtle(name).speed(value)

    def set_pensize(self, name: str, width: int):
        """
        Set pen thickness.

        Phrases: pen size, pen thickness, thicker line, thinner line, line width.

        Args:
            name: turtle name.
            width: pen width.
        """
        return self.get_turtle(name).pensize(width)

    def circle(self, name: str, radius: int):
        """
        Draw a circle.

        Phrases: draw circle, make a circle, circle.

        Args:
            name: turtle name.
            radius: circle radius.
        """
        return self.get_turtle(name).circle(radius)

    def goto(self, name: str, x: int, y: int):
        """
        Move turtle to an (x, y) position.

        Phrases: go to, move to, set position, jump to, teleport to.

        Args:
            name: turtle name.
            x: x coordinate.
            y: y coordinate.
        """
        return self.get_turtle(name).goto(x, y)

    def home(self, name: str):
        """
        Move turtle back to the home position (0, 0).

        Phrases: home, go home, return home, back to center.

        Args:
            name: turtle name.
        """
        return self.get_turtle(name).home()

    def clear(self, name: str):
        """
        Clear drawings made by this turtle.

        Phrases: clear, erase, clean canvas for this turtle.

        Args:
            name: turtle name.
        """
        return self.get_turtle(name).clear()

    def reset(self, name: str):
        """
        Reset this turtle (clears and returns to initial state).

        Phrases: reset, restart turtle, reset turtle.

        Args:
            name: turtle name.
        """
        return self.get_turtle(name).reset()