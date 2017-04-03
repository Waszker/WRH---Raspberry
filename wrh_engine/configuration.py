import os
from wrh_exceptions import *
from utils.io import *


class ConfigurationParser:
    """
    Class responsible for maintaining and parsing configuration file.
    Configuration file should store only one line for each installed module.
    Each line should start with unique module number and its unique id - that's the only defined configuration option!
    """
    configuration_filename = ".wrh.config"

    def __init__(self, configuration_file_path, module_classes):
        """
        Creates configuration parses object that parses configuration file in the provided path.
        :param configuration_file_path: filesystem path in which configuration file is present
        :param module_classes: list of module instances, one for each detected module in the system
        :raises UnknownModuleException: configuration file contains unknown module info
        :raises BadConfigurationException: configuration file is invalid
        """
        self.configuration_file = configuration_file_path + os.sep + self.configuration_filename
        if not os.path.isfile(self.configuration_file):
            log("No configuration file found, creating new one", Color.WARNING)
            self.save_configuration([])
        self.module_classes = module_classes
        self._check_file_sanity()

    def get_installed_modules(self):
        """
        This function does not check if configuration file is sane
        Please do check it before invoking!
        Returns instances of installed modules ready to be run as a separate process.
        :return: list of modules instances
        """
        with open(self.configuration_file, 'r') as f:
            instances = [self.module_classes[ConfigurationParser._get_module_type_from_line(line)](line) for line in f]
        return instances

    def save_configuration(self, installed_modules):
        """
        Overwrites configuration file and saves installed modules' information to it.
        :param installed_modules: list containing instances of installed modules
        """
        with open(self.configuration_file, 'w+') as f:
            f.write('\n'.join([module.get_configuration_line() for module in installed_modules]))

    def get_new_module_id(self):
        """
        Returns unique module id.
        """
        with open(self.configuration_file, 'r') as f:
            ids = [ConfigurationParser._get_module_id_from_line(line) for line in f]
        return (max(ids) + 1) if len(ids) > 0 else 0

    def _check_file_sanity(self):
        try:
            with open(self.configuration_file, 'r') as f:
                sanity = [self.module_classes[ConfigurationParser._get_module_type_from_line(line)]
                              .is_configuration_line_sane(line) for line in f]
        except KeyError as e:
            raise UnknownModuleException("Unknown module with id=%s" % str(e))

        if not all(sanity):
            raise BadConfigurationException(
                "Bad configuration line(s): " + ', '.join(([str(i) for i, b in enumerate(sanity) if b is False])))

    @staticmethod
    def _get_module_type_from_line(line):
        return int(line.split(";")[0])

    @staticmethod
    def _get_module_id_from_line(line):
        return int(line.split(";")[1])
