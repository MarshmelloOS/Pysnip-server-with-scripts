# Imports
from twisted.internet.reactor import callLater
from twisted.internet import reactor
from pyspades.server import fog_color
from pyspades.common import make_color
from commands import add, admin, name, get_player
from itertools import cycle
import time

R = (255, 0, 0)
BLACK = (0, 0, 0)

morse_code_dict = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
    'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
    'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', ' ': '/'
}

def send_fog(player, color):
    fog_color.color = make_color(*color)
    player.send_contained(fog_color)

@admin
@name('code')
def morse_code(connection, player=None):
    protocol = connection.protocol
    if player is not None:
        player = get_player(protocol, player)
    elif connection in protocol.players:
        player = connection
    else:
        raise ValueError()

    phrase = "Welcome to Build Empire"
    encoded_phrase = encode_morse(phrase)
    
    for letter in encoded_phrase:
        if letter == '.':
            color = R
        elif letter == '-':
            color = BLACK
        else:
            # Space between words
            time.sleep(2)  # Add a delay for better readability
            continue
        send_fog(player, color)
        time.sleep(1)  # Dot duration is 1 unit
    message = 'Morse code transmission completed.'
    return message

def encode_morse(phrase):
    encoded_phrase = []
    for char in phrase.upper():
        if char in morse_code_dict:
            encoded_phrase.extend(morse_code_dict[char])
            encoded_phrase.append(' ')  # Space between letters
    return encoded_phrase

add(morse_code)

def apply_script(protocol, connection, config):
    return protocol, connection
