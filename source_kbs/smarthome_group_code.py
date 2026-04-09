import requests


class SmartHome:
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

    def turn_on_lightbulb(self):
        """Turn the lightbulb on.

        Phrases: turn on the light, switch on light, lightbulb on, turn on lightbulb, enable light.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/badec2bd-10e0-40ff-a38d-95b8d80c4504/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": True}, headers=headers, verify=False, timeout=10)
        print(f"[TURN_ON] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("Lightbulb turned on")
        else:
            print(f"Failed to turn on lightbulb: {response.text}")

    def turn_off_lightbulb(self):
        """Turn the lightbulb off.

        Phrases: turn off the light, switch off light, lightbulb off, turn off lightbulb, disable light.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/badec2bd-10e0-40ff-a38d-95b8d80c4504/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": False}, headers=headers, verify=False, timeout=10)
        print(f"[TURN_OFF] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("Lightbulb turned off")
        else:
            print(f"Failed to turn off lightbulb: {response.text}")

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
