#!/usr/bin/python2.7
import sys
from wrh_engine.engine import WRHEngine
from wrh_engine.configuration import *

if __name__ == "__main__":
    if os.getuid() == 0:
        log("Cowardly refusing to run with root privileges!", Color.FAIL)
        sys.exit(0)
    else:
        engine = WRHEngine(sys.argv)
        engine.start()

    log("WRH system shutting down", Color.GREEN)
    sys.exit(0)
