# ============================================================
# turtle_app.py
# Domain Definition for NLP + Runner
# Supports multiple turtle instances + management commands
# ============================================================

class Turtle:
    """
    Represents a single turtle instance.
    Each object maintains its own state.
    """

    def __init__(self, name: str):
        """Create a new turtle with a given name."""
        self.name = name

    # ------------------------------------------------------------
    # Movement Commands
    # ------------------------------------------------------------

    def forward(self, distance: int):
        """Move this turtle forward by the given distance."""
        return f"{self.name}.forward({distance})"

    def backward(self, distance: int):
        """Move this turtle backward by the given distance."""
        return f"{self.name}.backward({distance})"

    def left(self, angle: int):
        """Turn this turtle left by the given angle in degrees."""
        return f"{self.name}.left({angle})"

    def right(self, angle: int):
        """Turn this turtle right by the given angle in degrees."""
        return f"{self.name}.right({angle})"

    # ------------------------------------------------------------
    # Pen Control
    # ------------------------------------------------------------

    def penup(self):
        """Lift the pen up so the turtle does not draw."""
        return f"{self.name}.penup()"

    def pendown(self):
        """Put the pen down so the turtle draws while moving."""
        return f"{self.name}.pendown()"

    # ------------------------------------------------------------
    # Positioning
    # ------------------------------------------------------------

    def goto(self, x: int, y: int):
        """Move this turtle to coordinate (x, y)."""
        return f"{self.name}.goto({x}, {y})"

    def home(self):
        """Return this turtle to origin (0, 0)."""
        return f"{self.name}.home()"

    # ------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------

    def circle(self, radius: int):
        """Draw a circle with the given radius."""
        return f"{self.name}.circle({radius})"

    # ------------------------------------------------------------
    # Style Commands
    # ------------------------------------------------------------

    def color(self, color_name: str):
        """
        Set this turtle's pen color.
        Examples: red, blue, green, black, "#ff0000"
        """
        return f"{self.name}.color({color_name!r})"

    def speed(self, value: int):
        """
        Set this turtle's speed.
        Typical range: 0 (fastest) to 10 (slowest in some configs).
        """
        return f"{self.name}.speed({value})"

    def pensize(self, width: int):
        """Set this turtle's pen width (thickness)."""
        return f"{self.name}.pensize({width})"

    # ------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------

    def hideturtle(self):
        """Hide this turtle cursor."""
        return f"{self.name}.hideturtle()"

    def showturtle(self):
        """Show this turtle cursor."""
        return f"{self.name}.showturtle()"

    # ------------------------------------------------------------
    # Canvas Control
    # ------------------------------------------------------------

    def clear(self):
        """Clear this turtle's drawings."""
        return f"{self.name}.clear()"

    def reset(self):
        """Reset this turtle to initial state."""
        return f"{self.name}.reset()"


# ============================================================
# Factory / Manager
# ============================================================

class TurtleApp:
    """
    TurtleApp manages multiple turtle instances.
    This is the "domain file" your NLP introspects.
    """

    def __init__(self):
        self.turtles = {}

    # ------------------------------------------------------------
    # Turtle lifecycle / management
    # ------------------------------------------------------------

    def create_turtle(self, name: str):
        """Create a new turtle with a unique name."""
        if name in self.turtles:
            raise ValueError(f"Turtle '{name}' already exists.")
        self.turtles[name] = Turtle(name)
        return f"Turtle '{name}' created."

    def delete_turtle(self, name: str):
        """Delete an existing turtle by name."""
        if name not in self.turtles:
            raise ValueError(f"Turtle '{name}' does not exist.")
        del self.turtles[name]
        return f"Turtle '{name}' deleted."

    def list_turtles(self):
        """List all existing turtle names."""
        names = sorted(self.turtles.keys())
        return names

    def get_turtle(self, name: str):
        """Retrieve an existing turtle by name."""
        if name not in self.turtles:
            raise ValueError(f"Turtle '{name}' does not exist.")
        return self.turtles[name]

    # ------------------------------------------------------------
    # Convenience wrappers (optional, helps NLP)
    # These let users say "set leo color red" without needing get_turtle in the NL.
    # ------------------------------------------------------------

    def turtle_forward(self, name: str, distance: int):
        """Move a named turtle forward by distance."""
        return self.get_turtle(name).forward(distance)

    def turtle_backward(self, name: str, distance: int):
        """Move a named turtle backward by distance."""
        return self.get_turtle(name).backward(distance)

    def turtle_left(self, name: str, angle: int):
        """Turn a named turtle left by angle degrees."""
        return self.get_turtle(name).left(angle)

    def turtle_right(self, name: str, angle: int):
        """Turn a named turtle right by angle degrees."""
        return self.get_turtle(name).right(angle)

    def set_turtle_color(self, name: str, color_name: str):
        """Set a named turtle's color."""
        return self.get_turtle(name).color(color_name)

    def set_turtle_speed(self, name: str, value: int):
        """Set a named turtle's speed."""
        return self.get_turtle(name).speed(value)

    def set_turtle_pensize(self, name: str, width: int):
        """Set a named turtle's pen thickness."""
        return self.get_turtle(name).pensize(width)