#!/bin/python2

import sys
import sysv_ipc as IPC

print 'Got memory number ', sys.argv[1]
memory = IPC.attach(int(sys.argv[1]))
print 'In memory we got', str(memory.read())

