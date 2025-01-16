"""
infiniclip lets player have an infinite clip. 

Written by Leif_The_Head
"""

from pyspades.constants import *
from pyspades.server import weapon_reload
from commands import add, admin, name, get_player, alias
import commands

ALWAYS_INFINITE = False

I_START_MESSAGE_OP = "{playe} has now an infinite clip"
I_START_MESSAGE_PLAYER = "You gained an infinite clip"
I_STOP_MESSAGE_OP = "{playe} returns to standard clip size"
I_STOP_MESSAGE_PLAYER = "You lost your infinite clip, too bad!"

@name('infiniteclip')
@alias('ic')
@admin
def toggle_inf(connection, player = None):
    protocol = connection.protocol
    if player is not None:
        player = get_player(protocol, player)
    elif connection in protocol.players:
        player = connection
    else:
        raise ValueError()
    
    player.infinite = infinite = not player.infinite
    
    if infinite:
        player.send_chat(I_START_MESSAGE_PLAYER)
        message = I_START_MESSAGE_OP.format(playe = player.name)
    else:
        player.send_chat(I_STOP_MESSAGE_PLAYER)
        message = I_STOP_MESSAGE_OP.format(playe = player.name)
    return message
    protocol.irc_say('* ' + message)
add(toggle_inf) 

def apply_script(protocol, connection, config):
    class InfiConnection(connection):
        infinite = False
        infinite_loop = None
        
        def on_login(self, name):
            self.infinite = ALWAYS_INFINITE
            connection.on_login(self, name)
        
        def on_disconnect(self):
            self.infinite = False
            connection.on_disconnect(self)
        
        def on_shoot_set(self, fire):
            if self.infinite:
                weapon = self.weapon_object
                was_shooting = weapon.shoot
                weapon.reset()
                weapon_reload.player_id = self.player_id
                weapon_reload.clip_ammo = 1337
                weapon_reload.reserve_ammo = 666
                weapon.set_shoot(was_shooting)
                self.send_contained(weapon_reload)
            connection.on_shoot_set(self, fire)
    
    return protocol, InfiConnection