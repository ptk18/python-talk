class SmartHome:
    """Enhanced smart home system with comprehensive query methods for conditionals"""
    
    def __init__(self):
        self.light_on = False
        self.tv_on = False
        self.ac_on = False
        self.temperature = 24

    # Light control methods
    def turn_light_on(self):
        """Turn the light on"""
        self.light_on = True
        return ("Light is:", self.is_light_on())

    def turn_light_off(self):
        """Turn the light off"""
        self.light_on = False
        return ("Light is:", self.is_light_on())
    
    def toggle_light(self):
        """Toggle the light state"""
        self.light_on = not self.light_on

    # TV control methods
    def turn_tv_on(self):
        """Turn the TV on"""
        self.tv_on = True
        return ("TV is:", self.is_tv_on())

    def turn_tv_off(self):
        """Turn the TV off"""
        self.tv_on = False
        return ("TV is:", self.is_tv_on())

    def toggle_tv(self):
        """Toggle the TV state"""
        self.tv_on = not self.tv_on
        return ("TV is:", self.is_tv_on())

    # AC control methods
    def turn_ac_on(self):
        """Turn the AC on"""
        self.ac_on = True
        return ("AC is:", self.is_ac_on())

    def turn_ac_off(self):
        """Turn the AC off"""
        self.ac_on = False
        return ("AC is:", self.is_ac_on())
    
    def toggle_ac(self):
        """Toggle the AC state"""
        self.ac_on = not self.ac_on
        return ("AC is:", self.is_ac_on())

    # Temperature control
    def set_temperature(self, value):
        """Set the target temperature"""
        self.temperature = value
        return ("Temperature set to:", self.temperature)
    
    def increase_temperature(self, amount=1):
        """Increase temperature by specified amount (default: 1)"""
        self.temperature += amount
        return ("Temperature increased to:", self.temperature)
    
    def decrease_temperature(self, amount=1):
        """Decrease temperature by specified amount (default: 1)"""
        self.temperature -= amount
        return ("Temperature decreased to:", self.temperature)

    # Query methods for conditionals
    def get_temperature(self):
        """Get the current temperature setting"""
        return ("Current temperature is:", self.temperature)
    
    def is_light_on(self):
        """Check if the light is currently on"""
        return self.light_on
    
    def is_tv_on(self):
        """Check if the TV is currently on"""
        return self.tv_on
    
    def is_ac_on(self):
        """Check if the AC is currently on"""
        return self.ac_on
    
    def is_hot(self, threshold=26):
        """Check if temperature is above threshold (default: 26)"""
        return self.temperature > threshold
    
    def is_cold(self, threshold=20):
        """Check if temperature is below threshold (default: 20)"""
        return self.temperature < threshold
    
    def is_comfortable(self, min_temp=20, max_temp=26):
        """Check if temperature is in comfortable range (default: 20-26)"""
        return min_temp <= self.temperature <= max_temp
    
    def count_devices_on(self):
        """Count how many devices are currently on"""
        count = 0
        if self.light_on:
            count += 1
        if self.tv_on:
            count += 1
        if self.ac_on:
            count += 1
        return count
    
    def is_any_device_on(self):
        """Check if any device is on"""
        return self.light_on or self.tv_on or self.ac_on
    
    def are_all_devices_off(self):
        """Check if all devices are off"""
        return not (self.light_on or self.tv_on or self.ac_on)

    # Comprehensive status
    def status(self):
        """Get complete system status"""
        return {
            "light": "on" if self.light_on else "off",
            "tv": "on" if self.tv_on else "off",
            "ac": "on" if self.ac_on else "off",
            "temperature": self.temperature,
            "devices_on": self.count_devices_on()
        }
    
    # Convenience methods
    def turn_all_on(self):
        """Turn all devices on"""
        self.turn_light_on()
        self.turn_tv_on()
        self.turn_ac_on()
    
    def turn_all_off(self):
        """Turn all devices off"""
        self.turn_light_off()
        self.turn_tv_off()
        self.turn_ac_off()


def main():
    home = SmartHome()
    print("Initial state:", home.status())
    
    # Test query methods
    print(f"\nTemperature: {home.get_temperature()}°C")
    print(f"Is hot? {home.is_hot()}")
    print(f"Is comfortable? {home.is_comfortable()}")
    print(f"Light on? {home.is_light_on()}")
    print(f"Any device on? {home.is_any_device_on()}")
    print(f"Devices on count: {home.count_devices_on()}")

    # Turn on devices
    print("\nTurning on light and AC...")
    home.turn_light_on()
    home.turn_ac_on()
    home.set_temperature(22)
    print("After changes:", home.status())
    
    print(f"Light on? {home.is_light_on()}")
    print(f"AC on? {home.is_ac_on()}")
    print(f"Devices on count: {home.count_devices_on()}")
    
    # Turn everything off
    print("\nTurning everything off...")
    home.turn_all_off()
    print("After turning all off:", home.status())
    print(f"All devices off? {home.are_all_devices_off()}")


if __name__ == "__main__":
    main()