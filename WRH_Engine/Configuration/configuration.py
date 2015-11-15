import re

def check_configuration_file_sanity(file_handler) :
    # First line: DEVICE_ID ; TOKEN
    # Every other: TYPE ; ID ; GPIO ; NAME ; ADDR
    # Other lines are for module entries
    first_line_pattern = re.compile("([1-9][0-9]{0,9});(.+)$")
    next_lines_pattern = re.compile("(([1-9][0-9]{0,9};){3})(.+?);(.*)$")

    for i, line in enumerate(file_handler) :
        if(i == 0) :
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
