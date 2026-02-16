# How to Write Method Docstrings

## Each method must include:

- A clear action description

- Common phrases users might say

- An Args section if parameters exist

### - Template (No Parameters)
```py
def action_name(self):
    """
    Describe what this action does.

    Phrases: alternative user expressions.
    """
```

### - Template (With Parameters)
```py
def action_name(self, parameter):
    """
    Describe what this action does.

    Phrases: alternative user expressions.

    Args:
        parameter: explanation of this value.
    """
```

- Example: Robot Domain
```py
class Robot:
    """
    A simple robot that can walk and speak.
    """

    def walk(self, steps):
        """
        Move forward a given number of steps.

        Phrases: walk, move, take steps, go forward, advance.

        Args:
            steps: number of steps to move.
        """
        pass

    def speak(self, speech):
        """
        Say the given text out loud.

        Phrases: say, speak, talk, utter.

        Args:
            speech: text to say.
        """
        pass

    def say_hello(self):
        """
        Greet the user.

        Phrases: say hello, greet, introduce yourself, hi.
        """
        pass
```

- Example: Smart Home Domain
```py
class SmartHome:
    """
    A smart home system for controlling devices.
    """

    def turn_tv_on(self):
        """
        Turn on the TV.

        Phrases: turn on tv, switch on television, power on tv, enable tv.
        """
        pass

    def increase_temperature(self, amount):
        """
        Increase the temperature setting.

        Phrases: increase temperature, raise temperature, make warmer.

        Args:
            amount: number of degrees to increase.
        """
        pass
```
- Example: Bank Account Domain
```py
class BankAccount:
    """
    A simple bank account system.
    """

    def deposit(self, amount):
        """
        Add money to the account.

        Phrases: deposit money, add money, top up account.

        Args:
            amount: amount of money to add.
        """
        pass
```

### - What NOT to Do

Avoid short or meaningless docstrings:
```py
"""Turns it on"""
```

Avoid technical implementation details:
```py
"""Updates internal boolean state variable"""
```

Docstrings must describe user-level meaning, not internal logic.

## Key Design Principle

### Docstrings describe:

#### What the user would say, not how the code works.

This makes the system:

-> Domain-independent

-> Extensible

-> Based on semantic similarity

-> Not dependent on hardcoded rules