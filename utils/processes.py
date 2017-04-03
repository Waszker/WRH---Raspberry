import time
import signal
from utils.io import log, Color

"""
Set of functions to deal with processes in the operating system.
"""


def end_process(process, timeout, suppress_messages=False):
    """
    Tries to end process by sending SIGINT signal. The request is repeated until process ends or timeout is reached.
    It the timeout is reached SIGKILL is sent instead.
    :param process: process to stop
    :param timeout: (in seconds) timeout after which SIGKILL process
    :param suppress_messages: should messages be printed to STDOUT
    """
    try:
        if not suppress_messages: log('Sending SIGINT to process: ' + str(process.pid))
        process.send_signal(signal.SIGINT)
        while process.poll() is None and timeout > 0:
            time.sleep(1)
            timeout -= 1
        if process.poll() is None:
            if not suppress_messages:
                log('Process ' + str(process.pid) + " not responding. Sending SIGTERM.", Color.WARNING)
            process.terminate()
    except OSError:
        pass
