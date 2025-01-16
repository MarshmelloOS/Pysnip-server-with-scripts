"""
Jail script by PXYC
Edited by Ninja Pig
Fixed by thepolm3
"""
 
from pyspades.common import to_coordinates, coordinates
from commands import add, admin, get_player, join_arguments, name, alias
from pyspades.constants import *
 
jail_location = 0, 0, 0 # Location of game1
jail_coords = [] # e.g. ["B4", "B5"]
 
jail_list = []
 
@name('game')
@alias('g')
@admin
def game1_player(connection, value = None, *args):
    protocol = connection.protocol # Meh
    if not value:
        value=connection.name
    try:
        player = get_player(protocol, value) # Get player
    except Exception:
        return "Invalid player"
    else:
        if player.jailed:
            return 'Player ' + player.name + ' Already ingame!' # Player is already jailed!
        elif not player.jailed:
            player.jailed = True # Set player to jailed
            if not args:
                reason = player.reason = "no reason"
            else:
                reason = player.reason = join_arguments(*args)
            try:
                player.squad = None
                player.squad_pref = None
            except Exception:
                pass #if squads are not enabled
            player.set_location(jail_location) # Move player to jail
            connection.protocol.send_chat("%s has joined game 1!" % (player.name)) # Message
            connection.protocol.irc_say("* %s joined game 1" % (player.name)) # Message
            jail_list.append(player.name)
 
@name('game1')
def is_jailed(connection, value = None):
    if value is None:
        if not jail_list:
            return 'No players.'
        else:
            return " players: " + ", ".join(jail_list)
    elif value is not None:
        protocol = connection.protocol
        try:
            player = get_player(protocol, value or connection) # Get player
        except Exception:
            return "Invalid player"
        else:
            if player.jailed:
                return 'Player %s is playing game 1' % (player.name)
            else:
                return 'Player %s is not playing.' % (player.name)
@name('quit')
@admin
def quit_from_game(connection, value=None):
    protocol = connection.protocol # Meh
    if not value:
        value=connection.name
    try:
        player = get_player(protocol, value) # Get player
    except Exception:
        return "Invalid player"

    if player not in protocol.players:
        raise ValueError() # Errors again
    else:
        if not player.jailed: # If player isn't jailed
            return 'Player ' + player.name + ' is not ingame!' # Message
        elif player.jailed: # If player is jailed
            player.jailed = False # Player is not jailed anymore
            player.reason=None
            player.kill() # Kill the player
            connection.protocol.send_chat("%s quit the game 1" % (player.name)) # Message
            connection.protocol.irc_say('* %s has left game 1' % (player.name)) # Message
            jail_list.remove(player.name)

add(game1_player)
add(quit_from_game)
add(is_jailed)
def apply_script(protocol,connection,config):
    class GameOneConnection(connection):
        jailed=False
        reason=None
        def on_disconnect(self):
            if self.jailed:
                jail_list.remove(self.name)
                self.jailed = False
                return connection.on_disconnect(self)
    return protocol, GameOneConnection
