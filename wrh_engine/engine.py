import sys
import os
import signal
from utils.io import *
from wrh_engine.configuration import ConfigurationParser, BadConfigurationException, UnknownModuleException
from wrh_engine.module_loader import ModuleDynamicLoader
from wrh_engine.overlord import Overlord

ninput = non_empty_input


class WRHEngine:
    """
    Main core of WRH system.
    There should be only one instance of WRHEngine running in the system at a time (this is not checked!).
    """
    _modules_folder = 'modules/'

    def __init__(self, argv):
        """
        Initializes engine with arguments passed during process startup.
        :param argv: arguments array
        :raises FileNotFoundException:
        :raises UnknownModuleException:
        :raises BadConfigurationException:
        """
        self.should_end = False
        self.args = argv
        log("WRH System main engine starting", (Color.BOLD, Color.UNDERLINE))
        log("Scanning for available modules")
        loader = ModuleDynamicLoader(self._modules_folder)
        self.modules_info = loader.get_modules_info()
        self.module_classes = loader.get_module_classes()
        log("Found modules: ")
        [log('*' + str(module_name), Color.BLUE) for module_name in self.modules_info.keys()]
        self.overlord_instances = []

    def start(self):
        """
        Starts main engine work.
        """
        self._check_configuration()
        # TODO: Add better start options checking
        if len(self.args) > 1 and self.args[1] == "--start-work":
            self._run_system()
        else:
            self._show_installed_modules()
            self._show_options()

    def _show_options(self):
        actions = {'1': self._edit_module,
                   '2': self._add_new_module,
                   '3': self._remove_module,
                   '4': self._run_system}
        while True:
            self.should_end = False
            log('\n[1] Edit module\n[2] Add new module\n[3] Delete module\n[4] Start modules\n[5] Exit')
            choice = ninput('> ')
            if choice == '5': break
            if choice not in actions: continue
            actions[choice]()

    def _edit_module(self):
        log('\nChoose which module to edit')
        [log('%d) %s named %s' % (i, module.type_name, module.name)) for i, module in enumerate(self.installed_modules)]
        choice = ninput('> ')
        try:
            self.installed_modules[int(choice)].edit()
            self.configuration_parser.save_configuration(self.installed_modules)
            log("Success!", Color.GREEN)
        except (KeyError, ValueError, IndexError):
            pass

    def _add_new_module(self):
        log("\nChose which module to add")
        [log('%d) %s' % (number, m_class.type_name)) for number, m_class in self.module_classes.iteritems()]

        choice = ninput('> ')
        try:
            module = self.module_classes[int(choice)]()
            module.run_registration_procedure(self.configuration_parser.get_new_module_id())
            self.installed_modules.append(module)
            self.configuration_parser.save_configuration(self.installed_modules)
            log("Success!", Color.GREEN)
        except (KeyError, ValueError, IndexError):
            pass

    def _remove_module(self):
        log('\nChoose which module to remove')
        [log('%d) %s named %s' % (i, module.type_name, module.name)) for i, module in enumerate(self.installed_modules)]
        choice = ninput('> ')
        try:
            del self.installed_modules[int(choice)]
            self.configuration_parser.save_configuration(self.installed_modules)
            log("Success!", Color.GREEN)
        except (KeyError, ValueError, IndexError):
            pass

    def _show_installed_modules(self):
        self.installed_modules = self.configuration_parser.get_installed_modules()
        log("\nDetected installed modules:")
        [log('%d) %s named %s' % (i, module.type_name, module.name), Color.HEADER)
         for i, module in enumerate(self.installed_modules)]

    def _check_configuration(self):
        try:
            self.configuration_parser = ConfigurationParser(os.getcwd(), self.module_classes)
        except (UnknownModuleException, BadConfigurationException) as e:
            log(str(e), Color.FAIL)
            sys.exit(1)

    def _run_system(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGCHLD, self._signal_handler)

        # If there should be more overlord instances - put them here
        overlord = Overlord(self.configuration_parser)
        overlord.start_modules()
        self.overlord_instances.append(overlord)

        # Run infinitely until SIGINT is caught
        while self.should_end is False:
            signal.pause()
        self.overlord_instances = []
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def _signal_handler(self, sig, _):
        if sig == signal.SIGINT:
            self.should_end = True
            signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        [overlord.handle_signal(sig) for overlord in self.overlord_instances]
