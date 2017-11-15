import signal
import time

from utils.io import log, Color

"""
Set of functions to deal with processes in the operating system.
"""


def does_process_exist(process):
    """
    Checks if certain process exists in the system.
    :param process: process to be checked
    :return: boolean
    """
    return process.poll() is None


def print_process_errors(process):
    """
    Awaits process error information on the STDERR stream.
    Process should be piped!
    This method does not return until process finishes!
    :param process: process to be polled
    """
    while does_process_exist(process):
        _, err = process.communicate()
        log(err, Color.FAIL)


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
        while does_process_exist(process) and timeout > 0:
            time.sleep(1)
            timeout -= 1
        if does_process_exist(process):
            if not suppress_messages:
                log('Process ' + str(process.pid) + " not responding. Sending SIGTERM.", Color.WARNING)
            process.terminate()
    except OSError:
        pass
