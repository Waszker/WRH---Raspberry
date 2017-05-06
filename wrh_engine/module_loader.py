import os
from importlib import import_module


class ModuleDynamicLoader:
    """
    Class taking care of dynamic modules loading.
    Every WRH module according to documentation should be provided in form of module folder with only three files:
    __init__.py file informing python interpreter that this is a module
    .wrh_module_backup magic, hidden file with module name as a content
    *.py file containing module implementation
    This class does not support any other module implementations and rely heavily on assumptions stated above.
    """
    magic_filename = ".wrh_module"

    def __init__(self, path):
        """
        Creates instance of DynamicLoader scanning provided path for modules.
        :param path: filesystem path name to scan
        :raise OSError: if the specified path does not exist
        """
        if not os.path.exists(path):
            raise OSError("Directory does not exist: %s" % path)

        self.path = path + (os.sep if path[-1] != os.sep else '')
        self.modules_info = self._scan_modules()
        self.module_classes = self._get_module_classes()

    def get_modules_info(self):
        """
        Returns available modules information.
        :return: dictionary with module name as a key and path to it as a value
        """
        return self.modules_info

    def get_module_classes(self):
        """
        Returns available modules classes.
        :return: dictionary containing module classes with key being type_number and value class name
        """
        return self.module_classes

    @staticmethod
    def is_module_folder(path):
        """
        Checks if folder at certain path contains WRH-compliant module.
        CAUTION: This method checks only if module magic file exists, nothing more!
        :return: boolean response
        """
        magic_file = os.sep.join((path, ModuleDynamicLoader.magic_filename))
        return os.path.exists(magic_file) and os.path.isfile(magic_file)

    def _scan_modules(self):
        modules = {}
        module_folders = [f for f in os.listdir(self.path) if ModuleDynamicLoader.is_module_folder(self.path + f)]
        [ModuleDynamicLoader._update_module_information(self.path + folder + os.sep, modules) for folder in module_folders]

        return modules

    @staticmethod
    def _update_module_information(path, modules_dictionary):
        class_name, module_name = None, None
        with open(path + ModuleDynamicLoader.magic_filename, 'r') as f:
            class_name = f.readline()
        for f in os.listdir(path):
            # Ignore anything that isn't a .py file
            if len(f) > 3 and f[-3:] == '.py' and f != "__init__.py":
                module_name = f[:-3]
                break
        if class_name is not None and module_name is not None:
            modules_dictionary[module_name] = (path, class_name)

    def _get_module_classes(self):
        module_classes = {}
        for module_name, (module_path, class_name) in self.modules_info.iteritems():
            module = import_module(str(module_path + module_name).replace('/', '.'))
            m_class = getattr(module, class_name)
            module_classes[m_class.TYPE_NUMBER] = m_class

        return module_classes
