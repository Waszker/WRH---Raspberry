from WRH_Engine.Module import module_base as base_module
from WRH_Engine.Configuration import configuration as c
from WRH_Engine.Utils import utils as u
from WRH_Engine.WebApiLibrary import WebApiClient as w
import Adafruit_DHT
import threading
import os
import sys
import re
import socket
import time
import signal


class DHT22Module(base_module.Module):
    """
    This class works with DHT22 temperature and humidity sensor.
    Adafruit_Python_DHT package is required by this module.
    Installation instructions:
    $ git clone https://github.com/adafruit/Adafruit_Python_DHT.git
    $ cd Adafruit_Python_DHT
    $ sudo python setup.py install
    """
    type_number = 1
    type_name = "DHT22 TEMP./HUM. SENSOR"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.type_number = DHT22Module.type_number
        self.type_name = DHT22Module.type_name
        self.last_temperature, self.last_humidity = None, None

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed.
        :param self:
        :param configuration_line:
        :return:
        """
        # Configuration line for camera should look like this:
        # TYPE_NUM=4 ; ID=INT ; NAME=STRING ; GPIO=INT ; INTERVAL=INT ; ADDRESS=STRING
        configuration_line_pattern = \
            "([1-9][0-9]{0,9});([1-9][0-9]{0,9});(.+?);([1-9][0-9]{0,9});([1-9][0-9]{0,9});(.+)$"
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
        return ["/usr/bin/python2.7", "-m", "WRH_Engine.Modules.DHT22.dht22"]

    def get_configuration_line(self):
        """
        Creates module configuration line.
        :return: Properly formatted configuration file line
        """
        return str(self.type_number) + ";" + str(
            self.id) + ";" + self.name + ";" + str(self.gpio) + ";" + str(self.interval) + ";" + self.address

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        configuration_line_pattern = self.is_configuration_line_sane(configuration_file_line)
        matches = re.search(configuration_line_pattern, configuration_file_line)
        self.id = matches.group(2)
        self.name = matches.group(3)
        self.gpio = int(matches.group(4))
        self.interval = int(matches.group(5))
        self.address = matches.group(6)

    def get_measurement(self):
        """
        Returns two float variables: humidity and temperature.
        """
        return Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, self.gpio)

    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """
        return "DHT22 temperature and humidity sensor"

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
        while True:
            self.gpio = self._check_if_input_is_positive_integer(
                u.get_non_empty_input("Please input gpio pin number to which sensor is connected: "))
            if self.gpio > 0: break
        while True:
            self.interval = self._check_if_input_is_positive_integer(u.get_non_empty_input(
                "Please input interval (in minutes) for taking consecutive measurements: "))
            if self.interval > 0: break
        self.address = u.get_non_empty_input("Please input port on which this module will be listening for commands: ")
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
        new_gpio = raw_input("Please input new gpio pin number to which sensor is connected: ")
        new_interval = raw_input("Please input new interval (in minutes) for taking consecutive measurements: ")
        new_address = raw_input("Please input new port on which this module will be listening for commands: ")

        if new_gpio and self._check_if_input_is_positive_integer(new_gpio) > 0: self.gpio = new_gpio
        if new_interval and self._check_if_input_is_positive_integer(new_interval) > 0: self.interval = new_interval
        if new_address: self.address = new_address
        if new_name:
            return base_module.Module.update_module_information_in_wrh(self, device_id, device_token, new_name)
        return (w.Response.STATUS_OK, '')

    def start_work(self, device_id, device_token):
        """
        Starts working procedure.
        """
        web_thread = threading.Thread(target=self._web_service_thread)
        web_thread.start()

        while True:
            self.last_humidity, self.last_temperature = self.get_measurement()
            # TODO: Send those values to WRH?
            time.sleep(self.interval * 60)

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        """
        return '<div style="border:1px solid black;"> \
               <script> function update_measurements_dht22_' + self.id + '(text) \n\
               { var res = text.split(";"); var h = res[0]; var t = res[1]; \
               document.getElementById("dht22Div' + self.id + '").innerHTML = "Humidity: " + h + "% Temperature: " + t + "*C"; } \n\
               function getMeasurements' + self.id + '() { getRequest("localhost", ' + self.address + ', "", update_measurements_dht22_' + self.id + '); } \
               getMeasurements' + self.id + '(); \
               setInterval(function() { \n\
               getMeasurements' + self.id + '(); \n\
               }, 60*1000);\n\
               </script> \n\
               <center>' + self.name + '</center>\
               <div id="dht22Div' + self.id + '" class="dht22Div"> </div>\
               </div>'

    def _web_service_thread(self):
        host = ''
        port = self.address
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                s.bind((host, int(port)))
                break
            except socket.error as msg:
                print DHT22Module.type_name + " " + self.name + 'port bind failed. Error Code : ' + str(
                    msg[0]) + ' Message ' + msg[1]
                time.sleep(10)  # Sleep 10 seconds before retrying
        print DHT22Module.type_name + " " + self.name + " started listening"
        while True:
            s.listen(10)
            connection, address = s.accept()
            connection.send('{0:0.1f};{1:0.1f}'.format(self.last_humidity, self.last_temperature))
            connection.close()
        s.close()

    def _check_if_input_is_positive_integer(self, text):
        try:
            return int(text)
        except ValueError:
            return -1


def _siginit_handler(_, __):
    print "DHT22: SIGINT signal caught"
    os._exit(0)


if __name__ == "__main__":
    print 'DHT22 module: started.'
    device_line = sys.argv[1]
    conf_line = sys.argv[2]
    signal.signal(signal.SIGINT, _siginit_handler)

    device_info = c.get_device_entry_data(device_line)
    dht22 = DHT22Module(conf_line)
    dht22.start_work(device_line[0], device_line[1])
