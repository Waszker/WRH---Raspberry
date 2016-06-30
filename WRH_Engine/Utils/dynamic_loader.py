import os
import sys


def scan_and_returns_modules(path):
    """
    Scans provided directory and updates list of found modules.
    :param path: path to scan for modules
    :return: dictionary containing module name as a key and tuple with path and class name as a value
    """
    found_modules = {}
    special_module_file = ".wrh_module"

    if not os.path.exists(path):
        raise OSError("Directory does not exist: %s" % path)

    sys.path.append(path)

    # Scan directory for potential module directories
    for f in os.listdir(path):
        tmp_path = path + str(f) + "/"
        # Each WRH module directory has to include special file .wrh_module with class name
        if os.path.exists(tmp_path + special_module_file) and os.path.isfile(tmp_path + special_module_file):
            for f2 in os.listdir(tmp_path):
                # Ignore anything that isn't a .py file
                if len(f2) > 3 and f2[-3:] == '.py' and f2 != "__init__.py":
                    module_name = f2[:-3]
                    with open(tmp_path + special_module_file, "r") as file:
                        class_name = file.readline()
                    found_modules[module_name] = (tmp_path, class_name)

    return found_modules
