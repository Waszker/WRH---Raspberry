from abc import ABCMeta, abstractmethod
from enum import Enum


class Color(Enum):
    NORMAL = '\033[0m'
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class IO:
    """
    Abstract class dealing with input/output operations.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self):
        pass

    @staticmethod
    def log(message, color=Color.NORMAL):
        """
        Prints provided message to the screen using color of choice.
        :param message: text to display
        :param color: color enum
        """
        isinstance(color, Color)
        print ''.join((''.join(color), str(message), str(Color.NORMAL)))

    @staticmethod
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

    @staticmethod
    def non_empty_numeric_input(message=''):
        """
        Reads user input discarding all empty and non-integer messages
        :param message: message to display
        :return: user's input number
        """
        while True:
            try:
                answer = int(IO.non_empty_input(message))
                break
            except ValueError:
                continue
        return answer
