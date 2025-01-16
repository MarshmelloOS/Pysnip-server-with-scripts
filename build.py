 
# Gamemode by thepolm3, influenced strongly by "strongblock" by hompy
from pyspades import world
from pyspades.constants import *
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from commands import add, admin, name, alias, get_player, join_arguments, InvalidPlayer
from collections import namedtuple
from pyspades.server import block_action, set_color
from pyspades.common import make_color
from pyspades.color import rgb_distance
from pyspades.constants import *
 
ON_GRENADE_THROW = "Grenades are disabled in this server."
ON_SHOOT_KILL = "Killing is disabled in this server."
ON_SPADE_KILL = "Killing is disabled in this server."
ON_GRENADE_KILL = "Grenades are disabled in this server."
ON_KILL = "Killing is disabled in BUILD gamemode."
ON_SUICIDE = "What a pity ! You got killed by yourself."
ON_FLAG_GET = "You can't get the intel; This is a BUILD server"
ON_BLOCK_DESTROY = "You can't destroy these blocks."
DIRT_COLOR = (71, 48, 35)
HIDE_STUFF = (0,0,63)
 
@name("ask")
def ask_for_block_permission(connection, player):
        try:
                # vanilla aos behavior
                subject = get_player(connection.protocol, '#' + player)
        except InvalidPlayer:
                subject = get_player(connection.protocol, player)
        if connection==subject:
                return "You are already allowed to break your own blocks!"
        subject.send_chat("to let him break your blocks.")
        subject.send_chat("to break you blocks. Do /allow %s" %(connection.name))
        subject.send_chat("%s is asking for permission" %(connection.name))
        return "Asked %s" %(subject.name)
 
@name("allow")
def allow_to_break_blocks(connection, player=None):
        try:
                # vanilla aos behavior
                subject = get_player(connection.protocol, '#' + player)
        except InvalidPlayer:
                subject = get_player(connection.protocol, player)
        if connection==subject:
                return "You are already allowed to break your own blocks!"
        strong_blocks=connection.protocol.strong_blocks
        for permission in strong_blocks:
                if strong_blocks[permission][0]==connection:
                        strong_blocks[permission].append(subject)
        connection.allowing.append(subject)
        subject.send_chat("%s has allowed you to break his blocks!" %(connection.name))
        return "%s can now break your blocks! Use /deny to stop them" %(subject.name)
 
@name("deny")
def stop_breaking_blocks(connection, player=None):
        try:
                # vanilla aos behavior
                subject = get_player(connection.protocol, '#' + player)
        except InvalidPlayer:
                subject = get_player(connection.protocol, player)
        if connection==subject:
                return "You cannot stop yourself breaking blocks!"
        strong_blocks=connection.protocol.strong_blocks
        for permission in strong_blocks:
                if strong_blocks[permission][0]==connection:
                        if subject in strong_blocks[permission]:
                                del(strong_blocks[subject])
        connection.allowing.pop(connection.allowing.index(subject))
        subject.send_chat("%s has stopped you to breaking his blocks!" %(connection.name))
        return "%s can no longer break your blocks!" %(subject.name)
 
 
def check_if_buried(protocol, x, y, z):
        if not protocol.map.is_surface(x, y, z):
                protocol.strong_blocks.pop((x, y, z), None)
 
def bury_adjacent(protocol, x, y, z):
        check_if_buried(protocol, x, y, z - 1)
        check_if_buried(protocol, x, y, z + 1)
        check_if_buried(protocol, x - 1, y, z)
        check_if_buried(protocol, x + 1, y, z)
        check_if_buried(protocol, x, y - 1, z)
        check_if_buried(protocol, x, y + 1, z)
 
def is_color_dirt(color):
        return rgb_distance(color, DIRT_COLOR) < 30
 
@alias('info')
def gamemodeinfo(connection):
        return'Server Running Gamemode : Build2 by ImChris'
 
@admin
def punish(connection, pl=None):
        if pl is not None:             
                pl = get_player(connection.protocol, pl)
                pl.punished = not pl.punished
                if pl.punished:
                        if pl.building:
                                pl.building = False
                        connection.protocol.send_chat("Player %s has been punished !" % pl.name, irc= True)
                else:
                        if not pl.building:
                                pl.building = True
                        connection.protocol.send_chat("Player %s has been forgiven !" % pl.name, irc= True)
        else:
                return "This player doesn't exists"
               
@alias('ba')           
@admin
def breakall(self, pl=None):
        msg = ("You allowed %s to break everyone's blocks" , "You has been allowed to break everyone's blocks", "You disallowed %s to break everyone's blocks", "You can no longer break everyone's blocks")
        if pl is None :
                pl = self
        else:                  
                pl = get_player(self.protocol, pl)

        pl.break_all = not pl.break_all
        if pl.break_all:
                self.send_chat(msg[0], pl.name)
                pl.send_chat(msg[1])
        else:
                self.send_chat(msg[2], pl.name)
                pl.send_chat(msg[3])

add(ask_for_block_permission)
add(allow_to_break_blocks)
add(stop_breaking_blocks)
add(gamemodeinfo)
add(punish)
add(breakall)
 
def apply_script(protocol, connection, config):
        class buildConnection(connection):
       
                punished = False
                break_all = False
                allowing=[]
                fly = True
                painting = False
                rapid = False
               
                def on_connect(self):
                        self.allowing=[self]
                        return connection.on_connect(self)
                       
                def on_grenade(self, time_left):
                        self.send_chat(ON_GRENADE_THROW)
                        return False
               
                def on_hit(self, hit_amount, hit_player, type, grenade):
                        if self.tool == SPADE_TOOL:
                                self.send_chat(ON_SPADE_KILL)
                        if self.tool == WEAPON_TOOL:
                                self.send_chat(ON_SHOOT_KILL)
                        if self.tool == GRENADE_TOOL:
                                self.send_chat(ON_GRENADE_KILL)
                        return False
               
                def on_kill(self, killer, type, grenade):
                        if killer:
                                killer.send_chat(ON_KILL)
                                return False
                        else:
                                self.send_chat(ON_SUICIDE)
                                return connection.on_kill(self, killer, type, grenade)
               
                def on_block_build(self, x, y, z):
                        self.refill()
                        if not is_color_dirt(self.color):
                                self.protocol.strong_blocks[str((x,y,z))] = self.allowing
                                bury_adjacent(self.protocol, x, y, z)
                        connection.on_block_build(self, x, y, z)
               
                def on_line_build(self, points):
                        self.refill()
                        if not is_color_dirt(self.color):
                                for xyz in points:
                                        self.protocol.strong_blocks[str((xyz))] = self.allowing
                                        bury_adjacent(self.protocol, *xyz)
                        connection.on_line_build(self, points)
 
                def on_flag_take(self):
                        self.send_chat(ON_FLAG_GET)
                        return False
               
                def on_block_destroy(self, x, y, z, value):
                        self.refill()
                        try:
                                strong_block = self.protocol.strong_blocks[str((x,y,z))]
                        except KeyError:
                                return connection.on_block_destroy(self, x, y, z, value)
                        if strong_block:
                                if self in strong_block:
                                        del(self.protocol.strong_blocks[str((x,y,z))])
                                elif self.break_all:
                                        del(self.protocol.strong_blocks[str((x,y,z))])
                                elif self.admin:
                                        del(self.protocol.strong_blocks[str((x,y,z))])
                                elif strong_block[0].name is None:
                                        del(self.protocol.strong_blocks[str((x,y,z))])
                                else:                          
                                        self.send_chat("Do /ask %s to gain access to his blocks" %(strong_block[0].name))
                                        self.send_chat(ON_BLOCK_DESTROY)
                                        return False
                        return connection.on_block_destroy(self, x, y, z, value)
                       
        class buildProtocol(protocol):
                game_mode=CTF_MODE
                strong_blocks = None
               
                def get_entity_location(team, entity_id):
                        if entity_id == GREEN_FLAG:
                                return (HIDE_STUFF)
                        if entity_id == BLUE_FLAG:
                                return (HIDE_STUFF)
                        if entity_id == GREEN_BASE:
                                return (HIDE_STUFF)
                        if entity_id == BLUE_BASE:
                                return (HIDE_STUFF)
               
                def on_map_change(self, map):
                        self.strong_blocks = {}
                        protocol.on_map_change(self, map)
 
        return buildProtocol, buildConnection
