import requests
import re


class SmartHome:
    COLOUR_MAP = {
        "red": "#FF0000",
        "green": "#00FF00",
        "blue": "#0000FF",
        "yellow": "#FFFF00",
        "orange": "#FFA500",
        "purple": "#800080",
        "pink": "#FFC0CB",
        "white": "#FFFFFF",
        "cyan": "#00FFFF",
        "magenta": "#FF00FF",
    }

    def __init__(self):
        """Initialize the SmartHome client."""
        # self.base_url = "https://turing.se.kmitl.ac.th/smarthome/api/api"
        self.base_url = "https://turing.se.kmitl.ac.th:5500/api"
        self.email = "p@gmail.com"
        self.password = "12345678"
        self.token = None

    def _ensure_authenticated(self):
        """Ensure the client is authenticated before making API calls."""
        if self.token is None:
            self.login()

    def _parse_colour(self, raw: str) -> str:
        """Extract a colour hex code from a raw string that may contain extra words.

        Handles inputs like 'red', 'color of red', 'lightbulb2 color red', '#FF0000'.
        """
        raw_lower = raw.strip().lower()

        # If it's already a hex code, return as-is
        if re.match(r'^#[0-9a-fA-F]{6}$', raw.strip()):
            return raw.strip()

        # Search for a known colour name anywhere in the input
        for name, hex_code in self.COLOUR_MAP.items():
            if re.search(r'\b' + name + r'\b', raw_lower):
                return hex_code

        # Fallback: return raw input (let the API handle it)
        return raw.strip()

    def login(self):
        """Login to the SmartHome API and store the authentication token.

        Phrases: login, log in, sign in, authenticate, connect account,
        access smart home, connect to smart home.
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

        Phrases: turn on lightbulb 1, turn on light 1, switch on lightbulb 1, switch on light 1,
        turn lightbulb 1 on, turn light 1 on, switch lightbulb 1 on, switch light 1 on,
        enable lightbulb 1, enable light 1, power on lightbulb 1, power on light 1,
        lightbulb 1 on, light 1 on, open lightbulb 1, open light 1.
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

        Phrases: turn off lightbulb 1, turn off light 1, switch off lightbulb 1, switch off light 1,
        turn lightbulb 1 off, turn light 1 off, switch lightbulb 1 off, switch light 1 off,
        disable lightbulb 1, disable light 1, power off lightbulb 1, power off light 1,
        lightbulb 1 off, light 1 off, close lightbulb 1, close light 1.
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

        Phrases: turn on lightbulb 2, turn on light 2, switch on lightbulb 2, switch on light 2,
        turn lightbulb 2 on, turn light 2 on, switch lightbulb 2 on, switch light 2 on,
        enable lightbulb 2, enable light 2, power on lightbulb 2, power on light 2,
        lightbulb 2 on, light 2 on, open lightbulb 2, open light 2.
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

        Phrases: turn off lightbulb 2, turn off light 2, switch off lightbulb 2, switch off light 2,
        turn lightbulb 2 off, turn light 2 off, switch lightbulb 2 off, switch light 2 off,
        disable lightbulb 2, disable light 2, power off lightbulb 2, power off light 2,
        lightbulb 2 off, light 2 off, close lightbulb 2, close light 2.
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

        Phrases: get devices, get device info, show devices, list devices,
        show all devices, list all devices, view devices, check devices,
        device status, show device status, what devices are there.
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

    def set_lightbulb_1_colour(self, colour):
        """Change lightbulb 1 colour.

        Phrases: change lightbulb 1 color, change light 1 color,
        set lightbulb 1 color, set light 1 color,
        change color lightbulb 1, change color light 1,
        change color of lightbulb 1, change color of light 1,
        set color of lightbulb 1, set color of light 1,
        change the color of lightbulb 1, change the color of light 1,
        lightbulb 1 color, light 1 color,
        make lightbulb 1, make light 1.
        """
        colour = self._parse_colour(colour)
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/f5398b01-79c5-4f88-b9ea-019b452d6de6/set_colour/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.post(url, json={"colour": colour}, headers=headers, verify=False, timeout=10)
        print(f"[SET_COLOUR_LB1] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"Lightbulb 1 colour changed to {colour}")
        else:
            print(f"Failed to change lightbulb 1 colour: {response.text}")

    def set_lightbulb_2_colour(self, colour):
        """Change lightbulb 2 colour.

        Phrases: change lightbulb 2 color, change light 2 color,
        set lightbulb 2 color, set light 2 color,
        change color lightbulb 2, change color light 2,
        change color of lightbulb 2, change color of light 2,
        set color of lightbulb 2, set color of light 2,
        change the color of lightbulb 2, change the color of light 2,
        lightbulb 2 color, light 2 color,
        make lightbulb 2, make light 2.
        """
        colour = self._parse_colour(colour)
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/badec2bd-10e0-40ff-a38d-95b8d80c4504/set_colour/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.post(url, json={"colour": colour}, headers=headers, verify=False, timeout=10)
        print(f"[SET_COLOUR_LB2] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"Lightbulb 2 colour changed to {colour}")
        else:
            print(f"Failed to change lightbulb 2 colour: {response.text}")

    def turn_on_ac(self):
        """Turn the air conditioner on.

        Phrases: turn on ac, switch on ac, turn ac on, switch ac on,
        enable ac, power on ac, start ac, ac on,
        turn on air conditioner, turn on air con.
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

        Phrases: turn off ac, switch off ac, turn ac off, switch ac off,
        disable ac, power off ac, stop ac, ac off,
        turn off air conditioner, turn off air con.
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

    def turn_on_fan(self):
        """Turn the fan on.

        Phrases: turn on fan, switch on fan, turn fan on, switch fan on,
        enable fan, power on fan, start fan, fan on.
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

        Phrases: turn off fan, switch off fan, turn fan off, switch fan off,
        disable fan, power off fan, stop fan, fan off.
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

    def turn_on_tv(self):
        """Turn the TV on.

        Phrases: turn on tv, switch on tv, turn tv on, switch tv on,
        enable tv, power on tv, start tv, tv on,
        turn on television.
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

        Phrases: turn off tv, switch off tv, turn tv off, switch tv off,
        disable tv, power off tv, stop tv, tv off,
        turn off television.
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
