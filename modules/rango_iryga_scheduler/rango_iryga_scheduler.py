import re
import sys
import signal
from wrh_engine import module_base as base_module
from utils.sockets import send_message
from utils.io import non_empty_positive_numeric_input as iinput


class RangoScenario:
    """
    Class for private use only that represents Rango Iryga scenario to run at a certain time.
    """

    def __init__(self, request):
        """
        Creates scenario from the provided information.
        :param request: line containing information about scenario, sent after user creates new request
        """
        self.is_active = False
        self.start_time = None
        self.active_on_days = []
        self.active_lines = []
        self.line_activation_times = {}
        self.line_activation_repeats = {}

    def get_html_information_string(self):
        """
        Returns HTML formatted string to display one the tornado web page.
        :return: HTML formatted string
        """
        pass

    def time_changed(self, date, rango_port):
        """
        Reacts to time change and runs scenario (self) if needed.
        :param date: current date (day of the month, etc.)
        :param rango_port: port of the Rango Iryga system
        """
        if self._should_activate(date):
            # Log action to file?
            self._activate(rango_port)

    def _should_activate(self, date):
        return (date.weekday() in self.active_on_days) and \
               (date.hour == self.start_time.hour) and \
               (date.minute == self.start_time.minute)

    def _activate(self, rango_port):
        state = "ON"
        for relay, time, repeats in zip(self.active_lines, self.line_activation_times, self.line_activation_repeats):
            message = "%s,%s,%s,%s" % tuple(map(str, (state, relay, time, repeats)))
            send_message("127.0.0.1", rango_port, message)


class RangoIrygaSchedulerModule(base_module.Module):
    """
    Rango Iryga Scheduler is a module responsible for automatically running watering scenarios.
    """
    type_number = 8
    type_name = "RANGO IRYGA SCHEDULER"
    configuration_line_pattern = str(type_number) + ";([0-9]{1,9});(.+?);([1-9][0-9]{0,9});([1-9][0-9]{0,9})$"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.type_number = RangoIrygaSchedulerModule.type_number
        self.type_name = RangoIrygaSchedulerModule.type_name
        self.scenarios = {i: [] for i in xrange(0, 7)}

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
        checker = re.compile(RangoIrygaSchedulerModule.configuration_line_pattern)
        return checker.match(configuration_line) is not None

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        return ["/usr/bin/python2.7", "-m", "modules.rango_iryga_scheduler.rango_iryga_scheduler"]

    def get_configuration_line(self):
        """
        Creates module configuration line.
        :return: Properly formatted configuration file line
        """
        return "%i;%i;%s;%i;%i" % (self.type_number, self.id, self.name, self.port, self.rango_port)

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(RangoIrygaSchedulerModule.configuration_line_pattern, configuration_file_line)
        self.id = int(matches.group(1))
        self.name = str(matches.group(2))
        self.port = int(matches.group(3))
        self.rango_port = int(matches.group(4))

    def get_measurement(self):
        """
        Returns measurements taken by this module
        """
        pass

    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """
        return "Rango Iryga Scheduler module used to maintain scenarios for the Rango Iryga irrigation system " \
               "for garden."

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
        self.port = iinput("Please input port on which this module will be listening for commands: ")
        self.rango_port = iinput("Please input port number of Rango Iryga installed in this system: ")

    def edit(self, device_id, device_token):
        """
        Runs interactive procedure to edit module.
        Returns connection status and response.
        """
        print 'Provide new module information (leave fields blank if you don\'t want to change)'
        print 'Please note that changes other than name will always succeed'
        print 'Name changing requires active Internet connection'
        new_name = raw_input('New module\'s name: ')
        new_port = raw_input("Please input new port on which this module will be listening for commands: ")
        new_rango_port = raw_input("Please input new port number of Rango Iryga installed in this system: ")

        if new_rango_port: self.rango_port = new_rango_port
        if new_port: self.port = new_port
        if new_name: self.name = new_name

    def start_work(self):
        """
        Starts working procedure.
        """
        base_module.Module.start_work(self)
        while self._should_end is False:
            signal.pause()

    def get_html_representation(self, _):
        """
        Returns html code to include in website.
        """
        return '<div class="card-panel"></div>'

    def _react_to_connection(self, connection, _):
        pass


if __name__ == "__main__":
    print 'Rango Iryga module: started.'
    conf_line = sys.argv[1]

    rango_iryga_scheduler = RangoIrygaSchedulerModule(conf_line)
    rango_iryga_scheduler.start_work()
