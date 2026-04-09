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

    def turn_on_lightbulb_1(self):
        """
        Turn lightbulb 1 on.

        Phrases: turn on lightbulb 1, turn lightbulb 1 on, switch on lightbulb 1,
        switch on light 1, turn on light 1, turn light 1 on,
        enable lightbulb 1, enable light 1, lightbulb 1 on, light 1 on,
        power on lightbulb 1, power on light 1, open light 1.
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
        """
        Turn lightbulb 1 off.

        Phrases: turn off lightbulb 1, turn lightbulb 1 off, switch off lightbulb 1,
        switch off light 1, turn off light 1, turn light 1 off,
        disable lightbulb 1, disable light 1, lightbulb 1 off, light 1 off,
        power off lightbulb 1, power off light 1, close light 1.
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
        """
        Turn lightbulb 2 on.

        Phrases: turn on lightbulb 2, turn lightbulb 2 on, switch on lightbulb 2,
        switch on light 2, turn on light 2, turn light 2 on,
        enable lightbulb 2, enable light 2, lightbulb 2 on, light 2 on,
        power on lightbulb 2, power on light 2, open light 2.
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
        """
        Turn lightbulb 2 off.

        Phrases: turn off lightbulb 2, turn lightbulb 2 off, switch off lightbulb 2,
        switch off light 2, turn off light 2, turn light 2 off,
        disable lightbulb 2, disable light 2, lightbulb 2 off, light 2 off,
        power off lightbulb 2, power off light 2, close light 2.
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

    def set_lightbulb_1_colour(self, colour):
        """
        Change lightbulb 1 colour.

        Phrases: change light 1 colour, change light 1 color, set light 1 colour,
        set light 1 color, change lightbulb 1 colour, change lightbulb 1 color,
        set lightbulb 1 colour, set lightbulb 1 color,
        change the lightbulb 1 color, set the lightbulb 1 color,
        change the light 1 color, set the light 1 color,
        make light 1 red, make light 1 green, make light 1 blue.
        """
        colour_map = {
            "red": "#FF0000",
            "green": "#00FF00",
            "blue": "#0000FF",
        }
        colour = colour_map.get(colour.lower(), colour)
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
        """
        Change lightbulb 2 colour.

        Phrases: change light 2 colour, change light 2 color, set light 2 colour,
        set light 2 color, change lightbulb 2 colour, change lightbulb 2 color,
        set lightbulb 2 colour, set lightbulb 2 color,
        change the lightbulb 2 color, set the lightbulb 2 color,
        change the light 2 color, set the light 2 color,
        make light 2 red, make light 2 green, make light 2 blue.
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
        print(f"[SET_COLOUR_LB2] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"Lightbulb 2 colour changed to {colour}")
        else:
            print(f"Failed to change lightbulb 2 colour: {response.text}")

    def set_lightbulb_1_brightness(self, brightness):
        """
        Change lightbulb 1 brightness.

        Phrases: change brightness light 1, set light 1 brightness,
        change light 1 brightness, set lightbulb 1 brightness,
        change lightbulb 1 brightness, adjust light 1 brightness,
        dim light 1, brighten light 1.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/f5398b01-79c5-4f88-b9ea-019b452d6de6/set_brightness/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"brightness": brightness}, headers=headers, verify=False, timeout=10)
        print(f"[SET_BRIGHTNESS_LB1] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"Lightbulb 1 brightness set to {brightness}")
        else:
            print(f"Failed to change lightbulb 1 brightness: {response.text}")

    def set_lightbulb_2_brightness(self, brightness):
        """
        Change lightbulb 2 brightness.

        Phrases: change brightness light 2, set light 2 brightness,
        change light 2 brightness, set lightbulb 2 brightness,
        change lightbulb 2 brightness, adjust light 2 brightness,
        dim light 2, brighten light 2.
        """
        self._ensure_authenticated()
        url = f"{self.base_url}/homes/lightbulbs/badec2bd-10e0-40ff-a38d-95b8d80c4504/set_brightness/"
        headers = {"Authorization": f"Token {self.token}"}
        response = requests.patch(url, json={"brightness": brightness}, headers=headers, verify=False, timeout=10)
        print(f"[SET_BRIGHTNESS_LB2] Status: {response.status_code}, Response: {response.text}")
        if response.status_code == 200:
            print(f"Lightbulb 2 brightness set to {brightness}")
        else:
            print(f"Failed to change lightbulb 2 brightness: {response.text}")

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

    def turn_on_ac(self):
        """
        Turn the air conditioner on.

        Phrases: turn on AC, turn the AC on, switch on AC,
        switch on the AC, enable AC, power on AC,
        turn on air conditioner, turn on air con,
        switch on air conditioner, start AC.
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
        """
        Turn the air conditioner off.

        Phrases: turn off AC, turn the AC off, switch off AC,
        switch off the AC, disable AC, power off AC,
        turn off air conditioner, turn off air con,
        switch off air conditioner, stop AC.
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
        """
        Set the air conditioner temperature.

        Phrases: set AC temperature, change AC temperature, set AC temp,
        change AC temp, adjust AC temperature, set air conditioner temperature,
        change air conditioner temperature, set temperature to,
        AC temperature to, adjust temperature.
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
        """
        Turn the fan on.

        Phrases: turn on fan, turn the fan on, switch on fan,
        switch on the fan, enable fan, power on fan,
        start fan, start the fan.
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
        """
        Turn the fan off.

        Phrases: turn off fan, turn the fan off, switch off fan,
        switch off the fan, disable fan, power off fan,
        stop fan, stop the fan.
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
        """
        Set the fan speed.

        Phrases: set fan speed, change fan speed, adjust fan speed,
        fan speed to, set the fan speed, change the fan speed,
        make fan faster, make fan slower.
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
        """
        Set the fan swing on or off.

        Phrases: turn on fan swing, turn off fan swing, enable swing,
        disable swing, fan swing on, fan swing off,
        enable fan swing, disable fan swing,
        start fan swing, stop fan swing.
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
        """
        Turn the TV on.

        Phrases: turn on TV, turn the TV on, switch on TV,
        switch on the TV, enable TV, power on TV,
        turn on television, turn the television on,
        switch on television, start TV.
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
        """
        Turn the TV off.

        Phrases: turn off TV, turn the TV off, switch off TV,
        switch off the TV, disable TV, power off TV,
        turn off television, turn the television off,
        switch off television, stop TV.
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
        """
        Increase the TV volume by 1.

        Phrases: increase volume, volume up, turn up TV, louder,
        raise volume, increase TV volume, turn up the volume,
        make it louder, raise the volume, turn the volume up.
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
        """
        Decrease the TV volume by 1.

        Phrases: decrease volume, volume down, turn down TV, quieter,
        lower volume, decrease TV volume, turn down the volume,
        make it quieter, lower the volume, turn the volume down.
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
        """
        Change the TV channel.

        Phrases: change channel, set TV channel, switch channel,
        change TV channel, set channel, go to channel,
        switch TV channel, change the channel, set the channel,
        switch to channel.
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
