import re

def check_configuration_file_sanity(file_handler) :
    # First line: DEVICE_ID ; TOKEN
    # Every other: TYPE ; ID ; GPIO ; NAME ; ADDR
    # Other lines are for module entries
    first_line_pattern = re.compile("([1-9][0-9]{0,9});(.+)$")
    next_lines_pattern = re.compile("(([1-9][0-9]{0,9};){3})(.+?);(.*)$")
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

def _get_first_line_data(line) :
    matches = re.search("([1-9][0-9]{0,9});(.+)$", line)
    return (matches.group(1), matches.group(2))

def _get_module_entry_data(line) :
    m = re.search("([1-9][0-9]{0,9});([1-9][0-9]{0,9});([1-9][0-9]{0,9});(.+?);(.*)$", line)
    return (m.group(1), m.group(2), m.group(3), m.group(4), m.group(5))

# This function does not check if configuration file is sane
# Please do check it before invoking!
# Returns tuple containing tuple of device id and device token
# and list of modules
def parse_configuration_file(file_handler) :
    (device_id, device_token) = _get_first_line_data(file_handler.readline())

    modules_list = []
    for i, line in enumerate(file_handler) :
        modules_list.append(_get_module_entry_data(line))

    return ((device_id, device_token), modules_list)

def get_module_type_string(module) :
    type = int(module[0])
    type_string = "UNKNOWN"
    if type == 1 :
        type_string = "DHT"
    elif type == 2 :
        type_string = "Camera"
    elif type == 3 :
        type_string = "Motion"
    elif type == 4 :
        type_string = "Wi-Fi Socket"

    return type_string

def print_module_information(module) :
    type = int(module[0])
    if type == 1 or type == 3 :
        print (module[3] + ' is module of type ' + get_module_type_string(module)),
        print (' connected to gpio ' + str(module[2]))
    else:
        print (module[3] + ' is module of type ' + get_module_type_string(module)),
        print (' available at address ' + module[4])
