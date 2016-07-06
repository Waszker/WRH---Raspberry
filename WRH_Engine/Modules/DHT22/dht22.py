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


class DHT22Module(base_module.Module):
    """
    This class works with DHT22 temperature and humidity sensor.
    """
    type_number = 1
    type_name = "DHT22 TEMP./HUM. SENSOR"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.type_number = DHT22Module.type_number
        self.type_name = DHT22Module.type_name

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed
        :param self:
        :param configuration_line:
        :return:
        """
        # Configuration line for camera should look like this:
        # TYPE_NUM=4 ; ID=INT ; NAME=STRING ; GPIO=STRING ; ADDRESS=STRING
        # TODO: Change it
        configuration_line_pattern = "([1-9][0-9]{0,9});([1-9][0-9]{0,9});(.+?);(.+?);(.+)$"
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
        Creates module configuration line
        :return: Properly formatted configuration file line
        """
        return str(self.type_number) + ";" + str(self.id) + ";" + self.name + ";" + self.gpio + ";" + self.address

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        # TODO: Change it
        configuration_line_pattern = self.is_configuration_line_sane(configuration_file_line)
        matches = re.search(configuration_line_pattern, configuration_file_line)
        self.id = matches.group(2)
        self.name = matches.group(3)
        self.gpio = matches.group(4)
        self.address = matches.group(5)

    def get_measurement(self):
        """
        """
        # TODO: Change it
        return ""

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
        # TODO: Change it
        return base_module.Module.register_in_wrh(self, device_id, device_token)

    def edit(self, device_id, device_token):
        """
        Runs interactive procedure to edit module.
        Returns connection status and response.
        """
        # TODO: Change it

    def start_work(self, device_id, device_token):
        """
        Starts working procedure.
        """
        # TODO: Change it

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        """
        # TODO: Change it


if __name__ == "__main__":
    print 'DHT22 module: started.'
    device_line = sys.argv[1]
    conf_line = sys.argv[2]

    device_info = c.get_device_entry_data(device_line)
    # TODO: Change it
