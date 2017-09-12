from enum import Enum

"""
Set of commands to deal with input/output operations.
"""


class Color(Enum):
    NORMAL = '\033[0m'
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def __str__(self):
        return str(self.value)


def log(message, color=Color.NORMAL):
    """
    Prints provided message to the screen using color of choice.
    :param message: text to display
    :param color: color enum
    """
    try:
        decoration = ''.join([str(c) for c in color])
    except TypeError:
        decoration = str(color)
    print ''.join((decoration, str(message), str(Color.NORMAL)))


def non_empty_input(message=''):
    """
    Reads user input discarding all empty messages.
    :param message: message to display
    :return: user's input
    """
    answer = None
    while answer is None or len(answer) == 0:
        answer = raw_input(message)
    return answer


def non_empty_numeric_input(message=''):
    """
    Reads user input discarding all empty and non-integer messages
    :param message: message to display
    :return: user's input number
    """
    while True:
        try:
            answer = int(non_empty_input(message))
            break
        except ValueError:
            continue
    return answer


def non_empty_positive_numeric_input(message=''):
    """
    Reads user input discarding all empty and non-integer messages
    :param message: message to display
    :return: user's input number
    """
    while True:
        try:
            answer = int(non_empty_input(message))
            if answer < 0: continue
            break
        except ValueError:
            continue
    return answer
