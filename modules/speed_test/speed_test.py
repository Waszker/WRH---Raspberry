import re
import subprocess
import sys
import threading
import time
import signal

from wrh_engine import module_base as base_module
from utils.io import *

ninput = non_empty_input


class SpeedTestModule(base_module.Module):
    """
    This is Internet speed test module that checks Internet connection speed regularly.
    It's not recommended to add more than one speed test to WRH system.
    """
    type_number = 6
    type_name = "INTERNET SPEED TEST"
    configuration_line_pattern = str(type_number) + ";([0-9]{1,9});(.+?);([1-9][0-9]{0,9});([1-9][0-9]{0,9})$"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.type_number = SpeedTestModule.type_number
        self.type_name = SpeedTestModule.type_name
        self.last_download, self.last_upload = "? Mbit/s", "? Mbit/s"

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed.
        :param self:
        :param configuration_line:
        :return:
        """
        # Configuration line for camera should look like this:
        # TYPE_NUM=6 ; ID=INT ; NAME=STRING ; INTERVAL=INT ; ADDRESS=INT
        checker = re.compile(SpeedTestModule.configuration_line_pattern)
        return checker.match(configuration_line) is not None

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        return ["/usr/bin/python2.7", "-m", "modules.speed_test.speed_test"]

    def get_configuration_line(self):
        """
        Creates module configuration line.
        :return: Properly formatted configuration file line
        """
        return str(self.type_number) + ";" + str(self.id) + ";" + self.name + ";" + str(self.interval) + ";" + str(
            self.address)

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(SpeedTestModule.configuration_line_pattern, configuration_file_line)
        self.id = matches.group(1)
        self.name = matches.group(2)
        self.interval = int(matches.group(3))
        self.address = int(matches.group(4))

    def get_measurement(self):
        """
        Returns measurements taken by this module: two strings with download and upload speed values.
        """
        command = ["/usr/bin/python2.7", "modules/speed_test/speedtest-cli/speedtest_cli.py"]
        try:
            results = subprocess.check_output(command)
        except subprocess.CalledProcessError:
            results = ""
        results = results.replace('\n', '')
        print "The results are as follows: " + str(results)
        pattern = ".+?Download: (.+?/s).+?Upload: (.+?/s).*"
        checker = re.compile(pattern)

        if not checker.match(str(results)):
            download, upload = "0 Mbit/s", "0 Mbit/s"
        else:
            download = re.search(pattern, results).group(1)
            upload = re.search(pattern, results).group(2)

        return download, upload

    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """
        return "Internet Speed Test module that runs tests and reports upload and download link speeds"

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
        while True:
            self.interval = SpeedTestModule._parse_input_as_integer(ninput(
                "Please input interval (in minutes) for taking consecutive measurements: "))
            if self.interval > 0: break
        while True:
            self.address = SpeedTestModule._parse_input_as_integer(ninput(
                "Please input port on which this module will be listening for commands: "))
            if self.address > 0: break

    def edit(self, device_id, device_token):
        """
        Runs interactive procedure to edit module.
        Returns connection status and response.
        """
        print 'Provide new module information (leave fields blank if you don\'t want to change)'
        print 'Please note that changes other than name will always succeed'
        print 'Name changing requires active Internet connection'
        new_name = raw_input('New module\'s name: ')
        new_interval = raw_input("Please input new interval (in minutes) for taking consecutive measurements: ")
        new_address = raw_input("Please input new port on which this module will be listening for commands: ")

        if new_interval and self._parse_input_as_integer(new_interval) > 0: self.interval = new_interval
        if new_address: self.address = new_address
        if new_name: self.name = new_name

    def start_work(self):
        """
        Starts working procedure.
        """
        base_module.Module.start_work(self)
        measurement_thread = threading.Thread(target=self._measurement_thread)
        measurement_thread.daemon = True
        measurement_thread.start()

        while self.should_end is False:
            signal.pause()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        """
        return '<div class="card-panel"> \
               <script> function update_measurements_speedtest_' + str(self.id) + '(text) \n\
               { document.getElementById("speedTestDiv' + str(self.id) + '").innerHTML = text; } \n\
               function getMeasurements' + str(self.id) + '() { getRequest("localhost", ' + str(self.address) + ', "", \
               update_measurements_speedtest_' + str(self.id) + '); } \
               getMeasurements' + str(self.id) + '(); \
               setInterval(function() { \n\
               getMeasurements' + str(self.id) + '(); \n\
               }, 60*1000);\n\
               </script> \n\
               <h5>' + str(self.name) + '</h5>\
               <div id="speedTestDiv' + str(self.id) + '" class="speedTestDiv"> </div>\
               </div>'

    def react_to_connection(self, connection, _):
        connection.send(str(self.last_download) + " " + str(self.last_upload))

    def _measurement_thread(self):
        while self.should_end is False:
            self.last_download, self.last_upload = self.get_measurement()
            time.sleep(self.interval * 60)

    @staticmethod
    def _parse_input_as_integer(text):
        try:
            return int(text)
        except ValueError:
            return -1


if __name__ == "__main__":
    print 'SpeedTest module: started.'
    conf_line = sys.argv[1]

    speedtest = SpeedTestModule(conf_line)
    speedtest.start_work()
