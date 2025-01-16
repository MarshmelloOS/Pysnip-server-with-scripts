"""
Allows changing another's fly status only if admin
"""

import commands


def fly(connection, player = None):
    protocol = connection.protocol
    if player is not None:
        if connection.admin:
            player = commmands.get_player(connection.protocol, player)
        else:
            return 'No administrator rights!'
    elif connection in protocol.players:
        player = connection
    else:
        raise ValueError('Invalid player')
    player.fly = not player.fly

    message = 'now flying' if player.fly else 'no longer flying'
    player.send_chat("You're %s" % message)
    if connection is not player and connection in protocol.players:
        connection.send_chat('%s is %s' % (player.name, message))
    protocol.send_chat('%s is %s' % (player.name, message), irc=True)
commands.add(fly)


def apply_script(protocol, connection, config):
    return protocol, connection
