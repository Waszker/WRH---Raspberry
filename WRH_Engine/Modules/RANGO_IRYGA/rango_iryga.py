from WRH_Engine.Module import module_base as base_module
from WRH_Engine.Configuration import configuration as c
from WRH_Engine.Utils import utils as u
from WRH_Engine.WebApiLibrary import WebApiClient as w
import sys
import signal
import re
import time
import requests
import socket
import urllib2


class RangoIrygaModule(base_module.Module):
    """
    Rango Iryga module makes it easier for the user to interact with Rango Irygation system.
    """
    type_number = 7
    type_name = "RANGO IRYGA"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.type_number = RangoIrygaModule.type_number
        self.type_name = RangoIrygaModule.type_name

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed.
        :param self:
        :param configuration_line:
        :return:
        """
        # Configuration line for camera should look like this:
        # TYPE_NUM=7 ; ID=INT ; NAME=STRING ; ADDRESS=STRING ; PORT=INT
        configuration_line_pattern = str(RangoIrygaModule.type_number) + \
                                     ";([1-9][0-9]{0,9});(.+?);(.+?);([1-9][0-9]{0,9})$"
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
        # TODO: Return command used to start module by OVERLORD program
        return ["/usr/bin/python2.7", "-m", "WRH_Engine.Modules.RANGO_IRYGA.rango_iryga"]

    def get_configuration_line(self):
        """
        Creates module configuration line.
        :return: Properly formatted configuration file line
        """
        return str(self.type_number) + ";" + str(self.id) + ";" + self.name + ";" + self.address + ";" + str(self.port)

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        configuration_line_pattern = self.is_configuration_line_sane(configuration_file_line)
        matches = re.search(configuration_line_pattern, configuration_file_line)
        self.id = int(matches.group(1))
        self.name = str(matches.group(2))
        self.address = str(matches.group(3))
        self.port = str(matches.group(4))

    def get_measurement(self):
        """
        Returns measurements taken by this module
        """
        time.sleep(1)  # Too fast polling resets ESP8266!
        value_finding_pattern = ".+?value=\"(.+?)\".+?value=\"(.+?)\".+?value=\"(.+?)\".+?value=\"(.+?)\".+?value=\"(.+?)\".+?value=\"(.+?)\".+?value=\"(.+?)\".+?value=\"(.+?)\".*$"
        checker = re.compile(value_finding_pattern)
        try:
            response = requests.get("http://" + self.address + "/socket.lua")
            # Remove all characters other than letters, numbers or = and " if connection was successful
            response_content = ''.join(e for e in response.content if e.isalnum() or e == '=' or e == '"')
        except requests.ConnectionError:
            response_content = ''
        if not checker.match(str(response_content)):
            state = "Unable to obtain socket states... Try again later."
        else:
            # Socket returns opposite state - we need to change its response
            true_state = {"ON": "<a style=\"color: green\">OFF</a>", "OFF": "<a style=\"color: red\">ON</a>"}
            search = re.search(value_finding_pattern, str(response_content))
            state = "Relay 1: " + true_state[search.group(1)] + "<br />Relay 2: " + true_state[
                search.group(3)] + "<br />Relay 3: " + true_state[
                        search.group(5)] + "<br />Relay 4: " + true_state[search.group(7)]
        return state

    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """
        return "Rango Iryga module used to maintain automatic irrigation system for garden."

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
        self.address = u.get_non_empty_input("Please input Rango Iryga IP address: ")
        while True:
            try:
                self.port = int(u.get_non_empty_input(
                    "Please input port on which this module will be listening for commands: "))
                break
            except ValueError:
                pass
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
        new_address = raw_input("Please input new Rango Iryga IP address: ")
        new_port = raw_input("Please input new port on which this module will be listening for commands: ")

        if new_address: self.address = new_address
        if new_port: self.port = new_port
        if new_name:
            return base_module.Module.update_module_information_in_wrh(self, device_id, device_token, new_name)
        return (w.Response.STATUS_OK, '')

    def start_work(self, device_id, device_token):
        """
        Starts working procedure.
        """
        host = ''
        port = self.port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                s.bind((host, int(port)))
                break
            except socket.error as msg:
                print 'Rango Iryga ' + self.address + ' port bind failed. Error Code : ' + str(
                    msg[0]) + ' Message ' + msg[1]
                time.sleep(10)  # Sleep 10 seconds before retrying
        print "Rango Iryga: " + self.address + " started listening"
        while True:
            s.listen(10)
            connection, address = s.accept()
            data = str(connection.recv(1024) + ",,").split(',')
            state, number, time_wait = data[0], data[1], data[2]
            if str(state) == "ON" or str(state) == "on":
                self._set_relay_state(number, True, time_wait)
            elif str(state) == "OFF" or str(state) == "off":
                self._set_relay_state(number, False, time_wait)
            elif str(state) == "STATE" or str(state) == "state":
                connection.send(self.get_measurement())
            connection.close()
        s.close()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        """
        # TODO: Add text input for time specifying!
        my_id = str(self.id)
        port = str(self.port)
        return '<div style="border:1px solid black;"> \
               <script> function update_relay_state_message' + my_id + '(text) \n\
               { document.getElementById("rangoIrygaDiv' + my_id + '").innerHTML = text; } \n\
               function getState' + my_id + '() { getRequest("localhost", ' + port + ', "STATE", update_relay_state_message' + my_id + '); } \
               function setState' + my_id + '(state, gpio, wait) { \
                        sendRequest(\'localhost\', ' + port + ', state + "," + gpio + "," + wait); \
                        getState' + my_id + '(); } \
               getState' + my_id + '(); \
               setInterval(function() { \n\
               getState' + my_id + '(); \n\
               }, 60*1000);\n\
               </script> \n\
                    <center>' + self.name + '</center>\
                    <div id="rangoIrygaDiv' + my_id + '" class="rangoIrygaDiv"> </div>\
                    <br />\
                    <table style="margin: 0px auto; width: 95%"><tr><td> \
                    Relay&nbsp;1 </td>\
                    <td><input id=\"relay1_' + my_id + '\" type=\"number\" style="margin: 3%; width: 33%"/></td> \
                    <td style="padding-left: 5%"><button type="button" onclick="setState' + my_id + '(\'ON\', 5, 10)">ON</button></td> \
                    <td style="padding-left: 5%"><button type="button" onclick="setState' + my_id + '(\'OFF\', 5, -1)">OFF</button></td></tr> \
                    <tr>\
                    <td>Relay&nbsp;2</td> \
                    <td><input id=\"relay2_' + my_id + '\" type=\"number\" style="margin: 3%; width: 33%"/></td> \
                    <td style="padding-left: 5%"><button type="button" onclick="setState' + my_id + '(\'ON\', 4, 10)">ON</button></td> \
                    <td style="padding-left: 5%"><button type="button" onclick="setState' + my_id + '(\'OFF\', 4, -1)">OFF</button></td></tr> \
                    <tr>\
                    <td>Relay&nbsp;3</td> \
                    <td><input id=\"relay3_' + my_id + '\" type=\"number\" style="margin: 3%; width: 33%"/></td> \
                    <td style="padding-left: 5%"><button type="button" onclick="setState' + my_id + '(\'ON\', 15, 10)">ON</button></td> \
                    <td style="padding-left: 5%"><button type="button" onclick="setState' + my_id + '(\'OFF\', 15, -1)">OFF</button></td></tr> \
                    <tr>\
                    <td>Relay&nbsp;4</td> \
                    <td><input id=\"relay4_' + my_id + '\" type=\"number\" style="margin: 3%; width: 33%"/></td> \
                    <td style="padding-left: 5%"><button type="button" onclick="setState' + my_id + '(\'ON\', 4, 10)">ON</button></td> \
                    <td style="padding-left: 5%"><button type="button" onclick="setState' + my_id + '(\'OFF\', 5, -1)">OFF</button></td></tr> \
                    </table> \
               </div>'

    def _set_relay_state(self, relay_number, should_turn_on, duration):
        # First get duration for relay opening
        try:
            duration = int(duration)
        except ValueError:
            if should_turn_on:
                duration = 60
            else:
                duration = ''

        # Then change relay's state
        try:
            relay_number = int(relay_number)
            state = "OFF"
            if should_turn_on: state = "ON"
            url = "http://" + self.address + "/socket.lua?wait=" + str(duration) + "&state=" + str(
                state) + "&gpio_num=" + str(
                relay_number)
            try:
                request = urllib2.Request(url)
                urllib2.urlopen(request).read()
            except urllib2.URLError:
                pass
        except ValueError:
            pass


def _siginit_handler(_, __):
    print "RANG IRYGA: SIGINT signal caught"
    sys.exit(0)


if __name__ == "__main__":
    print 'Rango Iryga module: started.'
    device_line = sys.argv[1]
    conf_line = sys.argv[2]
    signal.signal(signal.SIGINT, _siginit_handler)

    device_info = c.get_device_entry_data(device_line)
    dummy = RangoIrygaModule(conf_line)
    dummy.start_work(device_line[0], device_line[1])
