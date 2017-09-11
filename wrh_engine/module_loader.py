import os
from importlib import import_module

from wrh_engine.module_base import Module


class ModuleDynamicLoader:
    """
    Class taking care of dynamic modules loading.
    Every WRH module according to documentation should be provided in form of module folder with only three files:
    __init__.py file informing python interpreter that this is a module
    .wrh_module_backup magic, hidden file with module name as a content
    *.py file containing module implementation
    This class does not support any other module implementations and rely heavily on assumptions stated above.
    """
    MAGIC_FILENAME = ".wrh_module"

    def __init__(self, path):
        """
        Creates instance of DynamicLoader scanning provided path for modules.
        :param path: filesystem path name to scan
        :raise OSError: if the specified path does not exist
        """
        if not os.path.exists(path):
            raise OSError("Directory does not exist: %s" % path)

        self.path = path + (os.sep if path[-1] != os.sep else '')
        self.module_classes = self._get_module_classes()

    def get_module_classes(self):
        """
        Returns available modules classes.
        :return: dictionary containing module classes with key being class name and value class object
        """
        return self.module_classes

    @staticmethod
    def is_module_folder(path):
        """
        Checks if folder at certain path contains WRH-compliant module.
        CAUTION: This method checks only if module magic file exists, nothing more!
        :return: boolean response
        """
        magic_file = os.sep.join((path, ModuleDynamicLoader.MAGIC_FILENAME))
        return os.path.exists(magic_file) and os.path.isfile(magic_file)

    def _get_module_classes(self):
        module_classes, modules_info = {}, []
        modules_folders = [f for f in os.listdir(self.path) if ModuleDynamicLoader.is_module_folder(self.path + f)]
        [modules_info.extend(self._get_modules_info(self.path + folder + os.sep)) for folder in modules_folders]
        for (module_path, module_name) in modules_info:
            module = import_module(str(module_path + module_name).replace(os.sep, '.'))
            attributes = [getattr(module, attr) for attr in module.__dict__]
            classes_in_module = [attr for attr in attributes if isinstance(attr, type) and issubclass(attr, Module)]
            [module_classes.update({c.WRHID: c}) for c in classes_in_module]

        return module_classes

    @staticmethod
    def _get_modules_info(path):
        return [(path, f[:-3]) for f in os.listdir(path) if (len(f) > 3 and f[-3:] == '.py' and f != "__init__.py")]