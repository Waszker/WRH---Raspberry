#!/usr/bin/python2.7
import os
import sys

from wrh_engine.configuration import *
from wrh_engine.engine import WRHEngine

if __name__ == "__main__":
    if os.getuid() == 0:
        log("Cowardly refusing to run with root privileges!", Color.FAIL)
        sys.exit(0)
    else:
        engine = WRHEngine(sys.argv[1:])
        engine.start()

    log("WRH system shutting down", Color.GREEN)
    sys.exit(0)
