#HP tools by Kuma
#Version 1

from commands import add, alias, admin, get_player
from pyspades.constants import *

@admin
def hit(connection, name = None, value = None):
    protocol = connection.protocol
    if name and value is not None:
        player = get_player(protocol, name)
        player.set_hp(player.hp - int(value))
    elif name is not None and value is None:
        player = get_player(protocol, name)
        player.set_hp(player.hp - 50)
    else:
        raise ValueError()

@alias('hpc')
def hpcheck(connection, name= None):
    protocol = connection.protocol
    if name is not None:
        player = get_player(protocol, name)
        connection.send_chat("{} has {} HP".format(player.name, player.hp))

add(hpcheck)

add(hit)

def apply_script(protocol, connection, config):
    return protocol, connection
