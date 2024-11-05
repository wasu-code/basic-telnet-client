import socket
import sys
import threading

# Importing msvcrt for Windows or use sys.stdin for Unix-based systems
try:
    import msvcrt  # For Windows
except ImportError:
    import sys
    import tty
    import termios

# Stałe TELNET
IAC = 255  # Interpret As Command
DONT = 254
DO = 253
WONT = 252
WILL = 251
SE = 240  # End of subnegotiation parameters
NOP = 241  # No operation
SB = 250  # Subnegotiation
GA = 249  # Go ahead
EL = 248  # Erase line
EC = 247  # Erase character
AYT = 246  # Are you there
AO = 245  # Abort output
IP = 244  # Interrupt process
BRK = 243  # Break
DM = 242  # Data mark


def filter_telnet_commands(data):
    """Funkcja usuwająca kody sterujące"""
    result = bytearray()
    i = 0
    while i < len(data):
        if data[i] == IAC:
            i += 1  # Pomiń IAC
            if data[i] in (DO, DONT, WILL, WONT):
                i += 2  # Pomiń opcję
            elif data[i] in (SB, SE, NOP, GA, EL, EC, AYT, AO, IP, BRK, DM):
                i += 1  # Pomiń polecenie
        else:
            result.append(data[i])
        i += 1
    return result.decode("utf-8", errors="ignore")


# Funkcja obsługująca opcje TELNET
def handle_telnet_option(command, option, sock):
    if command == DO or command == DONT:
        # Serwer prosi klienta o włączenie lub wyłączenie opcji
        # Odpowiadamy "WONT" dla wszystkich opcji, których nie obsługujemy
        sock.sendall(bytes([IAC, WONT, option]))
    elif command == WILL or command == WONT:
        # Serwer informuje, że będzie lub nie będzie obsługiwał opcji
        # Odpowiadamy "DONT" dla wszystkich opcji, których nie obsługujemy
        sock.sendall(bytes([IAC, DONT, option]))


def receive_data(sock):
    buffer = bytearray()
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("\nPołączenie zamknięte przez serwer.")
                break

            buffer.extend(data)

            # Process data to handle Telnet commands
            i = 0
            while i < len(buffer):
                if buffer[i] == IAC:
                    # We have encountered a Telnet command
                    if i + 1 < len(buffer):
                        command = buffer[i + 1]
                        if command in (DO, DONT, WILL, WONT) and i + 2 < len(buffer):
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
            print(f"\nBłąd połączenia: {e}")
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
        print(f"\nBłąd wysyłania danych: {e}")


def main():
    if len(sys.argv) != 3:
        print("Użycie: python c2.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    # Tworzenie gniazda TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    print(f"Połączono z {host}:{port}")

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
