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


def handle_telnet_option(command, option, sock):
    """Funkcja obsługująca negocjacje opcji TELNET"""
    print(f">>>{command}, {option}")
    if command == telc.WILL and option == telc.OPTION_ECHO:
        print("echo? then dont")
        return sock.sendall(bytes([telc.IAC, telc.DONT, telc.OPTION_ECHO]))

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
            break


def send_data(sock):
    """Funkcja wysyłająca dane użytkownika do serwera znak po znaku"""
    try:
        if sys.platform == "win32":
            # Windows: użycie msvcrt do odczytu znaków
            while True:
                char = msvcrt.getch()  # Odczytaj pojedynczy znak
                sock.sendall(char)  # Wyślij znak do serwera
                # print(char.decode(), end="", flush=True)  # Echo na konsoli
        else:
            # Unix-based: użycie sys.stdin do odczytu znaków
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                while True:
                    char = sys.stdin.read(1)  # Odczytaj pojedynczy znak
                    sock.sendall(char.encode())  # Wyślij znak do serwera
                    # print(char, end="", flush=True)  # Echo na konsoli
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except socket.error as e:
        print(f"\nError sending data: {e}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python <filename>.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    # Tworzenie gniazda TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    print(f"Connected to {host}:{port}")

    # Tworzenie i uruchamianie wątków do odbierania i wysyłania danych
    receive_thread = threading.Thread(target=receive_data, args=(sock,))
    send_thread = threading.Thread(target=send_data, args=(sock,))

    # Ustawienie wątków jako daemons, aby zamykały się po zakończeniu głównego programu
    receive_thread.daemon = True
    send_thread.daemon = True

    # Start wątków
    receive_thread.start()
    send_thread.start()

    # Czekanie na zakończenie wątków
    receive_thread.join()
    send_thread.join()

    # Zamknięcie połączenia po zakończeniu
    sock.close()


if __name__ == "__main__":
    main()
