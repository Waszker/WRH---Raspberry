import threading

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

    return run_thread
