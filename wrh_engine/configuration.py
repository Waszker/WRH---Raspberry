from utils.decorators import with_open
from utils.io import *
from wrh_engine.constants import WRH_CONFIGURATION_FILENAME
from wrh_exceptions import *


class ConfigurationParser:
    """
    Class responsible for maintaining and parsing configuration file.
    Configuration file should store only one line for each installed module.
    Each line should start with unique module number and its unique id - that's the only defined configuration option!
    """

    def __init__(self, module_classes):
        """
        Creates configuration parses object that parses configuration file in the provided path.
        :param configuration_file_path: filesystem path in which configuration file is present
        :param module_classes: dictionary of module classes, with keys being the class names and values class objects
        :type configuration_file_path: str
        :type module_classes: dict
        :raises UnknownModuleException: configuration file contains unknown module info
        :raises BadConfigurationException: configuration file is invalid
        """
        try:
            open(WRH_CONFIGURATION_FILENAME).close()
        except IOError:
            log("No configuration file found, creating new one", Color.WARNING)
            self.save_configuration([])
        self.module_classes = module_classes
        self._check_file_sanity()

    @with_open(WRH_CONFIGURATION_FILENAME, 'r')
    def get_installed_modules(self, _file_=None):
        """
        This function does not check if configuration file is sane
        Please do check it before invoking!
        Returns instances of installed modules ready to be run as a separate process.
        :return: list of modules instances
        :rtype: list
        :param _file_: opened configuration file object, passed by decorator
        :type _file_: file
        """
        instances = [self.module_classes[self._get_module_class_name_from_line(line)](self._cut_module_name(line))
                     for line in _file_]
        return instances

    @with_open(WRH_CONFIGURATION_FILENAME, 'w+')
    def save_configuration(self, installed_modules, _file_=None):
        """
        Overwrites configuration file and saves installed modules' information to it.
        :param installed_modules: list containing instances of installed modules
        :type installed_modules: list
        :param _file_: opened configuration file object, passed by decorator
        :type _file_: file
        """
        _file_.write('\n'.join([module.WRHID + ';' + module.get_configuration_line() for module in installed_modules]))

    @with_open(WRH_CONFIGURATION_FILENAME, 'r')
    def get_new_module_id(self, _file_=None):
        """
        Returns unique module id.
        :param _file_: opened configuration file object, passed by decorator
        :type _file_: file
        """
        ids = [ConfigurationParser._get_module_id_from_line(line) for line in _file_]
        return (max(ids) + 1) if len(ids) > 0 else 0

    @with_open(WRH_CONFIGURATION_FILENAME, 'r')
    def _check_file_sanity(self, _file_=None):
        try:
            sanity = [self.module_classes[self._get_module_class_name_from_line(line)]
                          .is_configuration_line_sane(self._cut_module_name(line)) for line in _file_]
        except KeyError as e:
            raise UnknownModuleException("Unknown module %s" % str(e))

        if not all(sanity):
            raise BadConfigurationException(
                "Bad configuration line(s): " + ', '.join(([str(i) for i, b in enumerate(sanity) if b is False])))

    @staticmethod
    def _cut_module_name(line):
        return ';'.join(line.split(";")[1:])

    @staticmethod
    def _get_module_class_name_from_line(line):
        return line.split(";")[0]

    @staticmethod
    def _get_module_id_from_line(line):
        return int(line.split(";")[1])
