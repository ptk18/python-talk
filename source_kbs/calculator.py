class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


def main():
    calc = Calculator()
    print(f"2 + 3 = {calc.add(2, 3)}")
    print(f"7 - 4 = {calc.subtract(7, 4)}")
    print(f"6 * 5 = {calc.multiply(6, 5)}")
    print(f"8 / 2 = {calc.divide(8, 2)}")


if __name__ == "__main__":
    main()
