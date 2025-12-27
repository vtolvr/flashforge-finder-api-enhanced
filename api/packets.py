# Pre-defined G-code commands for the FlashForge Finder
# All commands need to start with ~ and end with \r\n when sent

# Wake up the printer and enable command mode
# Send this before any other commands or printer ignores you
request_control_message = '~M601 S1\r\n'

# Get printer info (firmware version, model, etc.)
request_info_message = '~M115\r\n'

# Get current print head position
request_head_position = '~M114\r\n'

# Get temperature readings (extruder and bed)
request_temp = '~M105\r\n'

# Get print progress (how many bytes processed)
request_progress = '~M27\r\n'

# Get printer status (endstops, etc.)
request_status = '~M119\r\n'