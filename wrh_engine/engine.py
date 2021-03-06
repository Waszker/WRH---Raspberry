import getopt
import os
import signal
import sys

from utils.io import log, Color, non_empty_input
from wrh_engine.configuration import ConfigurationParser, BadConfigurationException, UnknownModuleException
from wrh_engine.constants import WRH_MODULES_FOLDER
from wrh_engine.module_loader import ModuleDynamicLoader
from wrh_engine.overlord import Overlord

ninput = non_empty_input


class WRHEngine:
    """
    Main core of WRH system.
    There should be only one instance of WRHEngine running in the system at a time (this is not checked!).
    """

    def __init__(self, argv):
        """
        Initializes engine with arguments passed during process startup.
        :param argv: arguments array
        :raises FileNotFoundException:
        :raises UnknownModuleException:
        :raises BadConfigurationException:
        """
        self.__parse_args(argv)
        self.should_end = False
        log('WRH System main engine starting', Color.BOLD, Color.UNDERLINE)
        log('Scanning for available modules')
        loader = ModuleDynamicLoader(WRH_MODULES_FOLDER)
        self.module_classes = loader.get_module_classes()
        log('Found modules: ')
        [log(f'*{module_name}', Color.BLUE) for module_name in self.module_classes.keys()]
        self.overlord_instances = []

    def start(self):
        """
        Starts main engine work.
        """
        self._check_configuration()
        if not self.run_interactive:
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
        [log('%d) %s named %s' % (i, module.TYPE_NAME, module.name)) for i, module in enumerate(self.installed_modules)]
        choice = ninput('> ')
        try:
            self.installed_modules[int(choice)].edit()
            self.configuration_parser.save_configuration(self.installed_modules)
            log("Success!", Color.GREEN)
        except (KeyError, ValueError, IndexError):
            pass

    def _add_new_module(self):
        log("\nChose which module to add")
        module_classes = self.module_classes.values()
        [log(f'{i}) {m_class.TYPE_NAME}') for i, m_class in enumerate(module_classes)]

        try:
            module = module_classes[int(ninput('> '))]()
            module.run_registration_procedure(self.configuration_parser.get_new_module_id())
            self.installed_modules.append(module)
            self.configuration_parser.save_configuration(self.installed_modules)
            log('Success!', Color.GREEN)
        except (KeyError, ValueError, IndexError):
            pass

    def _remove_module(self):
        log('\nChoose which module to remove')
        [log(f'{i}) {module.TYPE_NAME} named {module.name}') for i, module in enumerate(self.installed_modules)]
        choice = ninput('> ')
        try:
            del self.installed_modules[int(choice)]
            self.configuration_parser.save_configuration(self.installed_modules)
            log('Success!', Color.GREEN)
        except (KeyError, ValueError, IndexError):
            pass

    def _show_installed_modules(self):
        self.installed_modules = self.configuration_parser.get_installed_modules()
        log('\nDetected installed modules:')
        [log(f'{i}) {module.TYPE_NAME} named {module.name}', Color.HEADER) for i, module in
         enumerate(self.installed_modules)]

    def _check_configuration(self):
        try:
            self.configuration_parser = ConfigurationParser(self.module_classes)
        except (UnknownModuleException, BadConfigurationException) as e:
            log(str(e), Color.EXCEPTION)
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

    def __parse_args(self, argv):
        try:
            opts, _ = getopt.getopt(argv, 'p:s', ['path=', 'start-work'])
            self.run_interactive = not (('-s', '') in opts or ('--start-work', '') in opts)
            opts_dict = {key: args for (key, args) in opts}
            os.chdir(opts_dict.get('-p' if '-p' in opts_dict else '--path', os.getcwd()))
        except getopt.GetoptError:
            pass
