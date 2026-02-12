# parser/code/smarthome.py
# ============================================================
# SmartHome domain for docstring-similarity command mapping
# IMPORTANT: Add docstrings with user phrases.
# ============================================================

class SmartHome:
    """
    A simple smart home system for controlling devices (light, tv, ac, temperature).
    """

    def __init__(self):
        """Initialize smart home state."""
        self.light_on = False
        self.tv_on = False
        self.ac_on = False
        self.temperature = 24

    def turn_light_on(self):
        """
        Turn on the light (lamp).
        Phrases: turn on light, switch on lamp, enable light, power on light.
        """
        self.light_on = True
        return "[ACTION] Turning light ON\n[STATE] Light on: True"

    def turn_light_off(self):
        """
        Turn off the light (lamp).
        Phrases: turn off light, switch off lamp, disable light, power off light.
        """
        self.light_on = False
        return "[ACTION] Turning light OFF\n[STATE] Light on: False"

    def turn_tv_on(self):
        """
        Turn on the TV (television).
        Phrases: turn on tv, switch on television, power on tv, enable television.
        """
        self.tv_on = True
        return "[ACTION] Turning TV ON\n[STATE] TV on: True"

    def turn_tv_off(self):
        """
        Turn off the TV (television).
        Phrases: turn off tv, switch off television, power off tv, disable television.
        """
        self.tv_on = False
        return "[ACTION] Turning TV OFF\n[STATE] TV on: False"

    def turn_ac_on(self):
        """
        Turn on the air conditioner (AC).
        Phrases: turn on ac, switch on air conditioner, power on ac, enable cooling.
        """
        self.ac_on = True
        return "[ACTION] Turning AC ON\n[STATE] AC on: True"

    def turn_ac_off(self):
        """
        Turn off the air conditioner (AC).
        Phrases: turn off ac, switch off air conditioner, power off ac, disable cooling.
        """
        self.ac_on = False
        return "[ACTION] Turning AC OFF\n[STATE] AC on: False"

    def increase_temperature(self, amount: int = 1):
        """
        Increase the temperature setting by a given number of degrees.
        Phrases: increase temperature, raise temperature, make warmer, turn up heat.

        Args:
            amount: number of degrees to increase (default 1).
        """
        self.temperature += amount
        return f"[ACTION] Increasing temperature by {amount}\n[STATE] Temperature: {self.temperature}"

    def decrease_temperature(self, amount: int = 1):
        """
        Decrease the temperature setting by a given number of degrees.
        Phrases: decrease temperature, lower temperature, make cooler, turn down heat.

        Args:
            amount: number of degrees to decrease (default 1).
        """
        self.temperature -= amount
        return f"[ACTION] Decreasing temperature by {amount}\n[STATE] Temperature: {self.temperature}"


# ------------------------------------------------------------
# Suggested tests (for test_runner.py) + expected generated_code
# ------------------------------------------------------------
# "turn on the light"          -> smarthome.turn_light_on()
# "switch off the tv"          -> smarthome.turn_tv_off()
# "power on television"        -> smarthome.turn_tv_on()
# "increase temperature by 2"  -> smarthome.increase_temperature(2)
# "make it warmer by 3 degrees"-> smarthome.increase_temperature(3)
# "decrease temperature 1"     -> smarthome.decrease_temperature(1)
