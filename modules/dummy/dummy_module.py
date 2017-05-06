import signal
import sys
from wrh_engine import module_base as base_module


class DummyModule(base_module.Module):
    """
    This is dummy module which can be used as a starting point when writing own one.
    """
    # TODO: Module number must be unique across all modules in order to prevent failures during WRH system boot
    TYPE_NUMBER = None
    # TODO: Module name should be written in uppercase, will be displayed on Tornado web page screen and should
    # not be too long
    TYPE_NAME = "UNDEFINED"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.type_number = DummyModule.TYPE_NUMBER
        self.type_name = DummyModule.TYPE_NAME
        # WARNING: No need to initialize variables here because base module initialization
        # invokes variable initialization from configuration line

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed.
        :param configuration_line:
        :return:
        """
        # TODO: This function checks if its configuration file line is well formed
        return False

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        # TODO: Return command used to start module by OVERLORD program
        return ["/usr/bin/python2.7", "-m", "modules.dummy.dummy_module"]

    def get_configuration_line(self):
        """
        Creates module configuration line.
        :return: Properly formatted configuration file line
        """
        # TODO: Return configuration line to be saved in WRH configuration file
        return str(self.type_number) + ";" + str(self.id)

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        # TODO: Parse module's configuration line and initialize its variables

    def get_measurement(self):
        """
        Returns measurements taken by this module
        """
        # TODO: Returns module's measurement

    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """
        # TODO: Create informative description
        return "Dummy module created for educational purposes"

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
        # TODO: Run interactive procedure for module registration

    def edit(self, device_id, device_token):
        """
        Runs interactive procedure to edit module.
        Returns connection status and response.
        """
        # TODO: Run interactive procedure for module edition

    def start_work(self):
        """
        Starts working procedure.
        """
        # TODO: Start module working procedure, can run base module's implementation too!

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        """
        # TODO: Return code to be used by Tornado

    def _sigint_handler(self, *_):
        print "DUMMY: SIGINT signal caught"
        # TODO: React to received sigint signal. The base module has already implemented sigint handler that is
        # automatically installed if running start_work() base module's procedure


if __name__ == "__main__":
    print 'Dummy module: started.'
    conf_line = sys.argv[1]

    dummy = DummyModule(conf_line)
    dummy.start_work()
