class SmartHome:
    """Simple smart home system with return-based actions"""

    def __init__(self):
        self.light_on = False
        self.tv_on = False
        self.ac_on = False
        self.temperature = 24

    # Light control
    def turn_light_on(self):
        self.light_on = True
        return "[ACTION] Turning light ON\n[STATE] Light on: True"

    def turn_light_off(self):
        self.light_on = False
        return "[ACTION] Turning light OFF\n[STATE] Light on: False"

    # TV control
    def turn_tv_on(self):
        self.tv_on = True
        return "[ACTION] Turning TV ON\n[STATE] TV on: True"

    def turn_tv_off(self):
        self.tv_on = False
        return "[ACTION] Turning TV OFF\n[STATE] TV on: False"

    # AC control
    def turn_ac_on(self):
        self.ac_on = True
        return "[ACTION] Turning AC ON\n[STATE] AC on: True"

    def turn_ac_off(self):
        self.ac_on = False
        return "[ACTION] Turning AC OFF\n[STATE] AC on: False"

    # Temperature control
    def set_temperature(self, value):
        self.temperature = value
        return f"[ACTION] Setting temperature to {value}\n[STATE] Temperature: {self.temperature}"

    def increase_temperature(self, amount=1):
        self.temperature += amount
        return f"[ACTION] Increasing temperature by {amount}\n[STATE] Temperature: {self.temperature}"

    def decrease_temperature(self, amount=1):
        self.temperature -= amount
        return f"[ACTION] Decreasing temperature by {amount}\n[STATE] Temperature: {self.temperature}"

    # Queries
    def get_temperature(self):
        return self.temperature

    def is_light_on(self):
        return self.light_on

    def is_tv_on(self):
        return self.tv_on

    def is_ac_on(self):
        return self.ac_on

    def count_devices_on(self):
        return int(self.light_on) + int(self.tv_on) + int(self.ac_on)

    def are_all_devices_off(self):
        return not (self.light_on or self.tv_on or self.ac_on)

    # Status
    def status(self):
        return {
            "light": "on" if self.light_on else "off",
            "tv": "on" if self.tv_on else "off",
            "ac": "on" if self.ac_on else "off",
            "temperature": self.temperature,
            "devices_on": self.count_devices_on()
        }

    # Convenience
    def turn_all_on(self):
        return "\n".join([
            "[ACTION] Turning ALL devices ON",
            self.turn_light_on(),
            self.turn_tv_on(),
            self.turn_ac_on()
        ])

    def turn_all_off(self):
        return "\n".join([
            "[ACTION] Turning ALL devices OFF",
            self.turn_light_off(),
            self.turn_tv_off(),
            self.turn_ac_off()
        ])
