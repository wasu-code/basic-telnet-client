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
    """Funkcja obsługująca negocjacje opcji TELNET"""
    # print(f">>>{command}, {option}")
    if command == telc.WILL and option == telc.OPTION_ECHO:
        global LOCAL_ECHO
        LOCAL_ECHO = False  # server sends echo, no need to double it with local echo
        print("Using remote echo")
        return sock.sendall(bytes([telc.IAC, telc.DO, telc.OPTION_ECHO]))

    if command == telc.DO or command == telc.DONT:
        # Serwer prosi klienta o włączenie lub wyłączenie opcji
        # Odpowiadamy "WONT" dla wszystkich opcji, których nie obsługujemy
        sock.sendall(bytes([telc.IAC, telc.WONT, option]))
    elif command == telc.WILL or command == telc.WONT:
        # Serwer informuje, że będzie lub nie będzie obsługiwał opcji
        # Odpowiadamy "DONT" dla wszystkich opcji, których nie obsługujemy
        sock.sendall(bytes([telc.IAC, telc.DONT, option]))


def receive_data(sock):
    """Function to receive and print data from the server, detecting Telnet commands and ANSI escape codes."""
    buffer = bytearray()

    # Regular expression pattern for ANSI escape codes
    ansi_escape_pattern = re.compile(rb"\x1B\[[0-?]*[ -/]*[@-~]")

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

    # Create TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    print(f"Connected to {host}:{port}")

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
