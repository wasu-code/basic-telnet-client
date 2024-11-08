# [Tel]net [C]ommnads

IAC = 255
"""Interpret as command"""

DONT = 254
"""Indicates the demand that the other party stop performing, or confirmation that you are no longer expecting the other party to perform, the indicated option."""

DO = 253
"""Indicates the request that the other party perform, or confirmation that you are expecting the other party to perform, the indicated option."""

WONT = 252
"""Indicates the refusal to perform, or continue performing, the indicated option."""

WILL = 251
"""Indicates the desire to begin performing, or confirmation that you are now performing, the indicated option."""

SB = 250
"""Subnegotiation of the indicated option follows."""

GA = 249
"""Go ahead. Used, under certain circumstances, to tell the other end that it can transmit."""

EL = 248
"""Erase line. Delete characters from the data stream back to but not including the previous CRLF."""

EC = 247
"""Erase character. The receiver should delete the last preceding undeleted character from the data stream."""

AYT = 246
"""Are you there. Send back to the NVT some visible evidence that the AYT was received."""

AO = 245
"""Abort output. Allows the current process to run to completion but do not send its output to the user."""

IP = 244
"""Interrupt process. Suspend, interrupt or abort the process to which the NVT is connected."""

BRK = 243
"""Break. Indicates that the "break" or "attention" key was hit."""

DM = 242
"""Data mark. Indicates the position of a Synch event within the data stream. This should always be accompanied by a TCP urgent notification."""

NOP = 241
"""No operation"""

SE = 240
"""End of subnegotiation parameters"""

OPTION_LINEMODE = 34

OPTION_ECHO = 1
