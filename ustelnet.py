import re
import socket
import sys
import threading
import telc  # telnet commands

# Importing msvcrt for Windows or use sys.stdin for Unix-based systems
try:
    import msvcrt  # For Windows
except ImportError:
    import sys
    import tty
    import termios

ACCEPT_CONTROL_CHARS = (
    False  # Enable (for VSC) or disable (for cmd) printing of control characters
)
LOCAL_ECHO = True

stop_event = threading.Event()


def handle_telnet_option(command, option, sock):
    """Function to handle TELNET options negotiations"""
    # print(f">>>{command}, {option}")
    if command == telc.WILL and option == telc.OPTION_ECHO:
        global LOCAL_ECHO
        LOCAL_ECHO = False  # server sends echo, no need to double it with local echo
        print("Using remote echo", end="", flush=True)
        return sock.sendall(bytes([telc.IAC, telc.DO, telc.OPTION_ECHO]))

    if command == telc.DO or command == telc.DONT:
        # Server asks to turn option on/off
        # Answer "WONT" for all (unsupported) options
        sock.sendall(bytes([telc.IAC, telc.WONT, option]))
    elif command == telc.WILL or command == telc.WONT:
        # Server informs it will/won't support a given option
        # Answer "DONT" for all (unsupported) options
        sock.sendall(bytes([telc.IAC, telc.DONT, option]))


def receive_data(sock):
    """Function to receive and print data from the server. Also handles detecting Telnet commands and ANSI escape codes."""
    buffer = bytearray()

    # Regular expression patterns to identify ANSI codes for control sequences
    ansi_escape_pattern = re.compile(
        rb"\x1B\[[0-?]*[ -/]*[@-~]"
    )  # General ANSI escape code
    cursor_position_pattern = re.compile(
        rb"\x1b\[(\d*);(\d*)f"
    )  # Move cursor to (row; col)
    cursor_down_pattern = re.compile(rb"\x1b\[(\d*)B")  # Move cursor down
    clear_line_pattern = re.compile(rb"\x1b\[2K")  # Clear line

    last_row = 0
    last_col = 0
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("\nConnection closed by the server.")
                stop_event.set()
                break

            buffer.extend(data)

            # Process data to handle Telnet commands and detect ANSI escape codes
            i = 0
            while i < len(buffer):
                if not ACCEPT_CONTROL_CHARS:
                    # Detect ANSI escape codes
                    match = ansi_escape_pattern.match(buffer[i:])
                    if match:
                        ansi_sequence = match.group(0)

                        # Handle specific ANSI sequences
                        if cursor_position_pattern.match(ansi_sequence):
                            # Match the cursor position ANSI code
                            row, col = cursor_position_pattern.match(
                                ansi_sequence
                            ).groups()
                            row = int(row) if row.isdigit() else last_row
                            col = int(col) if col.isdigit() else last_col
                            # Add newlines only if overriding some existing text
                            if col < last_col:
                                print("\n", end="", flush=True)
                            last_row = row
                            last_col = col

                        elif cursor_down_pattern.match(ansi_sequence):
                            # Match the cursor down ANSI code
                            num_lines = int(
                                cursor_down_pattern.match(ansi_sequence).group(1) or 1
                            )

                            # Only add newlines if moving down by more than 1 line
                            if num_lines > 1:
                                print("\n" * (num_lines - 1), end="", flush=True)

                        elif clear_line_pattern.match(ansi_sequence):
                            # Clear line (approximate by starting a new line)
                            print("\n", end="", flush=True)

                        # Move the index past the matched ANSI escape code
                        i += len(ansi_sequence)
                        continue  # Continue to process the rest of the buffer

                # Handle Telnet commands
                if buffer[i] == telc.IAC:
                    # IAC indicates a control command
                    if i + 1 < len(buffer):
                        command = buffer[i + 1]
                        if command in (
                            telc.DO,
                            telc.DONT,
                            telc.WILL,
                            telc.WONT,
                        ) and i + 2 < len(buffer):
                            option = buffer[i + 2]
                            handle_telnet_option(command, option, sock)
                            i += 2  # Skip the option byte
                        else:
                            # Skip the command byte
                            i += 1
                else:
                    # Normal data; print it
                    char = chr(buffer[i])
                    print(char, end="", flush=True)
                i += 1

            # Clear the processed part of the buffer
            buffer = buffer[i:]

        except socket.error as e:
            print(f"\nConnection error: {e}")
            stop_event.set()
            break


def send_data(sock):
    """Funkcja wysyłająca dane użytkownika do serwera znak po znaku"""
    try:
        if sys.platform == "win32":
            # Windows: użycie msvcrt do odczytu znaków
            while True:
                char = msvcrt.getch()  # Odczytaj pojedynczy znak
                sock.sendall(char)  # Wyślij znak do serwera
                if LOCAL_ECHO:
                    print(char.decode(), end="", flush=True)  # Echo na konsoli
        else:
            # Unix-based: użycie sys.stdin do odczytu znaków
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                while True:
                    char = sys.stdin.read(1)
                    sock.sendall(char.encode())
                    if LOCAL_ECHO:
                        print(char, end="", flush=True)  # Echo na konsoli
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except socket.error as e:
        print(f"\nError sending data: {e}")
        stop_event.set()


def main():
    if len(sys.argv) == 3:
        # Usage: python <filename>.py <host> <port>"
        host = sys.argv[1]
        port = int(sys.argv[2])
    else:
        host = str(input("Target host (defaults to localhost): ") or "localhost")
        port = int(input("Target port (defaults to 23): ") or 23)

    try:
        # Create TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        print(f"Connected to {host}:{port}")
    except ConnectionRefusedError:
        print(
            "Error: Connection refused. The server may not be listening on the specified port."
        )
        sys.exit(1)  # Exit the program with an error code
    except socket.timeout:
        print("Error: Connection timed out.")
        sys.exit(1)
    except socket.error as e:
        print(f"Socket error: {e}")
        sys.exit(1)

    sock.sendall(
        bytes([telc.IAC, telc.WONT, telc.OPTION_LINEMODE])
    )  # inform server we won't be sending lines but chars

    # Separate threads for sending and receiving data
    receive_thread = threading.Thread(target=receive_data, args=(sock,))
    send_thread = threading.Thread(target=send_data, args=(sock,))

    # Set threads as daemons, so they close after main program closes
    receive_thread.daemon = True
    send_thread.daemon = True

    receive_thread.start()
    send_thread.start()

    # Close main program after thread event is set
    stop_event.wait()

    # Close connection
    sock.close()


if __name__ == "__main__":
    main()
