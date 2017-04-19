"""
Set of instructions for getting information about the system.
"""


def get_cpu_temp():
    """
    Returns information about cpu temperature.
    :return: cpu temperature float value
    """
    temp_file = open("/sys/class/thermal/thermal_zone0/temp")
    cpu_temp = temp_file.read()
    temp_file.close()
    return float(cpu_temp) / 1000


def get_uptime():
    """
    Returns pretty string about system uptime.
    :return: uptime string
    """
    uptime_string = ""

    with open('/proc/uptime', 'r') as f:
        total_seconds = float(f.readline().split()[0])

        # Helper vars:
        minute = 60
        hour = minute * 60
        day = hour * 24

        # Get the days, hours, etc:
        days = int(total_seconds / day)
        hours = int((total_seconds % day) / hour)
        minutes = int((total_seconds % hour) / minute)
        seconds = int(total_seconds % minute)

        # Build up the pretty string (like this: "N days, N hours, N minutes, N seconds")
        if days > 0:
            uptime_string += str(days) + " " + (days == 1 and "day" or "days") + ", "
        if len(uptime_string) > 0 or hours > 0:
            uptime_string += str(hours) + " " + (hours == 1 and "hour" or "hours") + ", "
        if len(uptime_string) > 0 or minutes > 0:
            uptime_string += str(minutes) + " " + (minutes == 1 and "minute" or "minutes") + ", "
        uptime_string += str(seconds) + " " + (seconds == 1 and "second" or "seconds")
    return uptime_string
