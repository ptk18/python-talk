from typing import Optional


class Robot:
    """
    Simple programmable robot.

    Phrases: robot, bot, machine, android, smart robot.

    Notes:
    - Designed for NLP phrase matching.
    - Maintains internal battery state.
    - All actions print visible results for runner demo.
    """

    def __init__(self, name: str = "Robo"):
        """
        Create a new robot.

        Phrases: create robot, make robot, new robot, initialize robot,
        start robot, build robot.

        Args:
            name (str): robot name.
        """
        self.name = name
        self.battery = 100
        print(f"[INIT] Robot '{self.name}' created with battery {self.battery}%")

    # ------------------------------------------------------------
    # Basic actions
    # ------------------------------------------------------------

    def say_hello(self) -> None:
        """
        Robot greets.

        Phrases: say hello, greet, introduce yourself, hello.

        Returns:
            None
        """
        print(f"[HELLO] Hello, I am {self.name}")

    def walk(self, steps: int) -> None:
        """
        Walk forward a number of steps.

        Phrases: walk, move forward, go forward, step forward.
        Examples:
          - "walk 10"
          - "move forward 5 steps"

        Args:
            steps (int): number of steps.

        Returns:
            None
        """
        self.battery -= steps
        print(f"[WALK] Walked {steps} steps. Battery: {self.battery}%")

    def turn(self, direction: str) -> None:
        """
        Turn robot in a direction.

        Phrases: turn left, turn right, rotate left, rotate right, turn.
        Examples:
          - "turn left"
          - "rotate right"

        Args:
            direction (str): left or right.

        Returns:
            None
        """
        print(f"[TURN] Turned {direction}")

    def jump(self, height: int) -> None:
        """
        Jump up.

        Phrases: jump, hop, leap.
        Examples:
          - "jump 3"
          - "hop 2"

        Args:
            height (int): jump height.

        Returns:
            None
        """
        self.battery -= height
        print(f"[JUMP] Jumped {height} units. Battery: {self.battery}%")

    # ------------------------------------------------------------
    # Battery control
    # ------------------------------------------------------------

    def charge(self, amount: int) -> None:
        """
        Charge robot battery.

        Phrases: charge, recharge, power up, charge battery.
        Examples:
          - "charge 20"
          - "recharge 50"

        Args:
            amount (int): battery percentage to add.

        Returns:
            None
        """
        self.battery = min(100, self.battery + amount)
        print(f"[CHARGE] Charged {amount}%. Battery: {self.battery}%")

    def battery_status(self) -> int:
        """
        Show battery status.

        Phrases: battery status, battery level, show battery,
        how much battery, remaining battery.

        Returns:
            int: current battery percentage.
        """
        print(f"[BATTERY_STATUS] Battery: {self.battery}%")
        return self.battery

    # ------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------

    def rename(self, new_name: str) -> None:
        """
        Rename robot.

        Phrases: rename, change name, set name, call robot.
        Examples:
          - "rename to Atlas"
          - "change name to Neo"

        Args:
            new_name (str): new robot name.

        Returns:
            None
        """
        old = self.name
        self.name = new_name
        print(f"[RENAME] Robot renamed from {old} to {self.name}")

    def shutdown(self) -> None:
        """
        Shutdown robot.

        Phrases: shutdown, power off, turn off, stop robot.

        Returns:
            None
        """
        print(f"[SHUTDOWN] Robot {self.name} shutting down.")