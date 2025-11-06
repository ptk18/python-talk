import turtle

class SimpleTurtle:
    """Enhanced turtle graphics wrapper with query methods for conditionals"""
    
    def __init__(self, canvas_size=(400, 400)):
        self.screen = turtle.Screen()
        self.screen.setup(width=canvas_size[0], height=canvas_size[1])
        self.screen.title("Turtle Graphics")
        self.t = turtle.Turtle()
        self.t.speed(0)
    
    # Movement methods
    def forward(self, distance: float):
        """Move the turtle forward by the specified distance"""
        self.t.forward(distance)
    
    def backward(self, distance: float):
        """Move the turtle backward by the specified distance"""
        self.t.backward(distance)
    
    def left(self, angle: float):
        """Turn the turtle left by the specified angle in degrees"""
        self.t.left(angle)
    
    def right(self, angle: float):
        """Turn the turtle right by the specified angle in degrees"""
        self.t.right(angle)
    
    def goto(self, x: float, y: float):
        """Move the turtle to the specified x, y position"""
        self.t.goto(x, y)
    
    def home(self):
        """Move the turtle to the origin (0, 0) and reset heading"""
        self.t.home()
    
    # Drawing methods
    def circle(self, radius: float):
        """Draw a circle with the specified radius"""
        self.t.circle(radius)
    
    def dot(self, size: int = None):
        """Draw a dot at the current position"""
        if size:
            self.t.dot(size)
        else:
            self.t.dot()
    
    # Pen control
    def penup(self):
        """Lift the pen up (stop drawing)"""
        self.t.penup()
    
    def pendown(self):
        """Put the pen down (start drawing)"""
        self.t.pendown()
    
    def color(self, color_name: str):
        """Set the pen color"""
        self.t.color(color_name)
    
    def pensize(self, width: int):
        """Set the pen width"""
        self.t.pensize(width)
    
    # Query methods for conditionals
    def get_position(self):
        """Get the current (x, y) position of the turtle"""
        return self.t.position()
    
    def get_x(self):
        """Get the current x coordinate"""
        return self.t.xcor()
    
    def get_y(self):
        """Get the current y coordinate"""
        return self.t.ycor()
    
    def get_heading(self):
        """Get the current heading in degrees (0-360)"""
        return self.t.heading()
    
    def is_pen_down(self):
        """Check if the pen is currently down (drawing)"""
        return self.t.isdown()
    
    def get_color(self):
        """Get the current pen color"""
        return self.t.pencolor()
    
    def get_pensize(self):
        """Get the current pen width"""
        return self.t.pensize()
    
    def is_at_origin(self):
        """Check if turtle is at origin (0, 0)"""
        pos = self.t.position()
        return abs(pos[0]) < 0.1 and abs(pos[1]) < 0.1
    
    def is_facing_north(self):
        """Check if turtle is facing north (heading = 90)"""
        return abs(self.t.heading() - 90) < 1
    
    def is_facing_south(self):
        """Check if turtle is facing south (heading = 270)"""
        return abs(self.t.heading() - 270) < 1
    
    def is_facing_east(self):
        """Check if turtle is facing east (heading = 0)"""
        heading = self.t.heading()
        return abs(heading) < 1 or abs(heading - 360) < 1
    
    def is_facing_west(self):
        """Check if turtle is facing west (heading = 180)"""
        return abs(self.t.heading() - 180) < 1
    
    def distance_from_origin(self):
        """Calculate distance from origin (0, 0)"""
        pos = self.t.position()
        return (pos[0]**2 + pos[1]**2)**0.5
    
    def is_in_quadrant(self, quadrant: int):
        """Check if turtle is in specified quadrant (1-4)"""
        x, y = self.t.xcor(), self.t.ycor()
        if quadrant == 1:
            return x > 0 and y > 0
        elif quadrant == 2:
            return x < 0 and y > 0
        elif quadrant == 3:
            return x < 0 and y < 0
        elif quadrant == 4:
            return x > 0 and y < 0
        return False
    
    def is_within_bounds(self, x_min: float, x_max: float, y_min: float, y_max: float):
        """Check if turtle position is within specified bounds"""
        x, y = self.t.xcor(), self.t.ycor()
        return x_min <= x <= x_max and y_min <= y <= y_max
    
    # Visual control
    def clear(self):
        """Clear all drawings"""
        self.t.clear()
    
    def reset(self):
        """Reset turtle to initial state"""
        self.t.reset()
    
    def show(self):
        """Display the turtle graphics window"""
        self.screen.exitonclick()
    
    def hide_turtle(self):
        """Hide the turtle cursor"""
        self.t.hideturtle()
    
    def show_turtle(self):
        """Show the turtle cursor"""
        self.t.showturtle()
    
    def is_visible(self):
        """Check if turtle cursor is visible"""
        return self.t.isvisible()
    
    # Utility methods
    def get_state(self):
        """Get comprehensive turtle state"""
        return {
            "position": self.get_position(),
            "x": self.get_x(),
            "y": self.get_y(),
            "heading": self.get_heading(),
            "pen_down": self.is_pen_down(),
            "color": self.get_color(),
            "pensize": self.get_pensize(),
            "visible": self.is_visible()
        }


def main():
    turtle_bot = SimpleTurtle()
    
    # Test query methods
    print("Initial state:")
    print(f"  Position: {turtle_bot.get_position()}")
    print(f"  Heading: {turtle_bot.get_heading()}°")
    print(f"  At origin? {turtle_bot.is_at_origin()}")
    print(f"  Pen down? {turtle_bot.is_pen_down()}")
    print(f"  Color: {turtle_bot.get_color()}")
    
    # Draw and test
    turtle_bot.color("red")
    turtle_bot.forward(100)
    turtle_bot.left(90)
    turtle_bot.forward(100)
    
    print(f"\nAfter drawing:")
    print(f"  Position: {turtle_bot.get_position()}")
    print(f"  X: {turtle_bot.get_x()}, Y: {turtle_bot.get_y()}")
    print(f"  Heading: {turtle_bot.get_heading()}°")
    print(f"  In quadrant 1? {turtle_bot.is_in_quadrant(1)}")
    print(f"  Distance from origin: {turtle_bot.distance_from_origin():.2f}")
    print(f"  Facing north? {turtle_bot.is_facing_north()}")
    
    print(f"\nComplete state: {turtle_bot.get_state()}")
    
    turtle_bot.show()


if __name__ == "__main__":
    main()