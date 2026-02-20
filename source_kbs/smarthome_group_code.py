import requests


class SmartHome:
    def __init__(self):
        """Initialize the SmartHome client."""
        self.base_url = "https://turing.se.kmitl.ac.th/smarthome/api/api"
        self.email = "user@example.com"
        self.password = "password123"
        self.token = None

    def _ensure_authenticated(self):
        """Ensure the client is authenticated before making API calls."""
        if self.token is None:
            self.login()

    def login(self):
        """Login to the SmartHome API and store the authentication token."""
        url = f"{self.base_url}/auth/login/"
        response = requests.post(url, json={"email": self.email, "password": self.password})
        print(f"[LOGIN] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            return "Login successful"
        return f"Login failed: {response.text}"

    def turn_on_lightbulb(self):
        """Turn the lightbulb on."""
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/9ef31b3c-3abf-49e8-9d82-3512077ebdad/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": True}, headers=headers)
        print(f"[TURN_ON] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            return "Lightbulb turned on"
        return f"Failed to turn on lightbulb: {response.text}"

    def turn_off_lightbulb(self):
        """Turn the lightbulb off."""
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/9ef31b3c-3abf-49e8-9d82-3512077ebdad/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": False}, headers=headers)
        print(f"[TURN_OFF] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            return "Lightbulb turned off"
        return f"Failed to turn off lightbulb: {response.text}"

    def get_devices_info(self):
        """Get all devices information in the room."""
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/rooms/f414da7e-3d01-48e2-abe6-eb8a607a1ca6/get_devices/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.get(url, headers=headers)
        print(f"[GET_DEVICES] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            return response.json()
        return f"Failed to get devices information: {response.text}"
