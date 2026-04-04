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
        response = requests.post(url, json={"email": self.email, "password": self.password}, verify=False)
        print(f"[LOGIN] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            return "Login successful"
        return f"Login failed: {response.text}"

    def turn_on_lightbulb(self):
        """Turn the lightbulb on.

        Phrases: turn on the light, switch on light, lightbulb on, turn on lightbulb, enable light.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/450bc6dc-14dd-483b-a5ee-d944e3ba0357/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": True}, headers=headers, verify=False)
        print(f"[TURN_ON] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            return "Lightbulb turned on"
        return f"Failed to turn on lightbulb: {response.text}"

    def turn_off_lightbulb(self):
        """Turn the lightbulb off.

        Phrases: turn off the light, switch off light, lightbulb off, turn off lightbulb, disable light.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/450bc6dc-14dd-483b-a5ee-d944e3ba0357/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": False}, headers=headers, verify=False)
        print(f"[TURN_OFF] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            return "Lightbulb turned off"
        return f"Failed to turn off lightbulb: {response.text}"

    def get_devices_info(self):
        """Get all devices information in the room.

        Phrases: get devices, show devices, list devices, device info, what devices are there.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/homes/521b6189-28b2-4395-a099-4423cf166dc8/get_devices/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.get(url, headers=headers, verify=False)
        print(f"[GET_DEVICES] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            return response.json()
        return f"Failed to get devices information: {response.text}"
