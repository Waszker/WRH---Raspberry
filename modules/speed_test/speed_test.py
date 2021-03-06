import re
import signal
import subprocess
import sys
import time

from utils.decorators import in_thread, log_exceptions
from utils.io import non_empty_input, non_empty_positive_numeric_input, log, Color, wrh_input
from wrh_engine import module_base as base_module

ninput = non_empty_input
iinput = non_empty_positive_numeric_input


class SpeedTestModule(base_module.Module):
    """
    This is Internet speed test module that checks Internet connection speed regularly.
    It's not recommended to add more than one speed test to WRH system.
    """
    TYPE_NAME = "INTERNET SPEED TEST"
    CONFIGURATION_LINE_PATTERN = "([0-9]{1,9});(.+?);([1-9][0-9]{0,9});([1-9][0-9]{0,9})$"

    def __init__(self, configuration_file_line=None):
        self.last_download, self.last_upload = "? Mbit/s", "? Mbit/s"
        base_module.Module.__init__(self, configuration_file_line)

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        return ["/usr/bin/python3.6", "-m", "modules.speed_test.speed_test"]

    def get_configuration_line(self):
        """
        Creates module configuration line.
        :return: Properly formatted configuration file line
        """
        values = (self.id, self.name, self.interval, self.port)
        return ('{};' * len(values))[:-1].format(*values)

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(self.CONFIGURATION_LINE_PATTERN, configuration_file_line)
        self.id = matches.group(1)
        self.name = matches.group(2)
        self.interval = int(matches.group(3))
        self.port = int(matches.group(4))

    def get_measurement(self):
        """
        Returns measurements taken by this module: two strings with download and upload speed values.
        """
        command = ["/usr/bin/python2.7", "modules/speed_test/speedtest-cli/speedtest_cli.py"]
        try:
            results = subprocess.check_output(command).decode('utf_8')
        except subprocess.CalledProcessError:
            results = ""
        results = results.replace('\n', '')
        log("The results are as follows: " + str(results))
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

    def run_registration_procedure(self, new_id):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, new_id)
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
        self.name = wrh_input(message='New module\'s name: ', allowed_empty=True) or self.name
        self.interval = iinput("Please input new interval (in minutes) for taking consecutive measurements: ",
                               allowed_empty=True) or self.interval
        self.port = iinput("Please input new port on which this module will be listening for commands: ",
                           allowed_empty=True) or self.port

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
            with open('modules/speed_test/html/repr.html', 'r') as f:
                html = f.read()
                self.html_repr = html.format(id=self.id, name=self.name, port=self.port)
        return self.html_repr

    def _react_to_connection(self, connection, _):
        connection.send(f'{self.last_download} {self.last_upload}'.encode('utf-8'))

    @in_thread
    @log_exceptions()
    def _measurement_thread(self):
        while self._should_end is False:
            self.last_download, self.last_upload = self.get_measurement()
            time.sleep(self.interval * 60)


if __name__ == "__main__":
    try:
        log('SpeedTest module: started.')
        conf_line = sys.argv[1]

        speedtest = SpeedTestModule(conf_line)
        speedtest.start_work()
    except Exception as e:
        log(e, Color.EXCEPTION)
