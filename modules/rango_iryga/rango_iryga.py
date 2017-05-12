import re
import signal
import socket
import sys
import threading
import urllib2

import requests
from wrh_engine import module_base as base_module
from utils.io import *

ninput = non_empty_input


class RangoIrygaModule(base_module.Module):
    """
    Rango Iryga module makes it easier for the user to interact with Rango Irygation system.
    """
    TYPE_NUMBER = 7
    TYPE_NAME = "RANGO IRYGA"
    CONFIGURATION_LINE_PATTERN = str(TYPE_NUMBER) + ";([0-9]{1,9});(.+?);(.+?);([1-9][0-9]{0,9})$"
    RELAYS = [5, 4, 15, 14]
    DELAY = 120

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.relay_actions = {i: [] for i in RangoIrygaModule.RELAYS}

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed.
        :param configuration_line:
        :return:
        """
        checker = re.compile(RangoIrygaModule.CONFIGURATION_LINE_PATTERN)
        return checker.match(configuration_line) is not None

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        return ["/usr/bin/python2.7", "-m", "modules.rango_iryga.rango_iryga"]

    def get_configuration_line(self):
        """
        Creates module configuration line.
        :return: Properly formatted configuration file line
        """
        return str(RangoIrygaModule.TYPE_NUMBER) + ";" + str(
            self.id) + ";" + self.name + ";" + self.address + ";" + str(self.port)

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(RangoIrygaModule.CONFIGURATION_LINE_PATTERN, configuration_file_line)
        self.id = int(matches.group(1))
        self.name = str(matches.group(2))
        self.address = str(matches.group(3))
        self.port = str(matches.group(4))

    def get_measurement(self):
        """
        Returns measurements taken by this module
        """
        repeats = [sum([thread.isAlive() for thread in self.relay_actions[relay]]) for relay in RangoIrygaModule.RELAYS]
        value_finding_pattern = ".+?value=\"(.+?)\".+?value=\"(.+?)\".+?value=\"(.+?)\".+?value=\"(.+?)\".+?value=\"(.+?)\".+?value=\"(.+?)\".+?value=\"(.+?)\".+?value=\"(.+?)\".*$"
        checker = re.compile(value_finding_pattern)
        try:
            response = requests.get("http://" + self.address + "/socket.lua")
            # Remove all characters other than letters, numbers or = and " if connection was successful
            response_content = ''.join(e for e in response.content if e.isalnum() or e == '=' or e == '"')
        except requests.ConnectionError:
            response_content = ''
        if not checker.match(str(response_content)):
            state = "<a style=\"color: black; font-size: 25px\">? (" + str(repeats[0]) + ")</a>&" \
                                                                                         "<a style=\"color: black; font-size: 25px\">? (" + str(
                repeats[1]) + ")</a>&" \
                              "<a style=\"color: black; font-size: 25px\">? (" + str(repeats[2]) + ")</a>&" \
                                                                                                   "<a style=\"color: black; font-size: 25px\">? (" + str(
                repeats[3]) + ")</a>"
        else:
            # Socket returns opposite state - we need to change its response
            true_state = {"ON": "<a style=\"color: green; font-size: 25px\">OFF",
                          "OFF": "<a style=\"color: red; font-size: 25px\">ON"}
            search = re.search(value_finding_pattern, str(response_content))
            state = "" + true_state[search.group(1)] + " (" + str(repeats[0]) + ")</a>&" + true_state[
                search.group(3)] + " (" + str(repeats[1]) + ")</a>&" + true_state[
                        search.group(5)] + " (" + str(repeats[2]) + ")</a>&" + true_state[search.group(7)] + " (" + str(
                repeats[3]) + ")</a>"
        return state

    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """
        return "Rango Iryga module used to maintain automatic irrigation system for garden."

    def run_registration_procedure(self, new_id):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, new_id)
        self.address = ninput("Please input Rango Iryga IP address: ")
        while True:
            try:
                self.port = int(ninput(
                    "Please input port on which this module will be listening for commands: "))
                break
            except ValueError:
                pass

    def edit(self):
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
        if new_name: self.name = new_name

    def start_work(self):
        """
        Starts working procedure.
        """
        base_module.Module.start_work(self)
        while self._should_end is False:
            signal.pause()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        """
        my_id = str(self.id)
        port = str(self.port)
        return '<div class="card-panel"> \
                    <h5>' + self.name + '</h5>\
                    \
                    <table style="margin: 0px auto; max-width: 95%; width: auto"><tr><td> \
                    <h5>Linia&nbsp;1</h5> </td><td>\
                    <div id="rangoIrygaDiv_1_' + my_id + '" style="height: 50px; margin: auto">\
                        <img src="static/images/loading_spinner.gif" style="width: 50px;" />\
                    </div></td></tr>\
                    <tr><td><h6>Czas trwania (sek.):</h6></td> \
                    <td><div style="margin: 3%; width: 100%">\
                        <p class="input-field"><input id=\"relay1_time_' + my_id + '\" type=\"number\" style="width: 90%" value="300"/></p>\
                    </div></td></tr>\
                    <tr><td><h6>Liczba cykli:</h6></td> \
                    <td><div style="margin: 3%; width: 100%">\
                        <p class="input-field"><input id=\"relay1_cycles_' + my_id + '\" type=\"number\" style="width: 90%" value="1"/></p>\
                    </div></td></tr>\
                    <tr><td columnspan="2"><a class="dropdown-button btn grey darken-3" href="#" data-activates="dropdown1' + my_id + '">State</a></td></tr></table> \
                    <ul id="dropdown1' + my_id + '" class="dropdown-content"> \
                    <li><a onclick="setState' + my_id + '(\'ON\', 5, \'relay1_time_' + my_id + '\', \'relay1_cycles_' + my_id + '\')">ON</a></li> \
                    <li><a onclick="setState' + my_id + '(\'OFF\', 5, null)">OFF</a></li> \
                    <li><a onclick="getState' + my_id + '(5)">REFRESH</a></li></ul></br> \
                    <div class="line"></div><br \>\
                    \
                    <table style="margin: 0px auto; max-width: 95%; width: auto"><tr><td> \
                    <h5>Linia&nbsp;2</h5> </td><td>\
                    <div id="rangoIrygaDiv_2_' + my_id + '" style="height: 50px; margin: auto">\
                        <img src="static/images/loading_spinner.gif" style="width: 50px;" />\
                    </div></td></tr>\
                    <tr><td><h6>Czas trwania (sek.):</h6></td> \
                    <td><div style="margin: 3%; width: 100%">\
                        <p class="input-field"><input id=\"relay2_time_' + my_id + '\" type=\"number\" style="width: 90%" value="80"/></p>\
                    </div></td></tr>\
                    <tr><td><h6>Liczba cykli:</h6></td> \
                    <td><div style="margin: 3%; width: 100%">\
                        <p class="input-field"><input id=\"relay2_cycles_' + my_id + '\" type=\"number\" style="width: 90%" value="4"/></p>\
                    </div></td></tr>\
                    <tr><td columnspan="2"><a class="dropdown-button btn grey darken-3" href="#" data-activates="dropdown2' + my_id + '">State</a></td></tr></table> \
                    <ul id="dropdown2' + my_id + '" class="dropdown-content"> \
                    <li><a onclick="setState' + my_id + '(\'ON\', 4, \'relay2_time_' + my_id + '\', \'relay2_cycles_' + my_id + '\')">ON</a></li> \
                    <li><a onclick="setState' + my_id + '(\'OFF\', 4, null)">OFF</a></li> \
                    <li><a onclick="getState' + my_id + '(4)">REFRESH</a></li></ul></br> \
                    <div class="line"></div><br \>\
                    \
                    <table style="margin: 0px auto; max-width: 95%; width: auto"><tr><td> \
                    <h5>Linia&nbsp;3</h5> </td><td>\
                    <div id="rangoIrygaDiv_3_' + my_id + '" style="height: 50px; margin: auto">\
                        <img src="static/images/loading_spinner.gif" style="width: 50px;" />\
                    </div></td></tr>\
                    <tr><td><h6>Czas trwania (sek.):</h6></td> \
                    <td><div style="margin: 3%; width: 100%">\
                        <p class="input-field"><input id=\"relay3_time_' + my_id + '\" type=\"number\" style="width: 90%" value="300"/></p>\
                    </div></td></tr>\
                    <tr><td><h6>Liczba cykli:</h6></td> \
                    <td><div style="margin: 3%; width: 100%">\
                        <p class="input-field"><input id=\"relay3_cycles_' + my_id + '\" type=\"number\" style="width: 90%" value="1"/></p>\
                    </div></td></tr>\
                    <tr><td columnspan="2"><a class="dropdown-button btn grey darken-3" href="#" data-activates="dropdown3' + my_id + '">State</a></td></tr></table> \
                    <ul id="dropdown3' + my_id + '" class="dropdown-content"> \
                    <li><a onclick="setState' + my_id + '(\'ON\', 15, \'relay3_time_' + my_id + '\', \'relay3_cycles_' + my_id + '\')">ON</a></li> \
                    <li><a onclick="setState' + my_id + '(\'OFF\', 15, null)">OFF</a></li> \
                    <li><a onclick="getState' + my_id + '(15)">REFRESH</a></li></ul></br> \
                    <div class="line"></div><br \>\
                    \
                    <table style="margin: 0px auto; max-width: 95%; width: auto"><tr><td> \
                    <h5>Linia&nbsp;4</h5> </td><td>\
                    <div id="rangoIrygaDiv_4_' + my_id + '" style="height: 50px; margin: auto">\
                        <img src="static/images/loading_spinner.gif" style="width: 50px;" />\
                    </div></td></tr>\
                    <tr><td><h6>Czas trwania (sek.):</h6></td> \
                    <td><div style="margin: 3%; width: 100%">\
                        <p class="input-field"><input id=\"relay4_time_' + my_id + '\" type=\"number\" style="width: 90%" value="300"/></p>\
                    </div></td></tr>\
                    <tr><td><h6>Liczba cykli:</h6></td> \
                    <td><div style="margin: 3%; width: 100%">\
                        <p class="input-field"><input id=\"relay4_cycles_' + my_id + '\" type=\"number\" style="width: 90%" value="1"/></p>\
                    </div></td></tr>\
                    <tr><td columnspan="2"><a class="dropdown-button btn grey darken-3" href="#" data-activates="dropdown4' + my_id + '">State</a></td></tr></table> \
                    <ul id="dropdown4' + my_id + '" class="dropdown-content"> \
                    <li><a onclick="setState' + my_id + '(\'ON\', 14, \'relay4_time_' + my_id + '\', \'relay4_cycles_' + my_id + '\')">ON</a></li> \
                    <li><a onclick="setState' + my_id + '(\'OFF\', 14, null)">OFF</a></li> \
                    <li><a onclick="getState' + my_id + '(14)">REFRESH</a></li></ul></br> \
                    \
               <script> function update_relay_state_message' + my_id + '(text) \n\
               { states=text.split("&");\
                 document.getElementById("rangoIrygaDiv_1_' + my_id + '").innerHTML = states[0]; \
                 document.getElementById("rangoIrygaDiv_2_' + my_id + '").innerHTML = states[1]; \
                 document.getElementById("rangoIrygaDiv_3_' + my_id + '").innerHTML = states[2]; \
                 document.getElementById("rangoIrygaDiv_4_' + my_id + '").innerHTML = states[3]; \
               } \n\
               function getState' + my_id + '(num) { \
                        if(num == 0 || num == 5) {document.getElementById("rangoIrygaDiv_1_' + my_id + '").innerHTML = "<img src=\\"static/images/loading_spinner.gif\\" style=\\"width: 50px;\\" />";} \
                        if(num == 0 || num == 4) {document.getElementById("rangoIrygaDiv_2_' + my_id + '").innerHTML = "<img src=\\"static/images/loading_spinner.gif\\" style=\\"width: 50px;\\" />";} \
                        if(num == 0 || num == 15) {document.getElementById("rangoIrygaDiv_3_' + my_id + '").innerHTML = "<img src=\\"static/images/loading_spinner.gif\\" style=\\"width: 50px;\\" />";} \
                        if(num == 0 || num == 14) {document.getElementById("rangoIrygaDiv_4_' + my_id + '").innerHTML = "<img src=\\"static/images/loading_spinner.gif\\" style=\\"width: 50px;\\" />";} \
                        getRequest("localhost", ' + port + ', "STATE", update_relay_state_message' + my_id + '); } \
               function setState' + my_id + '(state, gpio, input_id, input_id2) { \
                        time_wait = input_id == null ? -1 : document.getElementById(input_id).value; \
                        repeats = input_id == null ? -1 : document.getElementById(input_id2).value; \
                        sendRequest(\'localhost\', ' + port + ', state + "," + gpio + "," + time_wait + "," + repeats); \
                        setTimeout(getState' + my_id + '(gpio), 500); } \
               getState' + my_id + '(0); \
               setInterval(function() { \n\
               getState' + my_id + '(0); \n\
               }, 60*1000);\n\
               </script> \n\
               </div>'

    def _stop_already_working_relay_threads(self, relay_number):
        thread_list = self.relay_actions[relay_number]
        for thread in thread_list:
            thread.cancel()
            thread.join()
        del thread_list[:]

        return thread_list

    def _set_relay_state(self, relay_number, should_turn_on, duration, repeats):
        duration = self._parse_duration_value(should_turn_on, duration)
        repeats = self._parse_repeats_value(should_turn_on, repeats)
        thread_list = self._stop_already_working_relay_threads(int(relay_number))

        latency = 0
        for i in xrange(repeats):
            self._create_watering_thread(thread_list, latency, relay_number, should_turn_on, duration)
            latency += (duration + RangoIrygaModule.DELAY)

    def _create_watering_thread(self, thread_list, latency, relay_number, should_turn_on, duration):
        thread = threading.Timer(latency, self._set_relay_state_on_esp,
                                 args=(relay_number, should_turn_on, duration))
        thread.daemon = True
        thread.start()
        if not should_turn_on:
            thread.join()
        else:
            thread_list.append(thread)

    def _parse_duration_value(self, should_turn_on, duration):
        # Duration value should be from range [-1, 600]
        # If the desired state of the Rango Iryga is OFF then duration is undefined (infinity)
        try:
            duration = int(duration)
            if duration < -1 or duration > 600:
                raise ValueError
        except ValueError:
            if should_turn_on:
                duration = '60'
            else:
                duration = ''

        return duration

    def _parse_repeats_value(self, should_turn_on, repeats):
        # Repeats value should be positive integer, bigger than 0.
        # If the desired state of the Rango Iryga is OFF then repeats should be equal to 1.
        try:
            repeats = int(repeats)
            if (should_turn_on and repeats < 1) or (not should_turn_on):
                repeats = 1
        except ValueError:
            repeats = 1

        return repeats

    def _set_relay_state_on_esp(self, relay_number, should_turn_on, duration):
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
                urllib2.urlopen(request, timeout=5).read()
            except urllib2.URLError, socket.timeout:
                pass
        except ValueError:
            pass

    def _react_to_connection(self, connection, _):
        data = str(connection.recv(1024) + ",,,").split(',')
        state, number, time_wait, repeats = data[0], data[1], data[2], data[3]
        if str(state) == "ON" or str(state) == "on":
            self._set_relay_state(number, True, time_wait, repeats)
        elif str(state) == "OFF" or str(state) == "off":
            self._set_relay_state(number, False, time_wait, repeats)
        elif str(state) == "STATE" or str(state) == "state":
            connection.send(self.get_measurement())


if __name__ == "__main__":
    print 'Rango Iryga module: started.'
    conf_line = sys.argv[1]

    rango_iryga = RangoIrygaModule(conf_line)
    rango_iryga.start_work()
