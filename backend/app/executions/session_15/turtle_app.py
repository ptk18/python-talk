# turtle_app.py
import turtle

class TurtleApp:
    """
    Multi-turtle domain.

    Movement commands DO NOT take a name.
    The backend will apply them to state.json active_object.
    """

    # -----------------------------
    # Turtle management
    # -----------------------------

    def create_turtle(self, name: str):
        """
        Create a new turtle variable in runner.py and make it active.

        Phrases: create turtle, make turtle, new turtle, add turtle, spawn turtle, create turtle named, make turtle called.

        Args:
            name: turtle variable name (example: top, left, right).
        """
        pass

    def select_turtle(self, name: str):
        """
        Choose which turtle is active.

        Phrases: select turtle, use turtle, switch turtle, choose turtle, set active turtle, focus on turtle.

        Args:
            name: turtle variable name to activate.
        """
        pass

    def list_turtles(self):
        """
        Show all turtle names.

        Phrases: list turtles, show turtles, what turtles exist, display turtles, all turtles.
        """
        pass

    def delete_turtle(self, name: str):
        """
        Delete a turtle by name.

        Phrases: delete turtle, remove turtle, destroy turtle, drop turtle.

        Args:
            name: turtle variable name to remove.
        """
        pass

    # -----------------------------
    # Movement (NO name param)
    # -----------------------------

    def turtle_forward(self, distance: int):
        """
        Move forward.

        Phrases: forward, go forward, move forward, advance, step forward, go ahead, move ahead.

        Args:
            distance: how far to move.
        """
        pass

    def turtle_backward(self, distance: int):
        """
        Move backward.

        Phrases: back, go back, move back, backward, reverse, step back, go backwards.

        Args:
            distance: how far to move back.
        """
        pass

    def turtle_left(self, angle: int):
        """
        Turn left.

        Phrases: left, turn left, rotate left.

        Args:
            angle: degrees to turn.
        """
        pass

    def turtle_right(self, angle: int):
        """
        Turn right.

        Phrases: right, turn right, rotate right.

        Args:
            angle: degrees to turn.
        """
        pass

    # -----------------------------
    # Pen / drawing (NO name param)
    # -----------------------------

    def penup(self):
        """
        Lift the pen (move without drawing).

        Phrases: pen up, lift pen, stop drawing, move without drawing.
        """
        pass

    def pendown(self):
        """
        Put the pen down (draw while moving).

        Phrases: pen down, draw, start drawing, resume drawing.
        """
        pass

    def set_color(self, color_name: str):
        """
        Set pen color.

        Phrases: set color, change color, make it red, use blue, pen color.

        Args:
            color_name: color like red, blue, black, or #ff0000.
        """
        pass

    def set_speed(self, value: int):
        """
        Set speed.

        Phrases: set speed, change speed, faster, slower, speed up, slow down.

        Args:
            value: speed value.
        """
        pass

    def set_pensize(self, width: int):
        """
        Set pen thickness.

        Phrases: pen size, pen thickness, thicker line, thinner line, line width.

        Args:
            width: pen width.
        """
        pass

    def circle(self, radius: int):
        """
        Draw a circle.

        Phrases: draw circle, make a circle, circle.

        Args:
            radius: circle radius.
        """
        pass

    def goto(self, x: int, y: int):
        """
        Go to position (x, y).

        Phrases: go to, move to, set position, jump to, teleport to.

        Args:
            x: x coordinate.
            y: y coordinate.
        """
        pass

    def home(self):
        """
        Go home (0,0).

        Phrases: home, go home, return home, back to center.
        """
        pass

    def clear(self):
        """
        Clear drawings.

        Phrases: clear, erase, clean canvas.
        """
        pass

    def reset(self):
        """
        Reset turtle.

        Phrases: reset, restart turtle, reset turtle.
        """
        pass