# Import all our protocol functions
from protocol import get_info
from protocol import get_head_position
from protocol import get_temp
from protocol import get_progress
from protocol import get_status
from protocol import home_printer
from protocol import move_axis
from protocol import set_led_color
from protocol import pause_print
from protocol import resume_print
from protocol import stop_print
from protocol import upload_file

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from browsers

PORT = 8899  # FlashForge Finder's TCP port


@app.route("/")
def index():
    """Root endpoint - just returns empty string"""
    return ''


@app.route("/<string:ip_address>/info")
def info(ip_address):
    """GET /10.0.0.96/info
    Returns printer info like firmware version, model, etc.
    """
    try:
        printer_info = get_info({'ip': ip_address, 'port': PORT})
        return jsonify(printer_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/<string:ip_address>/head-location")
def head_location(ip_address):
    """GET /10.0.0.96/head-location
    Where is the print head right now? Returns X, Y, Z coordinates
    """
    try:
        printer_info = get_head_position({'ip': ip_address, 'port': PORT})
        return jsonify(printer_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/<string:ip_address>/temp")
def temp(ip_address):
    """GET /10.0.0.96/temp
    Current and target temperatures for extruder and bed
    """
    try:
        printer_info = get_temp({'ip': ip_address, 'port': PORT})
        return jsonify(printer_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/<string:ip_address>/progress")
def progress(ip_address):
    """GET /10.0.0.96/progress
    How far into the current print? Returns bytes and percentage
    """
    try:
        printer_info = get_progress({'ip': ip_address, 'port': PORT})
        return jsonify(printer_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/<string:ip_address>/status")
def status(ip_address):
    """GET /10.0.0.96/status
    General printer status - endstops, etc.
    """
    try:
        printer_info = get_status({'ip': ip_address, 'port': PORT})
        return jsonify(printer_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/<string:ip_address>/home", methods=['POST'])
def home(ip_address):
    """POST /10.0.0.96/home
    Home all axes, or send {"axis": "Z"} to home just one
    """
    try:
        # If JSON is sent, look for 'axis' field, otherwise home everything
        axis = request.json.get('axis', 'all') if request.is_json else 'all'
        result = home_printer({'ip': ip_address, 'port': PORT}, axis)
        return jsonify({'success': True, 'response': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/<string:ip_address>/move", methods=['POST'])
def move(ip_address):
    """POST /10.0.0.96/move
    Move to a position
    Expects JSON: {"x": 10, "y": 20, "z": 5, "speed": 3000}
    You can leave out any coordinate to keep it at current position
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.json
        x = data.get('x')  # None if not provided
        y = data.get('y')
        z = data.get('z')
        speed = data.get('speed', 3000)  # Default to 3000 mm/min

        result = move_axis({'ip': ip_address, 'port': PORT}, x, y, z, speed)
        return jsonify({'success': True, 'response': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/<string:ip_address>/led", methods=['POST'])
def led(ip_address):
    """POST /10.0.0.96/led
    Change LED color
    Expects JSON: {"r": 255, "g": 0, "b": 0}
    Values are 0-255 like normal RGB
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.json
        r = data.get('r', 0)  # Default to 0 if not provided
        g = data.get('g', 0)
        b = data.get('b', 0)

        result = set_led_color({'ip': ip_address, 'port': PORT}, r, g, b)
        return jsonify({'success': True, 'response': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/<string:ip_address>/pause", methods=['POST'])
def pause(ip_address):
    """POST /10.0.0.96/pause
    Pause whatever's printing right now
    """
    try:
        result = pause_print({'ip': ip_address, 'port': PORT})
        return jsonify({'success': True, 'response': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/<string:ip_address>/resume", methods=['POST'])
def resume(ip_address):
    """POST /10.0.0.96/resume
    Continue a paused print
    """
    try:
        result = resume_print({'ip': ip_address, 'port': PORT})
        return jsonify({'success': True, 'response': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/<string:ip_address>/stop", methods=['POST'])
def stop(ip_address):
    """POST /10.0.0.96/stop
    Stop the print completely - this cancels it
    """
    try:
        result = stop_print({'ip': ip_address, 'port': PORT})
        return jsonify({'success': True, 'response': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/<string:ip_address>/upload", methods=['POST'])
def upload(ip_address):
    """POST /10.0.0.96/upload
    Upload a gcode file to the printer
    Send as multipart/form-data with file field named 'file'

    Note: Currently gives CRC errors on the printer - still debugging
    """
    try:
        # Make sure they actually sent a file
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Read the whole file into memory
        file_content = file.read()
        filename = file.filename

        result = upload_file({'ip': ip_address, 'port': PORT}, filename, file_content)
        return jsonify({'success': True, 'response': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Run the Flask server in debug mode
    app.run(debug=True)