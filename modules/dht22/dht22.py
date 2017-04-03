import re
import signal
import socket
import sys
import threading
import time

import Adafruit_DHT
from wrh_engine import module_base as base_module
from utils.io import *

ninput = non_empty_input
iinput = non_empty_positive_numeric_input


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
    configuration_line_pattern = str(type_number) + ";([0-9]{1,9});(.+?);([1-9][0-9]{0,9});([1-9][0-9]{0,9});(.+)$"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.type_number = DHT22Module.type_number
        self.type_name = DHT22Module.type_name
        self.last_temperature, self.last_humidity, self.socket = None, None, None
        self.should_end = False

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed.
        :param self:
        :param configuration_line:
        :return:
        """
        # Configuration line for camera should look like this:
        # TYPE_NUM=1 ; ID=INT ; NAME=STRING ; GPIO=INT ; INTERVAL=INT ; ADDRESS=STRING
        checker = re.compile(DHT22Module.configuration_line_pattern)
        return checker.match(configuration_line) is not None

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        return ["/usr/bin/python2.7", "-m", "modules.dht22.dht22"]

    def get_configuration_line(self):
        """
        Creates module configuration line.
        :return: Properly formatted configuration file line
        """
        return "%s;%s;%s;%s;%s;%s" % tuple(map(str, (self.type_number, self.id, self.name, self.gpio,
                                                     self.interval, self.address)))

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(DHT22Module.configuration_line_pattern, configuration_file_line)
        self.id = matches.group(1)
        self.name = matches.group(2)
        self.gpio = int(matches.group(3))
        self.interval = int(matches.group(4))
        self.address = matches.group(5)

    def get_measurement(self):
        """
        Returns two float variables: humidity and temperature.
        """
        return Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, self.gpio)

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

    def run_registration_procedure(self, new_id):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, new_id)
        self.gpio = iinput("Please input gpio pin number to which sensor is connected: ")
        self.interval = iinput("Please input interval (in minutes) for taking consecutive measurements: ")
        self.address = iinput("Please input port on which this module will be listening for commands: ")

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

        if new_gpio: self.gpio = new_gpio
        if new_interval: self.interval = new_interval
        if new_address: self.address = new_address
        if new_name: self.name = new_name

    def start_work(self):
        """
        Starts working procedure.
        """
        signal.signal(signal.SIGINT, self._sigint_handler)
        web_thread = threading.Thread(target=self._web_service_thread)
        measurement_thread = threading.Thread(target=self._measurement_thread)
        measurement_thread.daemon, web_thread.daemon = True, False
        [thread.start() for thread in (web_thread, measurement_thread)]
        while self.should_end is False:
            signal.pause()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        """
        return '<div class="card-panel"> \
               <script> function update_measurements_dht22_' + self.id + '(text) \n\
               { var res = text.split(";"); var h = res[0]; var t = res[1]; \
               document.getElementById("dht22Div' + self.id + '").innerHTML = "Humidity: " + h + "% Temperature: " + t + "*C"; } \n\
               function getMeasurements' + self.id + '() { getRequest("localhost", ' + self.address + ', "", update_measurements_dht22_' + self.id + '); } \
               getMeasurements' + self.id + '(); \
               setInterval(function() { \n\
               getMeasurements' + self.id + '(); \n\
               }, 60*1000);\n\
               </script> \n\
               <h5>' + self.name + '</h5>\
               <div id="dht22Div' + self.id + '" class="dht22Div"> </div>\
               </div>'

    def _measurement_thread(self):
        while self.should_end is False:
            try:
                self.last_humidity, self.last_temperature = self.get_measurement()
                # TODO: Send those values to WRH?
                time.sleep(self.interval * 60)
            except exceptions.AttributeError:
                pass

    def _web_service_thread(self):
        self.socket = self._bind_to_socket()
        print DHT22Module.type_name + " " + self.name + " started listening"
        try:
            self._await_connection()
            self.socket.close()
        except socket.error as e:
            pass

    def _bind_to_socket(self):
        host = ''
        port = self.address
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                s.bind((host, int(port)))
                break
            except socket.error as msg:
                print DHT22Module.type_name + " " + self.name + ' port bind failed. Error Code : ' + str(
                    msg[0]) + ' Message ' + msg[1]
                time.sleep(10)  # Sleep 10 seconds before retrying
        return s

    def _await_connection(self):
        self.socket.listen(10)
        while self.should_end is False:
            connection, address = self.socket.accept()
            if self.last_temperature is not None and self.last_humidity is not None:
                connection.send('{0:0.1f};{1:0.1f}'.format(self.last_humidity, self.last_temperature))
            else:
                connection.send('?;?')
            connection.close()

    def _sigint_handler(self, *_):
        self.should_end = True
        if self.socket is not None:
            self.socket.shutdown(socket.SHUT_RDWR)


if __name__ == "__main__":
    print 'DHT22 module: started.'
    conf_line = sys.argv[1]

    dht22 = DHT22Module(conf_line)
    dht22.start_work()
