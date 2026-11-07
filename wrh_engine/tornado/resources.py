import datetime
import subprocess as s

from utils.system_info import get_uptime, get_cpu_temp
from wrh_engine.constants import WRH_MODULES_FOLDER
from wrh_engine.engine import ConfigurationParser
from wrh_engine.module_loader import ModuleDynamicLoader


def get_installed_modules_info():
    loader = ModuleDynamicLoader(WRH_MODULES_FOLDER)
    modules_classes = loader.get_module_classes()
    parser = ConfigurationParser(modules_classes)
    modules = parser.get_installed_modules()
    # Modules can opt out of the web UI with WEB_VISIBLE = False (e.g. background uploaders)
    unique_classes = [c for c in {modules_classes[m.WRHID] for m in modules} if getattr(c, 'WEB_VISIBLE', True)]
    return sorted(unique_classes, key=lambda x: x.WRHID), modules


def get_system_stats():
    now = datetime.datetime.now()
    return {
        'date': '%02i-%02i-%04i' % (now.day, now.month, now.year),
        'time': '%02i:%02i' % (now.hour, now.minute),
        'uptime': get_uptime(),
        'cpu_temp': round(get_cpu_temp(), 1),
    }


def restart():
    s.call("sudo reboot", shell=True)
