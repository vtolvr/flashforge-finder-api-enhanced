def regex_for_field(field_name):
    """Parse generic field from printer response

    Example response: "Machine Type: Flashforge Finder\r\n"
    This grabs everything after the colon until the line ends

    field_name: the thing you're looking for (like "Machine Type")
    Returns a regex pattern that captures the value
    """
    return field_name + ': ?(.+?)\\r\\n'


def regex_for_coordinates(field_name):
    """Parse coordinate values from position responses

    Example response: "X:-19.19 Y:6 Z:7.3 A:846.11 B:0"
    Grabs the number after the coordinate letter

    field_name: which axis you want (X, Y, Z, etc.)
    Returns pattern that captures the number until next space
    """
    return field_name + ':(.+?) '


def regex_for_current_temperature():
    """Get the CURRENT temperature from temp response

    Example response: "T0:210 /210 B:0 /0"
    Format is: T0:current/target B:current/target

    This grabs the first number (current temp) for T0 (extruder)
    The -? part handles negative temps (shouldn't happen but just in case)
    """
    return 'T0:(-?[0-9].*?) '


def regex_for_target_temperature():
    """Get the TARGET temperature from temp response

    Example response: "T0:210 /210 B:0 /0"
    This grabs the number AFTER the slash (target temp)

    So from "210 /210" it captures the second "210"
    """
    return r'/(-?[0-9].*?) '


def regex_for_progress():
    """Parse print progress from M27 response

    Example response: "1234/5678\r"
    Format is: current_bytes/total_bytes

    This captures both numbers so we can calculate percentage
    Group 1 = bytes printed so far
    Group 2 = total file size in bytes
    """
    return r'([0-9].*)/([0-9].*?)\r'