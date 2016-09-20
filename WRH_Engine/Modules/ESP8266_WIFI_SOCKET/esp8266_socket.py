####################################################
# Set of functions to work with ESP8266 WRH WiFi socket
# connected to network with Raspberry Pi device.
####################################################

from WRH_Engine.Module import module_base as base_module
from WRH_Engine.Configuration import configuration as c
from WRH_Engine.Utils import utils as u
from WRH_Engine.WebApiLibrary import WebApiClient as w
import sys
import re
import requests
import socket
import time
import urllib2
import signal


class ESP8266SocketModule(base_module.Module):
    """
    This class works with ESP8266 WiFi socket.
    """
    type_number = 5
    type_name = "ESP8266 WIFI SOCKET"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.type_number = ESP8266SocketModule.type_number
        self.type_name = ESP8266SocketModule.type_name

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed
        :param self:
        :param configuration_line:
        :return:
        """
        # Configuration line for camera should look like this:
        # TYPE_NUM=5 ; ID=INT ; NAME=STRING ; GPIO=STRING ; ADDRESS=STRING
        configuration_line_pattern = str(ESP8266SocketModule.type_number) + \
                                     ";([1-9][0-9]{0,9});(.+?);(.+?);(.+)$"
        checker = re.compile(configuration_line_pattern)
        if not checker.match(configuration_line):
            raise base_module.BadConfigurationException
        return configuration_line_pattern

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        return ["/usr/bin/python2.7", "-m", "WRH_Engine.Modules.ESP8266_WIFI_SOCKET.esp8266_socket"]

    def get_configuration_line(self):
        """
        Creates module configuration line
        :return: Properly formatted configuration file line
        """
        return str(self.type_number) + ";" + str(self.id) + ";" + self.name + ";" + self.gpio + ";" + self.address

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        configuration_line_pattern = self.is_configuration_line_sane(configuration_file_line)
        matches = re.search(configuration_line_pattern, configuration_file_line)
        self.id = matches.group(1)
        self.name = matches.group(2)
        self.gpio = matches.group(3)
        self.address = matches.group(4)

    def get_measurement(self):
        """
        Returns information about socket state.
        """
        value_finding_pattern = ".+?value=\"(.+?)\".*$"
        checker = re.compile(value_finding_pattern)
        try:
            response = requests.get("http://" + str(self.gpio) + "/socket.lua")
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

    def get_type_number_and_name(self):
        """
        Returns module type number and short name (as two separate variables)
        """
        return self.type_number, self.type_name

    def run_registration_procedure(self, device_id, device_token):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, device_id, device_token)
        self.gpio = u.get_non_empty_input("Please input ESP8266 WiFi socket IP address: ")
        self.address = u.get_non_empty_input("Please input port on which module will be listening for commands: ")
        return base_module.Module.register_in_wrh(self, device_id, device_token)

    def edit(self, device_id, device_token):
        """
        Runs interactive procedure to edit module.
        Returns connection status and response.
        """
        print 'Provide new module information (leave fields blank if you don\'t want to change)'
        print 'Please note that changes other than name will always succeed'
        print 'Name changing requires active Internet connection'
        new_name = raw_input('New module\'s name: ')
        new_gpio = raw_input("Please input new IP address of ESP8266 device: ")
        new_address = raw_input("Please input new port on which module will be listening for commands: ")

        if new_gpio: self.gpio = new_gpio
        if new_address: self.address = new_address
        if new_name:
            return base_module.Module.update_module_information_in_wrh(self, device_id, device_token, new_name)
        return (w.Response.STATUS_OK, '')

    def start_work(self, device_id, device_token):
        """
        Starts working procedure. Module listens on specific port for commands. Client after connection should
        send "ON" or "OFF" message followed by ; and time for which socket should be in mentioned state.
        Optionally "STATE" message can be sent which results in state of the socket being returned.
        """
        host = ''
        port = self.address
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                s.bind((host, int(port)))
                break
            except socket.error as msg:
                print 'ESP8266 Wifi socket' + self.gpio + ' port bind failed. Error Code : ' + str(
                    msg[0]) + ' Message ' + msg[1]
                time.sleep(10)  # Sleep 10 seconds before retrying
        print "ESP8266 WiFi socket: " + self.gpio + " started listening"
        while True:
            s.listen(10)
            connection, address = s.accept()
            data = str(connection.recv(1024) + ",").split(',')
            state, time_wait = data[0], data[1]
            if str(state) == "ON" or str(state) == "on":
                self._set_socket_state(True, time_wait)
            elif str(state) == "OFF" or str(state) == "off":
                self._set_socket_state(False, time_wait)
            elif str(state) == "STATE" or str(state) == "state":
                connection.send(self.get_measurement())
            connection.close()
        s.close()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        :param website_host_address: ip address of server
        :return:
        """
        text_input_name = "esp_timeout_" + self.id
        return '<div class="card-panel"> \
                <h5>' + self.name + '</h5>\
                <div id="esp8266SocketDiv' + self.id + '" class="socketDiv" style="width: 50px; height: 50px; margin: auto"> \
                <img src="static/images/loading_spinner.gif" style="width: 50px;" /> \
                </div> \
                <br /> \
                <table style="margin: 0px auto; max-width: 95%; width: auto"><tr> \
                <td rowspan="3"><div style="margin: 3%; width: 100%"><p class="input-field"><input id=\"' + text_input_name + '\" type="number" style="width: 90%" value="-1"/></p></div></td> \
                <td><button class="waves-effect waves-light btn grey darken-3" type="button" onclick="setState' + self.id + '(\'ON\', \'' + text_input_name + '\')">ON</button></td> \
                </tr><tr><td><button class="waves-effect waves-light btn grey darken-3" type="button" onclick="setState' + self.id + '(\'OFF\', \'' + text_input_name + '\')">OFF</button></td> \
                </tr><tr><td><button class="waves-effect waves-light btn grey darken-3" type="button" onclick="getState' + self.id + '()">REFRESH</button></td> \
                </tr></table> \
                <script> \
                function update_state_message' + self.id + '(text) \n { \
                   if (text == "OFF") text = "<a style=\\"color: green; font-size: 25px\\">OFF</a>"; \
                   else if (text == "ON") text = "<a style=\\"color: red; font-size: 25px\\">ON</a>"; \
                   else text = "<a style=\\"color: black; font-size: 25px\\">UNKNOWN</a>"; \
                   document.getElementById("esp8266SocketDiv' + self.id + '").innerHTML = text; \
                } \n\
                function getState' + self.id + '() { \
                document.getElementById("esp8266SocketDiv' + self.id + '").innerHTML = "<img src=\\"static/images/loading_spinner.gif\\" style=\\"width: 50px;\\" />"; \
                    getRequest("localhost", ' + self.address + ', "STATE", update_state_message' + self.id + '); \
                } \
                function setState' + self.id + '(state, input_id) { \
                    time_wait = input_id == null ? -1 : document.getElementById(input_id).value; \
                    sendRequest(\'localhost\', ' + self.address + ', state + "," + time_wait); getState' + self.id + '(); \
                } \
                getState' + self.id + '(); \
                setInterval(function() { \n\
                getState' + self.id + '(); \n\
                }, 60*1000);\n\
                </script> \n\
                </div>'

    def _set_socket_state(self, should_turn_on, time_wait):
        state = "OFF"
        if should_turn_on: state = "ON"
        url = "http://" + self.gpio + "/socket.lua?wait=" + time_wait + "&state=" + state
        try:
            request = urllib2.Request(url)
            urllib2.urlopen(request, timeout=5).read()
        except urllib2.URLError, socket.timeout:
            pass


def _siginit_handler(_, __):
    print 'ESP8266: SIGINT signal caught'
    sys.exit(0)


if __name__ == "__main__":
    print 'ESP8266 WiFi socket: started.'
    device_line = sys.argv[1]
    conf_line = sys.argv[2]
    signal.signal(signal.SIGINT, _siginit_handler)

    device_info = c.get_device_entry_data(device_line)
    esp8266 = ESP8266SocketModule(conf_line)
    esp8266.start_work(device_info[0], device_info[1])
