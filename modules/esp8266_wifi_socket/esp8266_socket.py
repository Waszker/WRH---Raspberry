import re
import signal
import socket
import sys
import urllib2

import requests

from utils.io import non_empty_input, non_empty_positive_numeric_input, log
from wrh_engine import module_base as base_module

ninput = non_empty_input
npinput = non_empty_positive_numeric_input


class ESP8266SocketModule(base_module.Module):
    """
    This class works with ESP8266 WiFi socket.
    """
    TYPE_NAME = "ESP8266 WIFI SOCKET"
    CONFIGURATION_LINE_PATTERN = "([0-9]{1,9});(.+?);(.+?);(.+)$"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.html_repr = None

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed
        :param configuration_line:
        :return:
        """
        checker = re.compile(ESP8266SocketModule.CONFIGURATION_LINE_PATTERN)
        return checker.match(configuration_line) is not None

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        return ["/usr/bin/python2.7", "-m", "modules.esp8266_wifi_socket.esp8266_socket"]

    def get_configuration_line(self):
        """
        Creates module configuration line
        :return: Properly formatted configuration file line
        """
        return ('{};' * 4)[:-1].format(self.id, self.name, self.gpio, self.port)

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(ESP8266SocketModule.CONFIGURATION_LINE_PATTERN, configuration_file_line)
        self.id = matches.group(1)
        self.name = matches.group(2)
        self.gpio = matches.group(3)
        self.port = matches.group(4)

    def get_measurement(self):
        """
        Returns information about socket state.
        """
        value_finding_pattern = ".+?value=\"(.+?)\".*$"
        checker = re.compile(value_finding_pattern)
        try:
            response = requests.get("http://" + str(self.gpio) + "/socket.lua", timeout=5)
            # Remove all characters other than letters, numbers or = and " if connection was successful
            response_content = ''.join(e for e in response.content if e.isalnum() or e == '=' or e == '"')
        except requests.ConnectionError:
            response_content = ''
        if not checker.match(str(response_content)):
            state = "UNKNOWN"
        else:
            # Socket returns opposite state - we need to change its response
            true_state = {"ON": "OFF", "OFF": "ON"}
            state = true_state[re.search(value_finding_pattern, str(response_content)).group(1)]
        return state

    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """
        return "ESP8266 WiFi socket - electrical socket with WiFi connection capabilities and built-in timer"

    def run_registration_procedure(self, new_id):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, new_id)
        self.gpio = ninput("Please input ESP8266 WiFi socket IP address: ")
        self.port = npinput("Please input port on which module will be listening for commands: ")

    def edit(self):
        """
        Runs interactive procedure to edit module.
        Returns connection status and response.
        """
        log('Provide new module information (leave fields blank if you don\'t want to change)')
        log('Please note that changes other than name will always succeed')
        log('Name changing requires active Internet connection')
        new_name = raw_input('New module\'s name: ')
        new_gpio = raw_input("Please input new IP address of ESP8266 device: ")
        new_port = raw_input("Please input new port on which module will be listening for commands: ")

        if new_gpio: self.gpio = new_gpio
        if new_port: self.port = new_port
        if new_name: self.name = new_name

    def start_work(self):
        """
        Starts working procedure. Module listens on specific port for commands. Client after connection should
        send "ON" or "OFF" message followed by ; and time for which socket should be in mentioned state.
        Optionally "STATE" message can be sent which results in state of the socket being returned.
        """
        base_module.Module.start_work(self)
        while self._should_end is False:
            signal.pause()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        :param website_host_address: ip address of server
        :return:
        """
        if not self.html_repr:
            with open('modules/esp8266_wifi_socket/html/repr.html', 'r') as f:
                text_input_name = "esp_timeout_" + self.id
                html = f.read()
                self.html_repr = html.format(id=self.id, name=self.name, port=self.port, input_text=text_input_name)
        return self.html_repr

    def _set_socket_state(self, should_turn_on, time_wait):
        state = "ON" if should_turn_on else "OFF"
        url = "http://" + self.gpio + "/socket.lua?wait=" + time_wait + "&state=" + state
        try:
            request = urllib2.Request(url)
            urllib2.urlopen(request, timeout=5).read()
        except urllib2.URLError, socket.timeout:
            pass

    def _react_to_connection(self, connection, _):
        data = str(connection.recv(1024) + ",").split(',')
        state, time_wait = data[0], data[1]
        if str(state) == "ON" or str(state) == "on":
            self._set_socket_state(True, time_wait)
        elif str(state) == "OFF" or str(state) == "off":
            self._set_socket_state(False, time_wait)
        elif str(state) == "STATE" or str(state) == "state":
            connection.send(self.get_measurement())


if __name__ == "__main__":
    log('ESP8266 WiFi socket: started.')
    conf_line = sys.argv[1]
    esp8266 = ESP8266SocketModule(conf_line)
    esp8266.start_work()
