from twisted.internet.reactor import seconds
from pyspades.constants import *
from commands import add, get_player


#Script writted by MegaStar (3/19/2020)
#/drop to drop intel, also /drop (player/#ID) (only administrator)


WAIT_DROP = 5 #seconds that player need wait to take again the intel when use /drop

def drop(connection, player = None):
    if player is not None:
        if not connection.admin:
            return connection.send_chat("Only admin can use /drop in other players.")
        player = get_player(connection.protocol, player)
    elif connection in connection.protocol.players:
        player = connection
    else:
        raise ValueError()
    flag = player.team.other.flag
    if flag.player is not None:
        if flag.player is player:
            player.drop_time = seconds() + WAIT_DROP
            player.drop_flag()
            if connection is player:
                return connection.send_chat("You dropped the intel.")
            else:
                return connection.protocol.irc_say("{0} use drop in the player {1}".format(connection.name, player.name))

    msg = (player.name if player and (connection is not player) else "You currently") + " didn't have the intel"

    if connection in connection.protocol.players:
        return connection.send_chat(msg)
    else:
        return msg

add(drop)

def apply_script(protocol, connection, config):

    class DropIntelConnection(connection):
        drop_time = False

        def take_flag(self):
            if self.drop_time is not False:
                if seconds() <= self.drop_time:
                    return False
                else:
                    self.drop_time = False
            return connection.take_flag(self)


    return protocol, DropIntelConnection
