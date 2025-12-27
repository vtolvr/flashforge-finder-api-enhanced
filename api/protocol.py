from socket_handler import send_and_receive, send_file
from regex_patterns import regex_for_field, regex_for_coordinates, regex_for_current_temperature, \
    regex_for_target_temperature, regex_for_progress
import re


def get_info(printer_address):
    """Ask the printer about itself - basically M115 command
    Returns stuff like firmware version, model name, etc.
    """
    response = send_and_receive(printer_address, 'M115')
    info = {}
    lines = response.split('\n')

    # Parse each line that looks like "key: value"
    for line in lines:
        if ':' in line and 'CMD' not in line and 'ok' not in line:
            key_value = line.strip().split(':', 1)
            if len(key_value) == 2:
                info[key_value[0].strip()] = key_value[1].strip()
    return info


def get_temp(printer_address):
    """Check temperatures - M105 command
    Gets both extruder (T0) and bed (B) temps, current and target
    """
    response = send_and_receive(printer_address, 'M105')
    temp_info = {}

    # Extract temps using regex because the format is: "T0:200/210 B:60/60"
    # First number is current, second is target
    current_temp_match = re.search(r'T0:(-?[0-9.]+)', response)
    target_temp_match = re.search(r'T0:[0-9.]+ /(-?[0-9.]+)', response)
    bed_current_match = re.search(r'B:(-?[0-9.]+)', response)
    bed_target_match = re.search(r'B:[0-9.]+ /(-?[0-9.]+)', response)

    if current_temp_match:
        temp_info['current_temperature'] = current_temp_match.group(1)
    if target_temp_match:
        temp_info['target_temperature'] = target_temp_match.group(1)
    if bed_current_match:
        temp_info['bed_current_temperature'] = bed_current_match.group(1)
    if bed_target_match:
        temp_info['bed_target_temperature'] = bed_target_match.group(1)
    return temp_info


def get_head_position(printer_address):
    """Where's the print head right now? - M114 command
    Returns X, Y, Z coordinates in millimeters
    """
    response = send_and_receive(printer_address, 'M114')
    position = {}

    # Response format is like "X:50.0 Y:50.0 Z:10.0"
    x_match = re.search(r'X:(-?[0-9.]+)', response)
    y_match = re.search(r'Y:(-?[0-9.]+)', response)
    z_match = re.search(r'Z:(-?[0-9.]+)', response)

    if x_match:
        position['x'] = x_match.group(1)
    if y_match:
        position['y'] = y_match.group(1)
    if z_match:
        position['z'] = z_match.group(1)
    return position


def get_progress(printer_address):
    """How far into the print are we? - M27 command
    Returns current byte position and total file size
    """
    response = send_and_receive(printer_address, 'M27')
    progress_info = {}

    # Format is like "1234/5678" (current bytes / total bytes)
    progress_match = re.search(r'([0-9]+)/([0-9]+)', response)

    if progress_match:
        current = int(progress_match.group(1))
        total = int(progress_match.group(2))
        progress_info['current_byte'] = current
        progress_info['total_bytes'] = total
        # Calculate percentage if we have valid data
        if total > 0:
            progress_info['percentage'] = round((current / total) * 100, 2)
    return progress_info


def get_status(printer_address):
    """General printer status - M119 command
    Checks endstop states (switches that tell if axes are at limits)
    """
    response = send_and_receive(printer_address, 'M119')
    status_info = {'raw_response': response}
    lines = response.split('\n')

    # Parse endstop states - they're formatted like "x_min: TRIGGERED" or "x_min: open"
    for line in lines:
        if 'endstop' in line.lower() or 'TRIGGERED' in line or 'open' in line:
            parts = line.strip().split(':')
            if len(parts) == 2:
                status_info[parts[0].strip()] = parts[1].strip()
    return status_info


def home_printer(printer_address, axis='all'):
    """Send the print head home - G28 command
    axis: 'all' homes everything, or specify 'X', 'Y', or 'Z' for just one
    Homing means moving until it hits the endstop switches
    """
    if axis.upper() == 'ALL':
        command = 'G28'  # Home all axes
    else:
        command = f'G28 {axis.upper()}'  # Home specific axis

    response = send_and_receive(printer_address, command)
    return response


def move_axis(printer_address, x=None, y=None, z=None, speed=3000):
    """Move the print head - G1 command
    x, y, z: where to move (in millimeters), leave as None to keep current position
    speed: how fast to move (mm/min), default is 3000

    Example: move_axis(printer, x=50, y=50) moves to X=50, Y=50, keeps Z the same
    """
    command = 'G1'

    # Only add coordinates we actually want to change
    if x is not None:
        command += f' X{x}'
    if y is not None:
        command += f' Y{y}'
    if z is not None:
        command += f' Z{z}'
    command += f' F{speed}'  # F is feedrate (speed)

    response = send_and_receive(printer_address, command)
    return response


def set_led_color(printer_address, r, g, b):
    """Change the LED color - M146 command
    r, g, b: standard RGB values (0-255 each)
    The 'f0' at the end keeps it solid (not blinking)
    """
    command = f'M146 r{r} g{g} b{b} f0'
    response = send_and_receive(printer_address, command)
    return response


def pause_print(printer_address):
    """Hit pause on the current print - M25 command"""
    response = send_and_receive(printer_address, 'M25')
    return response


def resume_print(printer_address):
    """Continue a paused print - M24 command"""
    response = send_and_receive(printer_address, 'M24')
    return response


def stop_print(printer_address):
    """Stop the print completely - M26 command
    This cancels it, not just pause
    """
    response = send_and_receive(printer_address, 'M26')
    return response


def upload_file(printer_address, filename, file_content):
    """Upload a gcode file to the printer
    filename: what to call it on the printer (max 36 characters or it breaks)
    file_content: the actual file as bytes

    This is the function that currently has CRC issues
    """
    if len(filename) > 36:
        raise ValueError("Filename must be 36 bytes or less")

    result = send_file(printer_address, filename, file_content)
    return result