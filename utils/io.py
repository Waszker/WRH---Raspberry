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
    print(''.join((decoration, str(message), str(Color.NORMAL))))


def wrh_input(allowed_empty=False, message='', input_type=str, sanitizer=lambda x: True, allowed_exceptions=()):
    """
    Input sanitizing function that can be used for requesting specific input formats
    (see non_empty_numeric_input(), etc.)
    :param allowed_empty: is input allowed to be empty
    :param message: message to be displayed
    :param input_type: type of the expected input (str, int, Object())
    :type input_type: any
    :param sanitizer: function returning bool value, that checks if input is OK
    :param allowed_exceptions: exceptions that should not be raised during input parsing
    :return: parsed user's input
    """
    while True:
        try:
            answer = raw_input(message)
            if allowed_empty and not answer:
                break
            answer = input_type(answer)
            if not sanitizer(answer):
                continue
            break
        except allowed_exceptions:
            pass
    return answer


def non_empty_input(message='', **kwargs):
    """
    Reads user input discarding all empty messages.
    :param message: message to display
    :param kwargs: additional kwargs to be passed to wrh_input()
    :return: user's input
    """
    return wrh_input(message=message, **kwargs)


def non_empty_numeric_input(message='', **kwargs):
    """
    Reads user input discarding all empty and non-integer messages
    :param message: message to display
    :param kwargs: additional kwargs to be passed to wrh_input()
    :return: user's input number
    """
    return wrh_input(message=message, input_type=int, allowed_exceptions=(ValueError,), **kwargs)


def non_empty_positive_numeric_input(message='', **kwargs):
    """
    Reads user input discarding all empty and non-integer messages
    :param message: message to display
    :param kwargs: additional kwargs to be passed to wrh_input()
    :return: user's input number
    """
    return wrh_input(message=message, input_type=int, sanitizer=lambda x: x >= 0, allowed_exceptions=(ValueError,),
                     **kwargs)
