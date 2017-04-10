import time
import socket as s
from io import log, Color

"""
Set of functions to make socket handling a lot easier.
"""


def wait_bind_socket(socket, host, port, sleep, retries=-1, predicate=lambda: True, error_message=None):
    """
    Tries to bind socket for specified host and port.
    In case of failure the procedure is retried until predicate value is False or provided
    number of retries is achieved. After each failure the procedure sleeps for a sleep number
    of seconds.
    """
    while predicate() and retries != 0:
        try:
            socket.bind((str(host), int(port)))
            break
        except s.error as message:
            if error_message is not None:
                log(str(error_message) + str(message), Color.FAIL)
            time.sleep(sleep)
            retries = max(-1, retries - 1)
    return predicate() and retries != 0


def await_connection(socket, callback, predicate=lambda: True):
    """
    Waits for connection on provided socket. Each connection results in firing provided
    callback function with the connection and client address as arguments.
    """
    while predicate():
        try:
            connection, address = socket.accept()
            callback(connection, address)
            connection.close()
        except s.error:
            pass
