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


    # ------------------------------------------------------------
    # Movement (NO name parameter anymore)
    # Backend applies these to active object
    # ------------------------------------------------------------

    # DONE TEST
    def forward(self, distance: int):
        """
        Move forward.

        Phrases: forward, go forward, move forward, advance,
        step forward, go ahead, move ahead.

        Args:
            distance: how far to move forward.
        """
        turtle.forward(distance)

    # DONE TEST
    def backward(self, distance: int):
        """
        Move backward.

        Phrases: back, go back, move back, backward,
        reverse, step back, go backwards.

        Args:
            distance: how far to move backward.
        """
        turtle.backward(distance)

    # DONE TEST
    def left(self, angle: int):
        """
        Turn left.

        Phrases: left, turn left, rotate left, go left.

        Args:
            angle: degrees to turn left.
        """
        turtle.left(angle)

    # DONE TEST
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

    # DONE TEST
    def penup(self):
        """
        Lift the pen so the turtle moves without drawing.

        Phrases: pen up, lift pen, stop drawing, move without drawing.
        """
        turtle.penup()

    # DONE TEST
    def pendown(self):
        """
        Put the pen down so the turtle draws while moving.

        Phrases: pen down, draw, start drawing, resume drawing.
        """
        turtle.pendown()

    # DONE TEST
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

    # DONE TEST
    def speed(self, value: int):
        """
        Set turtle movement speed.

        Phrases: set speed, change speed, faster, slower,
        speed up, slow down.

        Args:
            value: speed value (0 fast, 1-10 common range).
        """
        turtle.speed(value)

    # DONE TEST
    def pensize(self, width: int):
        """
        Set pen thickness.

        Phrases: pen size, pen thickness, thicker line,
        thinner line, line width.

        Args:
            width: pen width.
        """
        turtle.pensize(width)

    # DONE TEST
    def circle(self, radius: int):
        """
        Draw a circle.

        Phrases: draw circle, make a circle, circle.

        Args:
            radius: circle radius.
        """
        turtle.circle(radius)

    # DONE TEST
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

    # DONE TEST
    def home(self):
        """ 
        Move turtle back to the home position (0, 0).

        Phrases: home, go home, go to home, return home, move to home
        return to home, back to center, go back home.

        """
        turtle.home()

    # DONE TEST
    def clear(self):
        """
        Clear drawings made by this turtle.

        Phrases: clear, erase, clean canvas.
        """
        turtle.clear()

    # DONE TEST
    def reset(self):
        """
        Reset turtle (clears and returns to initial state).

        Phrases: reset, restart turtle, reset turtle.
        """
        turtle.reset()

    # DONE TEST
    def pencolor(self, color_name: str):
        """
        Set the turtle pen color only.

        Phrases: set pen color, change pen color, line color,
        make pen red, use blue pen.

        Args:
            color_name: color name like "red", "blue", "black"
            or hex like "#ff0000".
        """
        turtle.pencolor(color_name)

    # DONE TEST
    def fillcolor(self, color_name: str):
        """
        Set the turtle fill color.

        Phrases: set fill color, change fill color, fill with red,
        use blue fill.

        Args:
            color_name: color name like "red", "blue", "black"
            or hex like "#ff0000".
        """
        turtle.fillcolor(color_name)

    # DONE TEST
    def begin_fill(self):
        """
        Start filling the next shape.

        Phrases: begin fill, start fill, fill shape, 
        begin filling, start filling, start color inside,
        start coloring inside.
        """
        turtle.begin_fill()

    # DONE TEST
    def end_fill(self):
        """
        Stop filling and complete the filled shape.

        Phrases: end fill, stop fill, finish fill, 
        end filling, stop filling, finish filling, complete filling,
        end coloring, stop coloring, finish coloring, complete coloring,
        complete fill.
        """
        turtle.end_fill()

    def setheading(self, angle: int):
        """
        Set the turtle heading to a specific angle.

        Phrases: set heading, face to, point to, turn to,
        face angle, point to angle, turn to angle, set angle.

        Args:
            angle: heading angle in degrees.
        """
        turtle.setheading(angle)

    def position(self):
        """
        Get the turtle current position.

        Phrases: position, current position, where is the turtle,
        get position.
        """
        return turtle.position()

    def xcor(self):
        """
        Get the turtle current x coordinate.

        Phrases: x coordinate, current x, get x position,
        horizontal position.
        """
        return turtle.xcor()

    def ycor(self):
        """
        Get the turtle current y coordinate.

        Phrases: y coordinate, current y, get y position,
        vertical position.
        """
        return turtle.ycor()

    def heading(self):
        """
        Get the turtle current heading angle.

        Phrases: heading, current angle, direction angle,
        where is it facing.
        """
        return turtle.heading()

    def dot(self, size: int):
        """
        Draw a dot at the turtle current position.

        Phrases: draw dot, make dot, place dot,
        create a dot.

        Args:
            size: dot size.
        """
        turtle.dot(size)

    def stamp(self):
        """
        Stamp a copy of the turtle shape onto the canvas.

        Phrases: stamp, stamp turtle, leave shape mark,
        print turtle shape.
        """
        return turtle.stamp()

    def clearstamp(self, stamp_id: int):
        """
        Clear one specific stamp from the canvas.

        Phrases: clear stamp, remove stamp, delete stamp.

        Args:
            stamp_id: id of the stamp to remove.
        """
        turtle.clearstamp(stamp_id)

    def clearstamps(self):
        """
        Clear all turtle stamps from the canvas.

        Phrases: clear stamps, remove all stamps,
        delete all stamps.
        """
        turtle.clearstamps()

    def hideturtle(self):
        """
        Hide the turtle cursor.

        Phrases: hide turtle, make turtle invisible,
        disappear turtle.
        """
        turtle.hideturtle()

    def showturtle(self):
        """
        Show the turtle cursor.

        Phrases: show turtle, make turtle visible,
        display turtle.
        """
        turtle.showturtle()

    def shape(self, shape_name: str):
        """
        Set the turtle shape.

        Phrases: set shape, change shape, use turtle shape,
        make shape arrow.

        Args:
            shape_name: shape name like "arrow", "turtle", "circle", or "square".
        """
        turtle.shape(shape_name)

    def shapesize(self, stretch_wid: int, stretch_len: int, outline: int):
        """
        Set the turtle shape size.

        Phrases: shape size, resize turtle, make turtle bigger,
        stretch turtle shape.

        Args:
            stretch_wid: width stretch factor.
            stretch_len: length stretch factor.
            outline: outline thickness.
        """
        turtle.shapesize(stretch_wid, stretch_len, outline)

    def write(self, text: str):
        """
        Write text at the turtle current position.

        Phrases: write, write text, print, print text, display, display text,
        show text, put text on screen, draw text.

        Args:
            text: text to write on the screen.
        """
        turtle.write(text)

    def bgcolor(self, color_name: str):
        """
        Set the screen background color.

        Phrases: background color, set background, change canvas color,
        make background blue.

        Args:
            color_name: color name like "red", "blue", "black"
            or hex like "#ff0000".
        """
        turtle.bgcolor(color_name)

    def title(self, text: str):
        """
        Set the turtle window title.

        Phrases: set title, change window title, name the screen,
        set page title.

        Args:
            text: title text for the turtle window.
        """
        turtle.title(text)

    def isdown(self):
        """
        Check whether the pen is currently down.

        Phrases: is pen down, pen status, drawing status,
        check pen down.
        """
        return turtle.isdown()

    def isvisible(self):
        """
        Check whether the turtle is currently visible.

        Phrases: is turtle visible, visibility status,
        check turtle visible.
        """
        return turtle.isvisible()

    def towards(self, x: int, y: int):
        """
        Get the angle from the turtle to a position.

        Phrases: angle towards, direction to point, face point angle,
        heading to coordinates.

        Args:
            x: x coordinate.
            y: y coordinate.
        """
        return turtle.towards(x, y)

    def distance(self, x: int, y: int):
        """
        Get the distance from the turtle to a position.

        Phrases: distance to point, how far from coordinates,
        measure distance to.

        Args:
            x: x coordinate.
            y: y coordinate.
        """
        return turtle.distance(x, y)

    def setx(self, x: int):
        """
        Set the turtle x coordinate.

        Phrases: set x, move x, change horizontal position,
        go to x.

        Args:
            x: x coordinate.
        """
        turtle.setx(x)

    def sety(self, y: int):
        """
        Set the turtle y coordinate.

        Phrases: set y, move y, change vertical position,
        go to y.

        Args:
            y: y coordinate.
        """
        turtle.sety(y)

    def degrees(self, fullcircle: int):
        """
        Set angle measurement unit to degrees.

        Phrases: use degrees, degree mode, set degrees.

        Args:
            fullcircle: number of units for a full circle, usually 360.
        """
        turtle.degrees(fullcircle)

    def radians(self):
        """
        Set angle measurement unit to radians.

        Phrases: use radians, radian mode, set radians.
        """
        turtle.radians()

    def screensize(self, width: int, height: int):
        """
        Set the drawable canvas size.

        Phrases: screen size, canvas size, resize canvas,
        set drawing area.

        Args:
            width: canvas width.
            height: canvas height.
        """
        turtle.screensize(width, height)

    def setup(self, width: int, height: int, startx: int, starty: int):
        """
        Set the turtle window size and position.

        Phrases: setup screen, set window size, resize window,
        move window position.

        Args:
            width: window width.
            height: window height.
            startx: window start x position.
            starty: window start y position.
        """
        turtle.setup(width, height, startx, starty)

    def clearscreen(self):
        """
        Clear the whole screen and reset turtle state.

        Phrases: clear screen, reset screen, wipe canvas,
        clear everything.
        """
        turtle.clearscreen()

    def resetscreen(self):
        """
        Reset the whole screen to its initial state.

        Phrases: reset screen, restart screen, restore default screen,
        reset everything.
        """
        turtle.resetscreen()
