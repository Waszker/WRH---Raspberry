from WRH_Engine.Module import module_base as base_module
from WRH_Engine.Configuration import configuration as c
import WRH_Engine.Utils.utils as u
from WRH_Engine.WebApiLibrary import WebApiClient as w
import sys
import re
import signal
import subprocess
import time
import threading
import socket


class SpeedTestModule(base_module.Module):
    """
    This is speed test module that checks Internet connection speed regularly.
    """
    type_number = 6
    type_name = "INTERNET SPEED TEST"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.type_number = SpeedTestModule.type_number
        self.type_name = SpeedTestModule.type_name
        self.last_download, self.last_upload = "0M bit/s", "0 Mbit/s"

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed.
        :param self:
        :param configuration_line:
        :return:
        """
        # Configuration line for camera should look like this:
        # TYPE_NUM=4 ; ID=INT ; NAME=STRING ; INTERVAL=INT ; ADDRESS=INT
        configuration_line_pattern = "([1-9][0-9]{0,9});([1-9][0-9]{0,9});(.+?);([1-9][0-9]{0,9});([1-9][0-9]{0,9})$"
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
        return ["/usr/bin/python2.7", "-m", "WRH_Engine.Modules.SPEED_TEST.speed_test"]

    def get_configuration_line(self):
        """
        Creates module configuration line.
        :return: Properly formatted configuration file line
        """
        return str(self.type_number) + ";" + str(self.id) + ";" + self.name + ";" + str(self.interval) + ";" + str(self.address)

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        configuration_line_pattern = self.is_configuration_line_sane(configuration_file_line)
        matches = re.search(configuration_line_pattern, configuration_file_line)
        self.id = matches.group(2)
        self.name = matches.group(3)
        self.interval = int(matches.group(4))
        self.address = int(matches.group(5))

    def get_measurement(self):
        """
        Returns measurements taken by this module: two strings with download and upload speed values.
        """
        command = ["/usr/bin/python2.7", "WRH_Engine/Modules/SPEED_TEST/speedtest-cli/speeedtest_cli.py"]
        results = subprocess.check_output(command)
        pattern = ".+?Download: (.+?)\n.+?Upload: (.+?)\n.*"
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

    def run_registration_procedure(self, device_id, device_token):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, device_id, device_token)
        while True:
            self.interval = SpeedTestModule._parse_input_as_integer(u.get_non_empty_input(
                "Please input interval (in minutes) for taking consecutive measurements: "))
            if self.interval > 0: break
        while True:
            self.address = SpeedTestModule._parse_input_as_integer(u.get_non_empty_input(
                "Please input port on which this module will be listening for commands: "))
            if self.address > 0: break
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
        new_interval = raw_input("Please input new interval (in minutes) for taking consecutive measurements: ")
        new_address = raw_input("Please input new port on which this module will be listening for commands: ")

        if new_interval and self._parse_input_as_integer(new_interval) > 0: self.interval = new_interval
        if new_address: self.address = new_address
        if new_name:
            return base_module.Module.update_module_information_in_wrh(self, device_id, device_token, new_name)
        return (w.Response.STATUS_OK, '')

    def start_work(self, device_id, device_token):
        """
        Starts working procedure.
        """
        web_thread = threading.Thread(target=self._web_service_thread())
        web_thread.daemon = True
        web_thread.start()

        while True:
            self.last_download, self.last_upload = self.get_measurement()
            time.sleep(self.interval)

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        """
        return '<div style="border:1px solid black;"> \
               <script> function update_measurements_speedtest_' + str(self.id) + '(text) \n\
               { document.getElementById("speedTestDiv' + str(self.id) + '").innerHTML = text; } \n\
               function getMeasurements' + str(self.id) + '() { getRequest("localhost", ' + str(self.address) + ', "", \
               update_measurements_speedtest_' + str(self.id) + '); } \
               getMeasurements' + str(self.id) + '(); \
               setInterval(function() { \n\
               getMeasurements' + str(self.id) + '(); \n\
               }, 60*1000);\n\
               </script> \n\
               <center>' + str(self.name) + '</center>\
               <div id="speedTestDiv' + str(self.id) + '" class="speedTestDiv"> </div>\
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
                print SpeedTestModule.type_name + " " + self.name + 'port bind failed. Error Code : ' + str(
                    msg[0]) + ' Message ' + msg[1]
                time.sleep(10)  # Sleep 10 seconds before retrying
        print SpeedTestModule.type_name + " " + self.name + " started listening"
        while True:
            s.listen(10)
            connection, address = s.accept()
            connection.send(str(self.last_download) + " " + str(self.last_upload))
            connection.close()
        s.close()

    @staticmethod
    def _parse_input_as_integer(text):
        try:
            return int(text)
        except ValueError:
            return -1


def _siginit_handler(_, __):
    print "SPEEDTEST: SIGINT signal caught"
    sys.exit(0)


if __name__ == "__main__":
    print 'SpeedTest module: started.'
    device_line = sys.argv[1]
    conf_line = sys.argv[2]
    signal.signal(signal.SIGINT, _siginit_handler)

    device_info = c.get_device_entry_data(device_line)
    speedtest = SpeedTestModule(conf_line)
    speedtest.start_work(device_line[0], device_line[1])
