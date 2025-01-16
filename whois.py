"""
Queries who a player is logged in as when using the alternatelogin.py script
"""

import commands


def whois(connection, player):
    player = commands.get_player(connection.protocol, player)
    username = player.username
    if username is None:
        message = ' is not logged in.'
    else:
        message = ' is logged in as ' + username
    return player.name + message
commands.add(whois)


def apply_script(protocol, connection, config):
    return protocol, connection
