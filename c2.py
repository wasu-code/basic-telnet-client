import socket
import sys
import threading
import telc

# Importing msvcrt for Windows or use sys.stdin for Unix-based systems
try:
    import msvcrt  # For Windows
except ImportError:
    import sys
    import tty
    import termios


def filter_telnet_commands(data):
    """Funkcja usuwająca kody sterujące"""
    result = bytearray()
    i = 0
    while i < len(data):
        if data[i] == telc.IAC:
            i += 1  # Pomiń IAC
            if data[i] in (telc.DO, telc.DONT, telc.WILL, telc.WONT):
                i += 2  # Pomiń opcję
            elif data[i] in (
                telc.SB,
                telc.SE,
                telc.NOP,
                telc.GA,
                telc.EL,
                telc.EC,
                telc.AYT,
                telc.AO,
                telc.IP,
                telc.BRK,
                telc.DM,
            ):
                i += 1  # Pomiń polecenie
        else:
            result.append(data[i])
        i += 1
    return result.decode("utf-8", errors="ignore")


def handle_telnet_option(command, option, sock):
    """Funkcja obsługująca negocjacje opcji TELNET"""
    if command == telc.DO or command == telc.DONT:
        # Serwer prosi klienta o włączenie lub wyłączenie opcji
        # Odpowiadamy "WONT" dla wszystkich opcji, których nie obsługujemy
        sock.sendall(bytes([telc.IAC, telc.WONT, option]))
    elif command == telc.WILL or command == telc.WONT:
        # Serwer informuje, że będzie lub nie będzie obsługiwał opcji
        # Odpowiadamy "DONT" dla wszystkich opcji, których nie obsługujemy
        sock.sendall(bytes([telc.IAC, telc.DONT, option]))


def receive_data(sock):
    """Function to receive and print data from the server"""
    buffer = bytearray()
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("\nConnection closed by the server.")
                break

            buffer.extend(data)

            # Process data to handle Telnet commands
            i = 0
            while i < len(buffer):
                if buffer[i] == telc.IAC:
                    # We have encountered a Telnet command
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
                    print(chr(buffer[i]), end="", flush=True)
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
                print(char.decode(), end="", flush=True)  # Echo na konsoli
        else:
            # Unix-based: użycie sys.stdin do odczytu znaków
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                while True:
                    char = sys.stdin.read(1)  # Odczytaj pojedynczy znak
                    sock.sendall(char.encode())  # Wyślij znak do serwera
                    print(char, end="", flush=True)  # Echo na konsoli
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
