# FlashForge Finder API Enhanced

A Python REST API for controlling FlashForge Finder 3D printers over WiFi. This is a complete rewrite of [01F0's flashforge-finder-api](https://github.com/01F0/flashforge-finder-api) with way more features and actual working code.

## What This Does

Controls your FlashForge Finder printer through a simple REST API. You can check temps, move the print head around, change LED colors, and upload files - all over your local network.

**Current Features:**
- Get printer status, temperature, position, and print progress
- Home the printer (all axes or just one)
- Move the print head wherever you want
- Change the LED color because why not
- Pause, resume, or stop prints
- Upload G-code files (mostly working, see known issues)

## Why This Exists

The original repo by 01F0 was a great start, but it's 3 years old and basically doesn't work anymore without heavy modifications. I spent way too much time fixing and adding to it, so figured I'd share the results instead of letting it rot on my hard drive.

This isn't a pull request because:
- I rewrote like 95% of the code
- Added a ton of new stuff
- Changed the whole structure
- The original repo hasn't been touched in years
- PRs take forever and this was faster

## Setup

You need Python 3.8 or newer.

```bash
git clone https://github.com/YOUR_USERNAME/flashforge-finder-api-enhanced.git
cd flashforge-finder-api-enhanced
pip install -r requirements.txt
python api/app.py
```

Server runs on http://localhost:5000

## How TO Use It
Replace <ip> with your printer's IP (find it in your router or printer settings).

### Check Stuff

```
# Temperature
curl http://localhost:5000/<ip>/temp

# Current position
curl http://localhost:5000/<ip>/head-location

# Print progress
curl http://localhost:5000/<ip>/progress

# General status
curl http://localhost:5000/<ip>/status

# Printer info
curl http://localhost:5000/<ip>/info
```

### Control The Printer

```
# Home everything
curl -X POST http://localhost:5000/<ip>/home

# Home just Z axis
curl -X POST http://localhost:5000/<ip>/home \
  -H "Content-Type: application/json" \
  -d '{"axis":"Z"}'

# Move somewhere
curl -X POST http://localhost:5000/<ip>/move \
  -H "Content-Type: application/json" \
  -d '{"x":50,"y":50,"z":10,"speed":3000}'

# Make it red
curl -X POST http://localhost:5000/<ip>/led \
  -H "Content-Type: application/json" \
  -d '{"r":255,"g":0,"b":0}'

# Pause/resume/stop
curl -X POST http://localhost:5000/<ip>/pause
curl -X POST http://localhost:5000/<ip>/resume
curl -X POST http://localhost:5000/<ip>/stop
```

### Upload Files

```
curl -X POST http://localhost:5000/<ip>/upload \
  -F "file=@yourfile.gcode"
```

### Python Examples

```
import requests

PRINTER_IP = "10.0.0.96" # REPLACE WITH YOUR OWN PRINTERS IP (OBVIOUSLY)
BASE_URL = f"http://localhost:5000/{PRINTER_IP}"

# Check temperature
temp = requests.get(f"{BASE_URL}/temp").json()
print(f"Extruder: {temp['current_temperature']}°C")

# Move the head
requests.post(f"{BASE_URL}/move", json={
    "x": 50,
    "y": 50,
    "z": 10,
    "speed": 3000
})

# Change LED to red because we can lol
requests.post(f"{BASE_URL}/led", json={
    "r": 255,
    "g": 0,
    "b": 0
})
```

## How The Protocol Works
The Finder talks over TCP on port 8899. Here's what you need to know:

1. First send ~M601 S1\r\n or it ignores you
2. All commands start with ~ and end with \r\n
3. Wait for ok in the response before sending more commands
4. Don't spam it or it might just turn off

### G-code COmmands That Work

```
M105   - Get temperature
M114   - Current position
M119   - Endstop status
M27    - Print progress
G28    - Home (add X/Y/Z for specific axis)
G1     - Move somewhere
M146   - LED color
M25    - Pause
M24    - Resume
M26    - Stop
```

## File Structure

```
flashforge-finder-api-enhanced/
├── api/
│   ├── app.py              # Flask server and routes
│   ├── protocol.py         # G-code functions
│   ├── socket_handler.py   # TCP communication
│   └── regex_patterns.py   # Old parsing stuff
├── requirements.txt
├── README.md
└── LICENSE
```

## Known Issues
File upload gives CRC errors - The upload works but the printer complains about CRC mismatches. I'm still debugging this. The protocol docs say one thing but the printer seems to want something slightly different. If you figure it out, please let me know.

## Credits
Based on the original work by 01F0.

Also learned a lot from random forum posts and people who reverse-engineered this protocol before me. The FlashForge community is small but helpful.

## Want To Help?
Pull requests welcome. Things that need work:

- Fix that CRC error in uploads

## License
MIT - do whatever you want with it
