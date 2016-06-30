############################################################
# Configuration library takes care of checking
# and parsing configuration file.
# It should be used in a situation where module object
# from configuration file line is needed.
#############################################################
import re
from ..module.module import Module

def check_configuration_file_sanity(file_handler) :
    """
    Checks if provided configuration file is well formatted
    and can be parsed.
    First line: DEVICE_ID ; TOKEN
    Every other: TYPE ; ID ; GPIO ; NAME ; ADDR
    Other lines are for module entries
    """
    first_line_pattern = re.compile("([1-9][0-9]{0,9});(.+)$")
    next_lines_pattern = re.compile("(([1-9][0-9]{0,9};){2})(.*?);(.+?);(.*)$")
    does_match = False

    for i, line in enumerate(file_handler) :
        if i == 0 :
            does_match = first_line_pattern.match(line)
            if not does_match :
                print 'First line of config file is corrupted!'
                break
        else :
            does_match = next_lines_pattern.match(line)
            if not does_match :
                print 'Line ' + line + 'seems to be corrupted!'
                break

    return does_match


def get_device_entry_data(line) :
    """
    This function does not check if configuration file is sane
    Please do check it before invoking!
    Returns device information (id and token)
    from the provided first configuration file line.
    """
    matches = re.search("([1-9][0-9]{0,9});(.+)$", line)
    return (matches.group(1), matches.group(2))


def get_module_entry_data(line) :
    """
    This function does not check if configuration file is sane
    Please do check it before invoking!
    Parses configuration file line as a module object
    and returns it.
    """
    m = re.search("([1-9][0-9]{0,9});([1-9][0-9]{0,9});(.*?);(.+?);(.*)$", line)
    return Module(m.group(2), m.group(1), m.group(3), m.group(4), m.group(5))


def parse_configuration_file(file_handler) :
    """
    This function does not check if configuration file is sane
    Please do check it before invoking!
    Returns tuple containing tuple of device id and device token
    and list of module
    """
    (device_id, device_token) = get_device_entry_data(file_handler.readline())

    modules_list = []
    for i, line in enumerate(file_handler) :
        modules_list.append(get_module_entry_data(line))

    return ((device_id, device_token), modules_list)


def update_configuration_file(file_handler, system_info, modules):
    """
    Rewrites configuration file with newer data.
    """
    file_handler.write(str(system_info[0]) + ';' + system_info[1] + '\n')
    for module in modules:
        add_new_module(file_handler, module)


def add_new_module(file_handler, module) :
    """
    Appends module configuration line to provided configuration file.
    """
    file_handler.write(str(module.type) + ';' + str(module.id) + ';'
                       + str(module.gpio) + ';' + str(module.name) +
                       ';' + str(module.address) + '\n')

