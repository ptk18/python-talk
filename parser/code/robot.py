class Robot:
    def __init__(self, name="Robo"):
        self.name = name

    def say_hello(self):
        """Greet the user. Phrases: say hello, greet, introduce yourself, hi."""
        print(f"Hello, I am {self.name}")

    def walk(self, steps):
        """Move forward a given number of steps. Phrases: walk, move, take steps, go forward, advance.
        Args:
            steps: number of steps to move.
        """
        self.battery -= steps
        print(f"Walked {steps} steps. Battery: {self.battery}")

    def speak(self, speech):
        """Say the given text out loud. Phrases: say, speak, talk, utter.
        Args:
            speech: text to say.
        """
        print(speech)