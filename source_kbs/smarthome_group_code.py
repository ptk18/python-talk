import requests


class SmartHome:
    def __init__(self):
        """Initialize the SmartHome client."""
        # self.base_url = "https://turing.se.kmitl.ac.th/smarthome/api/api"
        self.base_url = "https://turing.se.kmitl.ac.th:5500/api"
        self.email = "p@gmail.com"
        self.password = "12345678"
        self.token = None
        self.tv_volume = 10

    def _ensure_authenticated(self):
        """Ensure the client is authenticated before making API calls."""
        if self.token is None:
            self.login()

    def login(self):
        """Login to the SmartHome API and store the authentication token.

        Phrases: login, sign in, authenticate, connect to smart home.
        """
        url = f"{self.base_url}/auth/login/"
        response = requests.post(url, json={"email": self.email, "password": self.password}, verify=False, timeout=10)
        print(f"[LOGIN] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            print("Login successful")
        else:
            print(f"Login failed: {response.text}")

    def turn_on_lightbulb_1(self):
        """Turn lightbulb 1 on.

        Phrases: turn on lightbulb 1, switch on light 1, lightbulb 1 on, turn on light 1, enable light 1.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/f5398b01-79c5-4f88-b9ea-019b452d6de6/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": True}, headers=headers, verify=False, timeout=10)
        print(f"[TURN_ON_LB1] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("Lightbulb 1 turned on")
        else:
            print(f"Failed to turn on lightbulb 1: {response.text}")

    def turn_off_lightbulb_1(self):
        """Turn lightbulb 1 off.

        Phrases: turn off lightbulb 1, switch off light 1, lightbulb 1 off, turn off light 1, disable light 1.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/f5398b01-79c5-4f88-b9ea-019b452d6de6/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": False}, headers=headers, verify=False, timeout=10)
        print(f"[TURN_OFF_LB1] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("Lightbulb 1 turned off")
        else:
            print(f"Failed to turn off lightbulb 1: {response.text}")

    def turn_on_lightbulb_2(self):
        """Turn lightbulb 2 on.

        Phrases: turn on lightbulb 2, switch on light 2, lightbulb 2 on, turn on light 2, enable light 2.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/badec2bd-10e0-40ff-a38d-95b8d80c4504/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": True}, headers=headers, verify=False, timeout=10)
        print(f"[TURN_ON_LB2] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("Lightbulb 2 turned on")
        else:
            print(f"Failed to turn on lightbulb 2: {response.text}")

    def turn_off_lightbulb_2(self):
        """Turn lightbulb 2 off.

        Phrases: turn off lightbulb 2, switch off light 2, lightbulb 2 off, turn off light 2, disable light 2.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/badec2bd-10e0-40ff-a38d-95b8d80c4504/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": False}, headers=headers, verify=False, timeout=10)
        print(f"[TURN_OFF_LB2] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("Lightbulb 2 turned off")
        else:
            print(f"Failed to turn off lightbulb 2: {response.text}")

    def get_devices_info(self):
        """Get all devices information in the room.

        Phrases: get devices, show devices, list devices, device info, what devices are there.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/homes/d0cef9a6-1050-4830-908d-b85e994de47d/get_devices/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"[GET_DEVICES] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(response.json())
        else:
            print(f"Failed to get devices information: {response.text}")

    def get_all_homes_info(self):
        """Get all homes information.

        Phrases: get all homes, show homes, list homes, what homes are there, homes info.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/homes/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"[GET_HOMES] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(response.json())
        else:
            print(f"Failed to get homes: {response.text}")

    def set_lightbulb_colour(self, colour):
        """Change the lightbulb colour.

        Phrases: change light colour, set light color, change lightbulb colour, make the light red, change light to blue.
        """
        colour_map = {
            "red": "#FF0000",
            "green": "#00FF00",
            "blue": "#0000FF",
        }
        colour = colour_map.get(colour.lower(), colour)
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/badec2bd-10e0-40ff-a38d-95b8d80c4504/set_colour/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.post(url, json={"colour": colour}, headers=headers, verify=False, timeout=10)
        print(f"[SET_COLOUR] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"Lightbulb colour changed to {colour}")
        else:
            print(f"Failed to change lightbulb colour: {response.text}")

    def set_lightbulb_brightness(self, brightness):
        """Change the lightbulb brightness.

        Phrases: change brightness, set light brightness, dim the light, brighten the light, set lightbulb brightness.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/badec2bd-10e0-40ff-a38d-95b8d80c4504/set_brightness/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"brightness": brightness}, headers=headers, verify=False, timeout=10)
        print(f"[SET_BRIGHTNESS] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"Lightbulb brightness set to {brightness}")
        else:
            print(f"Failed to change lightbulb brightness: {response.text}")

    def turn_on_ac(self):
        """Turn the air conditioner on.

        Phrases: turn on AC, switch on air conditioner, AC on, enable AC, turn on air con.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/acs/35da478b-b03b-4509-9f66-979c76bfa3d9/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": True}, headers=headers, verify=False, timeout=10)
        print(f"[AC_ON] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("AC turned on")
        else:
            print(f"Failed to turn on AC: {response.text}")

    def turn_off_ac(self):
        """Turn the air conditioner off.

        Phrases: turn off AC, switch off air conditioner, AC off, disable AC, turn off air con.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/acs/35da478b-b03b-4509-9f66-979c76bfa3d9/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": False}, headers=headers, verify=False, timeout=10)
        print(f"[AC_OFF] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("AC turned off")
        else:
            print(f"Failed to turn off AC: {response.text}")

    def set_ac_temperature(self, temp):
        """Set the air conditioner temperature.

        Phrases: set AC temperature, change AC temp, set air conditioner to 25 degrees, adjust AC temperature.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/acs/35da478b-b03b-4509-9f66-979c76bfa3d9/set_temperature/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"temp": temp}, headers=headers, verify=False, timeout=10)
        print(f"[SET_TEMP] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"AC temperature set to {temp}")
        else:
            print(f"Failed to set AC temperature: {response.text}")

    def turn_on_fan(self):
        """Turn the fan on.

        Phrases: turn on fan, switch on fan, fan on, enable fan, start the fan.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/fans/eadcc85f-71c5-4452-b3ac-f2276a5cfa7a/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": True}, headers=headers, verify=False, timeout=10)
        print(f"[FAN_ON] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("Fan turned on")
        else:
            print(f"Failed to turn on fan: {response.text}")

    def turn_off_fan(self):
        """Turn the fan off.

        Phrases: turn off fan, switch off fan, fan off, disable fan, stop the fan.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/fans/eadcc85f-71c5-4452-b3ac-f2276a5cfa7a/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": False}, headers=headers, verify=False, timeout=10)
        print(f"[FAN_OFF] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("Fan turned off")
        else:
            print(f"Failed to turn off fan: {response.text}")

    def set_fan_speed(self, speed):
        """Set the fan speed.

        Phrases: set fan speed, change fan speed, fan speed to 1, adjust fan speed, make fan faster, make fan slower.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/fans/eadcc85f-71c5-4452-b3ac-f2276a5cfa7a/set_speed/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"speed": speed}, headers=headers, verify=False, timeout=10)
        print(f"[SET_SPEED] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"Fan speed set to {speed}")
        else:
            print(f"Failed to set fan speed: {response.text}")

    def set_fan_swing(self, swing):
        """Set the fan swing on or off.

        Phrases: turn on fan swing, enable swing, fan swing on, turn off fan swing, disable swing, fan swing off.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/fans/eadcc85f-71c5-4452-b3ac-f2276a5cfa7a/set_swing/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"swing": swing}, headers=headers, verify=False, timeout=10)
        print(f"[SET_SWING] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"Fan swing set to {swing}")
        else:
            print(f"Failed to set fan swing: {response.text}")

    def turn_on_tv(self):
        """Turn the TV on.

        Phrases: turn on TV, switch on TV, TV on, enable TV, turn on television.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/tvs/f914aefe-76d2-44fd-bc0a-bf536f0bd227/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": True}, headers=headers, verify=False, timeout=10)
        print(f"[TV_ON] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("TV turned on")
        else:
            print(f"Failed to turn on TV: {response.text}")

    def turn_off_tv(self):
        """Turn the TV off.

        Phrases: turn off TV, switch off TV, TV off, disable TV, turn off television.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/tvs/f914aefe-76d2-44fd-bc0a-bf536f0bd227/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": False}, headers=headers, verify=False, timeout=10)
        print(f"[TV_OFF] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("TV turned off")
        else:
            print(f"Failed to turn off TV: {response.text}")

    def increase_tv_volume(self):
        """Increase the TV volume by 1.

        Phrases: increase volume, volume up, turn up TV, louder, raise volume.
        """
        self._ensure_authenticated()
        self.tv_volume = min(self.tv_volume + 1, 100)
        url = f"{self.base_url}/homes/tvs/f914aefe-76d2-44fd-bc0a-bf536f0bd227/set_volume/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"volume": self.tv_volume}, headers=headers, verify=False, timeout=10)
        print(f"[VOLUME_UP] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"TV volume increased to {self.tv_volume}")
        else:
            print(f"Failed to increase TV volume: {response.text}")

    def decrease_tv_volume(self):
        """Decrease the TV volume by 1.

        Phrases: decrease volume, volume down, turn down TV, quieter, lower volume.
        """
        self._ensure_authenticated()
        self.tv_volume = max(self.tv_volume - 1, 0)
        url = f"{self.base_url}/homes/tvs/f914aefe-76d2-44fd-bc0a-bf536f0bd227/set_volume/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"volume": self.tv_volume}, headers=headers, verify=False, timeout=10)
        print(f"[VOLUME_DOWN] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"TV volume decreased to {self.tv_volume}")
        else:
            print(f"Failed to decrease TV volume: {response.text}")

    def set_tv_channel(self, channel):
        """Change the TV channel.

        Phrases: change channel, set TV channel, switch channel, go to channel 2, change TV to channel 5.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/tvs/f914aefe-76d2-44fd-bc0a-bf536f0bd227/set_channel/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"channel": channel}, headers=headers, verify=False, timeout=10)
        print(f"[SET_CHANNEL] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"TV channel set to {channel}")
        else:
            print(f"Failed to set TV channel: {response.text}")
