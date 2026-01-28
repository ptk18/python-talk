import turtle as t

screen = t.Screen()
screen.setup(800, 800, 50, 50)

screen.screensize(700, 700)

def square(x = 20):
    for _ in range(4):
        t.forward(x)
        t.lt(90)
        
def drawIt():
    for _ in range(4):
        for i in range(4):
            square(20*(i+1))
            t.lt(90)
        t.lt(90)
            
if __name__ == "__main__":
    drawIt()
    # Keep the window open for streaming
    screen.exitonclick()  # Close when clicked
    # Or use screen.mainloop() to keep it open indefinitely