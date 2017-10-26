import os
import threading

from utils.io import wrh_open

"""
Set of decorators that can be useful.
"""


def in_thread(method):
    """
    Runs decorated method in a separate, daemon thread.
    :param method:
    :return:
    """

    def run_thread(*args, **kwargs):
        thread = threading.Thread(target=method, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread

    return run_thread


def with_open(filename, mode):
    """
    Runs provided method with additional named parameter being the requested, opened file object,
    located in wrh operating path.
    The additional parameter is available under '_file_' name.
    If the requested file does not exist, method is not invoked.
    :param filename: name of the file in the system (wrh operation path is added automatically)
    :type filename: str
    :param mode: mode in which file should be opened
    :type mode: str
    """

    def inner(method):

        def open_and_run(*args, **kwargs):
            try:
                with wrh_open(filename, mode) as f:
                    kwargs['_file_'] = f
                    return method(*args, **kwargs)
            except IOError:
                pass

        return open_and_run

    return inner
