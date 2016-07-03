############################################################
# Configuration library takes care of checking
# and parsing configuration file.
# It should be used in a situation where module object
# from configuration file line is needed.
#############################################################
import re
from ..Module.module_base import BadConfigurationException


def check_configuration_file_sanity(file_handler, modules):
    """
    Checks if provided configuration file is well formatted
    and can be parsed.
    First line: DEVICE_ID ; TOKEN
    Every other line is checked by dynamically loaded modules
    Other lines are for module entries
    """
    first_line_pattern = re.compile("([1-9][0-9]{0,9});(.+)$")
    does_match = False

    for i, line in enumerate(file_handler):
        if i == 0:
            does_match = first_line_pattern.match(line)
            if not does_match:
                print 'First line of config file is corrupted!'
                break
        else:
            module = modules[_get_module_number_from_line(line)]
            try:
                if module is None or not module.is_configuration_line_sane(line):
                    print "Unknown module with number " + str(_get_module_number_from_line(line))
                    does_match = False
                    break
            except BadConfigurationException:
                print 'Line ' + line + 'seems to be corrupted!'
                does_match = False
                break

    return does_match


def get_device_entry_data(line):
    """
    This function does not check if configuration file is sane
    Please do check it before invoking!
    Returns device information (id and token)
    from the provided first configuration file line.
    """
    matches = re.search("([1-9][0-9]{0,9});(.+)$", line)
    return matches.group(1), matches.group(2)


def parse_configuration_file(file_handler, modules_classes):
    """
    This function does not check if configuration file is sane
    Please do check it before invoking!
    Returns tuple containing tuple of device id and device token
    and list of modules
    """
    device_info = get_device_entry_data(file_handler.readline())

    modules_list = []
    for i, line in enumerate(file_handler):
        module_class = modules_classes[_get_module_number_from_line(line)]
        modules_list.append(module_class(line))

    return device_info, modules_list


def update_configuration_file(file_handler, system_info, modules):
    """
    Rewrites configuration file with newer data.
    """
    file_handler.write(str(system_info[0]) + ';' + system_info[1] + '\n')
    for module in modules:
        add_new_module(file_handler, module)


def add_new_module(file_handler, module):
    """
    Appends module configuration line to provided configuration file.
    """
    file_handler.write(module.get_configuration_line() + '\n')


def _get_module_number_from_line(line):
    return int(line.split(";")[0])
