import socket
import struct
import zlib

BUFFER_SIZE = 1024  # How much data to read at once
CHUNK_SIZE = 4096  # Upload files in 4KB chunks


def send_and_receive(printer_address, command):
    """The main communication function - send a command, get a response

    How this works:
    1. Connect to printer on port 8899
    2. Send M601 S1 to wake it up and enable command mode
    3. Wait for 'ok' response
    4. Send your actual command
    5. Wait for response with 'ok' at the end
    6. Clean up and return
    """
    printer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    printer_socket.settimeout(10)  # Don't wait forever

    try:
        printer_socket.connect((printer_address['ip'], printer_address['port']))

        # Wake up the printer - it ignores everything until you send this
        init_command = '~M601 S1\r\n'
        printer_socket.sendall(init_command.encode())

        # Wait for initial 'ok' response
        response = b''
        while b'ok' not in response:
            chunk = printer_socket.recv(BUFFER_SIZE)
            if not chunk:
                break
            response += chunk

        # Now send the actual command we care about
        formatted_command = f'~{command}\r\n'  # Commands need ~ prefix and \r\n suffix
        printer_socket.sendall(formatted_command.encode())

        # Collect the response until we see 'ok'
        response = b''
        while True:
            chunk = printer_socket.recv(BUFFER_SIZE)
            if not chunk:
                break
            response += chunk
            if b'ok\r\n' in response or b'ok\n' in response:
                break

        return response.decode('utf-8', errors='ignore')

    finally:
        printer_socket.close()


def send_file(printer_address, filename, file_content):
    """Upload a file to the printer - this is where the CRC fun happens

    The protocol:
    1. Connect and init with M601 S1
    2. Send M650 (prepare for file transfer)
    3. Send M28 with file size and path
    4. Send file data in 4KB chunks with special headers
    5. Send M29 to finish

    Each chunk needs:
    - Magic bytes (0x5a5aa5a5)
    - Packet counter
    - Chunk size (always 4096)
    - CRC32 checksum
    - The actual data (padded to 4096 bytes)
    """
    printer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    printer_socket.settimeout(30)  # File upload takes longer

    try:
        printer_socket.connect((printer_address['ip'], printer_address['port']))

        # Same initialization dance as regular commands
        init_command = '~M601 S1\r\n'
        printer_socket.sendall(init_command.encode())
        response = b''
        while b'ok' not in response:
            chunk = printer_socket.recv(BUFFER_SIZE)
            if not chunk:
                break
            response += chunk

        # Tell printer we're about to send a file
        m650_cmd = '~M650\r\n'
        printer_socket.sendall(m650_cmd.encode())
        response = b''
        while b'ok' not in response:
            chunk = printer_socket.recv(BUFFER_SIZE)
            if not chunk:
                break
            response += chunk

        # Tell printer the file size and where to save it
        # Format: M28 <size> 0:/user/<filename>
        file_size = len(file_content)
        m28_cmd = f'~M28 {file_size} 0:/user/{filename}\r\n'
        printer_socket.sendall(m28_cmd.encode())
        response = b''
        while b'ok' not in response:
            chunk = printer_socket.recv(BUFFER_SIZE)
            if not chunk:
                break
            response += chunk

        # Now the fun part - send the file in chunks
        counter = 0  # Packet sequence number
        offset = 0

        while offset < file_size:
            # Grab next chunk of actual data (might be less than 4KB at end)
            chunk_end = min(offset + CHUNK_SIZE, file_size)
            actual_data = file_content[offset:chunk_end]
            actual_data_len = len(actual_data)

            # Calculate CRC32 on the UNPADDED data
            # This is important - CRC before padding!
            crc = zlib.crc32(actual_data) & 0xffffffff

            # NOW pad the data to 4096 bytes with zeros
            data_chunk = actual_data + b'\x00' * (CHUNK_SIZE - actual_data_len)

            # Build the packet header
            # Format: magic(4 bytes) + counter(4 bytes) + length(4 bytes) + crc(4 bytes)
            # Using >BBBBIII means big-endian, 4 individual bytes, then 3 unsigned ints
            header = struct.pack('>BBBBIII',
                                 0x5a, 0x5a, 0xa5, 0xa5,  # Magic bytes - printer checks these
                                 counter,  # Which packet is this
                                 CHUNK_SIZE,  # Always 4096
                                 crc)  # CRC32 of unpadded data

            # Send header + padded data as one packet
            packet = header + data_chunk
            printer_socket.sendall(packet)

            # Give the printer a moment to breathe
            # Without this, some printers get overwhelmed
            import time
            time.sleep(0.01)

            offset = chunk_end
            counter += 1

        # Tell printer we're done sending data
        m29_cmd = '~M29\r\n'
        printer_socket.sendall(m29_cmd.encode())
        response = b''
        while b'ok' not in response:
            chunk = printer_socket.recv(BUFFER_SIZE)
            if not chunk:
                break
            response += chunk

        return f'File {filename} uploaded successfully'

    except Exception as e:
        raise Exception(f'Upload failed: {str(e)}')
    finally:
        printer_socket.close()