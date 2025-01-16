#PEACE script by Kuma
#This script is mainly aimed at build servers, has useful commands for building

#VERSION 2.4
#LOT OF STUFF ADDED

from commands import add, alias, admin, name, move
from twisted.internet.task import LoopingCall

PEACE_ENABLED_MESSAGE = "Peace mode has been enabled, Type /peacehelp for more information."
PEACE_DISABLED_MESSAGE = "Peace mode has been disabled."
NO_PEACE = "Peace mode is not enabled."
FLY_STRIPED = "All players were striped of their fly."
NO_GRENADE_MESSAGE = "Grenades won't do anything."

PEACE = True #Change this to False if you don't want peace from start
NO_GRENADE = True #Change this to False if you want grenades (Only for PEACE mode)

@alias('peace')
@admin
def peacemode(connection):
    global PEACE, strip
    protocol = connection.protocol
    PEACE = not PEACE
    if PEACE:
        protocol.send_chat(PEACE_ENABLED_MESSAGE)
    else:
        protocol.send_chat(PEACE_DISABLED_MESSAGE)
        strip_fly(connection)

@alias('sf')        
@admin
def strip_fly(connection):
    protocol = connection.protocol    
    for player in protocol.players.values():
        while(player.fly):
            player.fly = False
    connection.send_chat(FLY_STRIPED)

def peacehelp(connection):
    protocol = connection.protocol
    help = ["-" * 50,"Some of the commands are: /f, /ib, /gt","Players don't take fall damage or grenade damage","In peace mode, no player can be killed by a normal player", "-" * 50]
    if connection in protocol.players:
        for line in help:
            connection.send_chat(line)

@alias('f')
def peace_fly(connection):
    protocol = connection.protocol
    if PEACE:
        if connection in protocol.players:
            player = connection
            player.fly = not player.fly
            message = 'now flying' if player.fly else 'no longer flying'
            player.send_chat("You're {0}".format(message))
    else:
        connection.send_chat(NO_PEACE)

@alias('gt')
def peace_go_to(connection, value):
    if PEACE:
        protocol = connection.protocol
        if connection in protocol.players:
            move(connection, connection.name, value) #Imported from commands.py
    else:
        connection.send_chat(NO_PEACE)

@alias('ib') 
def peace_infi_blocks(connection):
    protocol = connection.protocol
    if PEACE:
        if connection in protocol.players:
            connection.infinite_blocks = not connection.infinite_blocks
            message = 'now in infinite blocks mode' if connection.infinite_blocks else 'not in infinite blocks mode'
            connection.send_chat("You're {0}".format(message))
    else:
        connection.send_chat(NO_PEACE)

@alias('ta')
def teleportall(connection, value = None):
    protocol = connection.protocol
    if not value is None and PEACE:
        for player in protocol.players.values():
            move(player, player.name, value, silent = True)
        protocol.send_chat("All players were teleported to {}".format(value))
      
add(peacemode)
add(peacehelp)
add(peace_fly)
add(peace_go_to)
add(peace_infi_blocks)
add(strip_fly)
add(teleportall)

def apply_script(protocol, connection, config):

    class peaceConnection(connection):
        infinite_blocks = False
        strip = False
        
        def on_block_build(self, x, y, z):
            if PEACE:
                if self.infinite_blocks:
                    self.refill()
                    return connection.on_block_build(self, x, y, z)
            return connection.on_block_build(self, x, y, z)

        def on_line_build(self, points):
            if PEACE:
                if self.infinite_blocks:
                    self.refill()
                    return connection.on_line_build(self, points)
            return connection.on_line_build(self, points)

        def on_hit(self, hit_amount, hit_player, type, grenade):
            if PEACE:
                return False
            return connection.on_hit(self, hit_amount, hit_player, type, grenade)

        def on_fall(self, damage):
            if PEACE:
                return False
            return connection.on_fall(self, damage)

        def grenade_exploded(self, grenade):
            if PEACE:
                if NO_GRENADE:
                    self.send_chat(NO_GRENADE_MESSAGE)
                    return False
            return connection.grenade_exploded(self, grenade)

    return protocol, peaceConnection
