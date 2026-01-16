class SmartHome:
    """Simple smart home system with return-based actions"""

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

    def increase_temperature(self, amount=1):
        self.temperature += amount
        return f"[ACTION] Increasing temperature by {amount}\n[STATE] Temperature: {self.temperature}"

    def decrease_temperature(self, amount=1):
        self.temperature -= amount
        return f"[ACTION] Decreasing temperature by {amount}\n[STATE] Temperature: {self.temperature}"

 
