import re
import signal
import sys
import threading
import time

import Adafruit_DHT

from utils.database import send_measurement
from wrh_engine import module_base as base_module
from utils.io import *
from utils.decorators import in_thread

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
    TYPE_NAME = "DHT22 TEMP./HUM. SENSOR"
    CONFIGURATION_LINE_PATTERN = "([0-9]{1,9});(.+?);([1-9][0-9]{0,9});([1-9][0-9]{0,9});(.+)$"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.last_temperature, self.last_humidity, self.socket, self.html_repr = None, None, None, None

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed.
        :param configuration_line:
        :return:
        """
        checker = re.compile(DHT22Module.CONFIGURATION_LINE_PATTERN)
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
        return "%s;%s;%s;%s;%s" % tuple(map(str, (self.id, self.name, self.gpio, self.interval, self.port)))

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(DHT22Module.CONFIGURATION_LINE_PATTERN, configuration_file_line)
        self.id = matches.group(1)
        self.name = matches.group(2)
        self.gpio = int(matches.group(3))
        self.interval = int(matches.group(4))
        self.port = matches.group(5)

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

    def run_registration_procedure(self, new_id):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, new_id)
        self.gpio = iinput("Please input gpio pin number to which sensor is connected: ")
        self.interval = iinput("Please input interval (in minutes) for taking consecutive measurements: ")
        self.port = iinput("Please input port on which this module will be listening for commands: ")

    def edit(self):
        """
        Runs interactive procedure to edit module.
        Returns connection status and response.
        """
        log('Provide new module information (leave fields blank if you don\'t want to change)')
        log('Please note that changes other than name will always succeed')
        log('Name changing requires active Internet connection')
        new_name = raw_input('New module\'s name: ')
        new_gpio = raw_input("Please input new gpio pin number to which sensor is connected: ")
        new_interval = raw_input("Please input new interval (in minutes) for taking consecutive measurements: ")
        new_port = raw_input("Please input new port on which this module will be listening for commands: ")

        if new_gpio: self.gpio = new_gpio
        if new_interval: self.interval = new_interval
        if new_port: self.port = new_port
        if new_name: self.name = new_name

    def start_work(self):
        """
        Starts working procedure.
        """
        base_module.Module.start_work(self)
        self._measurement_thread()
        while self._should_end is False:
            signal.pause()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        """
        if not self.html_repr:
            with wrh_open('modules/dht22/html/repr.html', 'r') as f:
                html = f.read()
                self.html_repr = html.format(id=self.id, name=self.name, port=self.port)
        return self.html_repr

    @in_thread
    def _measurement_thread(self):
        while self._should_end is False:
            try:
                self.last_humidity, self.last_temperature = self.get_measurement()
                send_measurement(self.id, (self.last_humidity, self.last_temperature))
                time.sleep(self.interval * 60)
            except AttributeError:
                pass

    def _react_to_connection(self, connection, _):
        if self.last_temperature is not None and self.last_humidity is not None:
            connection.send('{0:0.1f};{1:0.1f}'.format(self.last_humidity, self.last_temperature))
        else:
            connection.send('?;?')


if __name__ == "__main__":
    log('DHT22 module: started.')
    conf_line = sys.argv[1]

    dht22 = DHT22Module(conf_line)
    dht22.start_work()
