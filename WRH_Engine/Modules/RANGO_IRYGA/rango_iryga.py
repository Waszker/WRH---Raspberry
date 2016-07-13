from WRH_Engine.Module import module_base as base_module
from WRH_Engine.Configuration import configuration as c
import sys
import signal


class RangoIrygaModule(base_module.Module):
    """
    Rango Iryga module makes it easier for the user to interact with Rango Irygation system.
    """
    type_number = 7
    type_name = "RANGO IRYGA"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.type_number = RangoIrygaModule.type_number
        self.type_name = RangoIrygaModule.type_name

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed.
        :param self:
        :param configuration_line:
        :return:
        """
        # TODO: This function checks if its configuration file line is well formed and raises exception if not
        raise base_module.BadConfigurationException()

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        # TODO: Return command used to start module by OVERLORD program
        return ["/usr/bin/python2.7", "-m", "WRH_Engine.Modules.DUMMY.dummy_module"]

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

    def run_registration_procedure(self, device_id, device_token):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, device_id, device_token)
        # TODO: Run interactive procedure for module registration
        return base_module.Module.register_in_wrh(self, device_id, device_token)

    def edit(self, device_id, device_token):
        """
        Runs interactive procedure to edit module.
        Returns connection status and response.
        """
        # TODO: Run interactive procedure for module edition

    def start_work(self, device_id, device_token):
        """
        Starts working procedure.
        """
        # TODO: Start module working procedure

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        """
        # TODO: Return code to be used by Tornado


def _siginit_handler(_, __):
    # TODO: React to SIGINT
    print "DUMMY: SIGINT signal caught"
    sys.exit(0)


if __name__ == "__main__":
    print 'Dummy module: started.'
    device_line = sys.argv[1]
    conf_line = sys.argv[2]
    signal.signal(signal.SIGINT, _siginit_handler)

    device_info = c.get_device_entry_data(device_line)
    dummy = DummyModule(conf_line)
    dummy.start_work(device_line[0], device_line[1])
