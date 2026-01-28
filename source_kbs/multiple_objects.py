class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

class SmartHome:
    def turn_light_on(self):
        pass

    def turn_light_off(self):
        pass

def main():
    calc1 = Calculator()
    calc2 = Calculator()
    home = SmartHome()
    
    print(calc1.add(1, 2))
    print(calc2.subtract(5, 3))
    home.turn_light_on()

if __name__ == "__main__":
    main()
