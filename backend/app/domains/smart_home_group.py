import requests


class SmartHome:
    def __init__(self):
        """
        Initialize the SmartHome client.

        Phrases: initialize smart home, start smart home, create smart home,
        setup smart home, connect smart home.
        """
        # self.base_url = "https://turing.se.kmitl.ac.th:5500/api"
        self.base_url = "https://turing.se.kmitl.ac.th/smarthome/api/api"
        self.email = "user@example.com"
        self.password = "password123"
        self.token = None

    def _ensure_authenticated(self):
        """
        Ensure the client is authenticated before making API calls.

        Phrases: authenticate, login first, make sure logged in,
        ensure authenticated, check authentication.
        """
        if self.token is None:
            self.login()

    def login(self):
        """
        Login to the SmartHome API and store the authentication token.

        Phrases: login, log in, sign in, authenticate,
        connect account, access smart home.
        """
        url = f"{self.base_url}/auth/login/"
        response = requests.post(url, json={"email": self.email, "password": self.password})
        print(f"[LOGIN] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access")
            return "Login successful"
        return f"Login failed: {response.text}"

    def turn_on_lightbulb(self):
        """
        Turn the lightbulb on.

        Phrases: turn on lightbulb, turn the lightbulb on, switch on lightbulb,
        switch on the lightbulb, enable lightbulb, power on lightbulb,
        turn on light, turn the light on, switch on light,
        switch on the light, enable light, power on light,
        open light, open the light.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/9ef31b3c-3abf-49e8-9d82-3512077ebdad/"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.patch(url, json={"is_on": True}, headers=headers)
        print(f"[TURN_ON] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            return "Lightbulb turned on"
        return f"Failed to turn on lightbulb: {response.text}"

    def turn_off_lightbulb(self):
        """
        Turn the lightbulb off.

        Phrases: turn off lightbulb, turn the lightbulb off, switch off lightbulb,
        switch off the lightbulb, disable lightbulb, power off lightbulb,
        turn off light, turn the light off, switch off light,
        switch off the light, disable light, power off light,
        close light, close the light.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/9ef31b3c-3abf-49e8-9d82-3512077ebdad/"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.patch(url, json={"is_on": False}, headers=headers)
        if response.status_code == 200:
            return "Lightbulb turned off"
        return f"Failed to turn off lightbulb: {response.text}"

    def get_devices_info(self):
        """
        Get all devices information in the room.

        Phrases: get device info, get devices info, show devices,
        show all devices, list devices, view devices,
        check devices, get room devices, device status,
        show device status, list all devices.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/rooms/f414da7e-3d01-48e2-abe6-eb8a607a1ca6/get_devices/"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return f"Failed to get devices information: {response.text}"
