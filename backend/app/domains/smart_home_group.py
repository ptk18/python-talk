import requests


class SmartHome:
    def __init__(self):
        """
        Initialize the SmartHome client.

        Phrases: initialize smart home, start smart home, create smart home,
        setup smart home, connect smart home.
        """
        # self.base_url = "https://turing.se.kmitl.ac.th/smarthome/api/api"
        self.base_url = "https://turing.se.kmitl.ac.th:5500/api"
        self.email = "p@gmail.com"
        self.password = "12345678"
        self.token = None
        self.tv_volume = 10

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
        response = requests.post(url, json={"email": self.email, "password": self.password}, verify=False, timeout=10)
        print(f"[LOGIN] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            print("Login successful")
        else:
            print(f"Login failed: {response.text}")

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
        url = f"{self.base_url}/homes/lightbulbs/badec2bd-10e0-40ff-a38d-95b8d80c4504/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": True}, headers=headers, verify=False, timeout=10)
        print(f"[TURN_ON] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("Lightbulb turned on")
        else:
            print(f"Failed to turn on lightbulb: {response.text}")

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
        url = f"{self.base_url}/homes/lightbulbs/badec2bd-10e0-40ff-a38d-95b8d80c4504/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": False}, headers=headers, verify=False, timeout=10)
        print(f"[TURN_OFF] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("Lightbulb turned off")
        else:
            print(f"Failed to turn off lightbulb: {response.text}")

    def get_devices_info(self):
        """
        Get all devices information in the room.

        Phrases: get device info, get devices info, show devices,
        show all devices, list devices, view devices,
        check devices, get room devices, device status,
        show device status, list all devices.
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
        """
        Get all homes information.

        Phrases: get all homes, show homes, list homes, what homes are there,
        homes info, show all homes, view homes, get homes.
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
        """
        Change the lightbulb colour.

        Phrases: change light colour, change light color, set light colour,
        set light color, change lightbulb colour, change lightbulb color,
        set lightbulb colour, set lightbulb color,
        make the light red, make the light green, make the light blue,
        change light to red, change light to green, change light to blue,
        change the lightbulb color, set the lightbulb color,
        change the light color, set the light color.
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
        """
        Change the lightbulb brightness.

        Phrases: change brightness, set brightness, set light brightness,
        change light brightness, dim the light, brighten the light,
        set lightbulb brightness, change lightbulb brightness,
        adjust brightness, adjust light brightness.
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
        """
        Turn the air conditioner on.

        Phrases: turn on AC, turn the AC on, switch on AC,
        switch on the AC, enable AC, power on AC,
        turn on air conditioner, turn on air con,
        switch on air conditioner, start AC.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/acs/PLACEHOLDER_AC_UUID/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": True}, headers=headers, verify=False, timeout=10)
        print(f"[AC_ON] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("AC turned on")
        else:
            print(f"Failed to turn on AC: {response.text}")

    def turn_off_ac(self):
        """
        Turn the air conditioner off.

        Phrases: turn off AC, turn the AC off, switch off AC,
        switch off the AC, disable AC, power off AC,
        turn off air conditioner, turn off air con,
        switch off air conditioner, stop AC.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/acs/PLACEHOLDER_AC_UUID/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": False}, headers=headers, verify=False, timeout=10)
        print(f"[AC_OFF] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("AC turned off")
        else:
            print(f"Failed to turn off AC: {response.text}")

    def set_ac_temperature(self, temp):
        """
        Set the air conditioner temperature.

        Phrases: set AC temperature, change AC temperature, set AC temp,
        change AC temp, adjust AC temperature, set air conditioner temperature,
        change air conditioner temperature, set temperature to,
        AC temperature to, adjust temperature.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/acs/PLACEHOLDER_AC_UUID/set_temperature/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"temp": temp}, headers=headers, verify=False, timeout=10)
        print(f"[SET_TEMP] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"AC temperature set to {temp}")
        else:
            print(f"Failed to set AC temperature: {response.text}")

    def turn_on_fan(self):
        """
        Turn the fan on.

        Phrases: turn on fan, turn the fan on, switch on fan,
        switch on the fan, enable fan, power on fan,
        start fan, start the fan.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/fans/PLACEHOLDER_FAN_UUID/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": True}, headers=headers, verify=False, timeout=10)
        print(f"[FAN_ON] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("Fan turned on")
        else:
            print(f"Failed to turn on fan: {response.text}")

    def turn_off_fan(self):
        """
        Turn the fan off.

        Phrases: turn off fan, turn the fan off, switch off fan,
        switch off the fan, disable fan, power off fan,
        stop fan, stop the fan.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/fans/PLACEHOLDER_FAN_UUID/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": False}, headers=headers, verify=False, timeout=10)
        print(f"[FAN_OFF] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("Fan turned off")
        else:
            print(f"Failed to turn off fan: {response.text}")

    def set_fan_speed(self, speed):
        """
        Set the fan speed.

        Phrases: set fan speed, change fan speed, adjust fan speed,
        fan speed to, set the fan speed, change the fan speed,
        make fan faster, make fan slower.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/fans/PLACEHOLDER_FAN_UUID/set_speed/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"speed": speed}, headers=headers, verify=False, timeout=10)
        print(f"[SET_SPEED] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"Fan speed set to {speed}")
        else:
            print(f"Failed to set fan speed: {response.text}")

    def set_fan_swing(self, swing):
        """
        Set the fan swing on or off.

        Phrases: turn on fan swing, turn off fan swing, enable swing,
        disable swing, fan swing on, fan swing off,
        enable fan swing, disable fan swing,
        start fan swing, stop fan swing.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/fans/PLACEHOLDER_FAN_UUID/set_swing/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"swing": swing}, headers=headers, verify=False, timeout=10)
        print(f"[SET_SWING] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"Fan swing set to {swing}")
        else:
            print(f"Failed to set fan swing: {response.text}")

    def turn_on_tv(self):
        """
        Turn the TV on.

        Phrases: turn on TV, turn the TV on, switch on TV,
        switch on the TV, enable TV, power on TV,
        turn on television, turn the television on,
        switch on television, start TV.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/tvs/PLACEHOLDER_TV_UUID/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": True}, headers=headers, verify=False, timeout=10)
        print(f"[TV_ON] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("TV turned on")
        else:
            print(f"Failed to turn on TV: {response.text}")

    def turn_off_tv(self):
        """
        Turn the TV off.

        Phrases: turn off TV, turn the TV off, switch off TV,
        switch off the TV, disable TV, power off TV,
        turn off television, turn the television off,
        switch off television, stop TV.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/tvs/PLACEHOLDER_TV_UUID/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"is_on": False}, headers=headers, verify=False, timeout=10)
        print(f"[TV_OFF] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print("TV turned off")
        else:
            print(f"Failed to turn off TV: {response.text}")

    def increase_tv_volume(self):
        """
        Increase the TV volume by 1.

        Phrases: increase volume, volume up, turn up TV, louder,
        raise volume, increase TV volume, turn up the volume,
        make it louder, raise the volume, turn the volume up.
        """
        self._ensure_authenticated()
        self.tv_volume = min(self.tv_volume + 1, 100)
        url = f"{self.base_url}/homes/tvs/PLACEHOLDER_TV_UUID/set_volume/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"volume": self.tv_volume}, headers=headers, verify=False, timeout=10)
        print(f"[VOLUME_UP] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"TV volume increased to {self.tv_volume}")
        else:
            print(f"Failed to increase TV volume: {response.text}")

    def decrease_tv_volume(self):
        """
        Decrease the TV volume by 1.

        Phrases: decrease volume, volume down, turn down TV, quieter,
        lower volume, decrease TV volume, turn down the volume,
        make it quieter, lower the volume, turn the volume down.
        """
        self._ensure_authenticated()
        self.tv_volume = max(self.tv_volume - 1, 0)
        url = f"{self.base_url}/homes/tvs/PLACEHOLDER_TV_UUID/set_volume/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"volume": self.tv_volume}, headers=headers, verify=False, timeout=10)
        print(f"[VOLUME_DOWN] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"TV volume decreased to {self.tv_volume}")
        else:
            print(f"Failed to decrease TV volume: {response.text}")

    def set_tv_channel(self, channel):
        """
        Change the TV channel.

        Phrases: change channel, set TV channel, switch channel,
        change TV channel, set channel, go to channel,
        switch TV channel, change the channel, set the channel,
        switch to channel.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/tvs/PLACEHOLDER_TV_UUID/set_channel/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"channel": channel}, headers=headers, verify=False, timeout=10)
        print(f"[SET_CHANNEL] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"TV channel set to {channel}")
        else:
            print(f"Failed to set TV channel: {response.text}")
