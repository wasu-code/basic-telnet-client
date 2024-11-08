# Telnet

## Instalacja programów do testowania

### Instalacja serwera

instalujemy serwer telnet by przez łączenie z nim testować naszego klienta
np. [KpyM](https://www.kpym.com/2/kpym/index.htm)

> potem odinstalować i usunąć usługę !!! (usługę, nie instalator)

Ustawiamy:

- `port`: 23
- `ban_max_connections`: 0

### Instalacja klienta

PuTTY

na PC musimy mięć lokalne konto użytkownika

wireshark

> przechwytywanie ruchu lokalnego

---

stary protokół, ale jest częścią wielu nowszych jak HTTP

## Zadanie

> Celem zadania jest zaimplementowanie klienta protokołu TELNET, zgodnego z RFC854, 855 w dowolnym języku programowania dającym dostęp do TCP Socket i bez wykorzystania dedykowanych bibliotek. Klient będzie działał w wierszu poleceń i musi obsługiwać minimalną funkcjonalność NVT. [`moodle - zad`](https://el.us.edu.pl/wnst/mod/assign/view.php?id=111627)

- nasz klient nie musi obsługiwać dodatkowych opcji ale musi na nie odpowiedzeić (np. że nie zrobi)
- pozbycie się ze strumienia danych części ... żeby kody sterujące nie trafiły do strumienia danych konsoli
- echo
  - lokalne - nasz pc wyświetla na konsoli co wpisaliśmy
  - zdalne - na serwerze jest wpisywane i serwer odsyła co wpisze
- tryb pracy: znak po znaku czy po lini - poinformować serwer

## RFC

[`RFC 854`](https://datatracker.ietf.org/doc/html/rfc854)
[`RFC 855`](https://datatracker.ietf.org/doc/html/rfc855)

> In summary, WILL XXX is sent, by either party, to indicate that
> party's desire (offer) to begin performing option XXX, DO XXX and
> DON'T XXX being its positive and negative acknowledgments; similarly,
> DO XXX is sent to indicate a desire (request) that the other party
> (i.e., the recipient of the DO) begin performing option XXX, WILL XXX
> and WON'T XXX being the positive and negative acknowledgments. Since
> the NVT is what is left when no options are enabled, the DON'T and
> WON'T responses are guaranteed to leave the connection in a state
> which both ends can handle. Thus, all hosts may implement their
> TELNET processes to be totally unaware of options that are not
> supported, simply returning a rejection to (i.e., refusing) any
> option request that cannot be understood.

## TODO

- backspace to ...
