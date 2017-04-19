import time
import socket as s
from contextlib import contextmanager
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


@contextmanager
def open_connection(*args, **kwargs):
    """
    Context manager method for opening TCP connections.
    """
    try:
        connection = s.create_connection(*args, **kwargs)
        yield connection
        connection.close()
    except s.error:
        pass


def receive_message(host, port, buffer_size=1024, message=None):
    """
    Receives message with the maximum size of buffer_size from host on provided port.
    If the optional parameter message is not None then this message is sent prior to receiving procedure.
    This method does not raise exceptions if anything goes wrong.
    :param host: host to connect to
    :param port: port to connect to
    :param buffer_size: size of the buffer for receiving the message
    :param message: message to send prior to receiving
    :return: received message, None if an error occurred or no message was received
    """
    data = None
    with open_connection((host, port)) as connection:
        if message is not None:
            connection.send(message)
        data = connection.recv(buffer_size)
    return data


def send_message(host, port, message):
    """
    Sends message to provided host on certain port.
    This method does not raise exceptions if anything goes wrong.
    :param host: host to connect to
    :param port: port to connect to
    :param message: message to send
    """
    with open_connection((host, port)) as connection:
        connection.send(message)
