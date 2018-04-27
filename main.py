#!/usr/bin/python3.6
import os
import sys

from utils.io import log, Color
from wrh_engine.engine import WRHEngine

if __name__ == "__main__":
    try:
        if os.getuid() == 0:
            log('Cowardly refusing to run with root privileges!', Color.FAIL)
            sys.exit(0)
        else:
            engine = WRHEngine(sys.argv[1:])
            engine.start()

        log('WRH system shutting down', Color.GREEN)
        sys.exit(0)
    except Exception as e:
        log(e, Color.EXCEPTION)
        raise
