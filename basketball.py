#-*-coding:utf-8-*-
"""
Basketball
This script is for Basketball game

COMMANDS
    /makegoal
        Start making goal by hitting blocks

    /savegoal
        Record the deta of goals

USAGE
    How to change coat size
        Rewrite the map-meta-deta [map name]_goal.txt
        'north_edge' and 'south_edge' mean coat size

    How to change spawn location
        Rewrite the map-meta-deta [map name]_goal.txt
        'blue_spawn_pos' and 'green_spawn_pos' mean spawn location
"""


import __builtin__
import json
import os
from pyspades.constants import *
from pyspades.contained import BlockAction
from pyspades.server import block_action, orientation_data, grenade_packet, weapon_reload, set_tool, create_player
from pyspades.common import Vertex3, coordinates
from pyspades import world
from pyspades.world import Grenade
from commands import add, admin, name, alias, join_arguments
from twisted.internet.reactor import callLater, seconds
from collections import defaultdict
from map import DEFAULT_LOAD_DIR


CENTER = (256, 256)

HIDE_POS = (0, 0, 63)


#The function to check if the player has the intel
def checkHolder(flag, holder):	#holder is the player
    if flag.player == holder:
        return True		#If holder has the Intel, return 1
    else:
        return False		#If holder doesn't has the Intel, return 0

#This function is from Football.py
#This function change the team of player who do owngoal
def fill_create_player(player, team):			#team is player's new team
    x, y, z = player.world_object.position.get()
    create_player.x = x
    create_player.y = y
    create_player.z = z
    create_player.name = player.name
    create_player.player_id = player.player_id
    create_player.weapon = player.weapon
    create_player.team = team.id


#function to save goal deta
@admin
def savegoal(connection):
     connection.protocol.dump_goal_json()
     connection.send_chat("!!GOAL SAVED!!")
     return
add(savegoal)




#function to make goal
@admin
def makegoal(*arguments):
    connection = arguments[0]
    connection.reset_build()
    if connection.goal_making:
        connection.send_chat('Making goal is canceled')
    else:
        param = len(arguments)
        if param < 2:
            connection.send_chat('b = blue, g = green, n = neutral')
            connection.send_chat('Enter team')
            return False
        connection.arguments = arguments
        connection.send_chat('Hit 2 blocks to set goal area')
    connection.goal_making = not connection.goal_making
add(makegoal)


#Setting of goal
#In this class "self" means goal itself
class GoalObject:
    id = None
    label = None
    teamname = None

    #Initialize the goal
    def __init__(self, id_n, belong_team, x1, x2, y1, y2, z1, z2):
        self.id = id_n
        self.label = str(self.id)
        self.teamname = belong_team
        self.west = x1
        self.east = x2
        self.north = y1
        self.south = y2
        self.top = z1
        self.botom = z2


    #Check if the goal(self) contains given position(x, y, z)
    def contains(self, x, y, z):
        if self.west <= x and self.east >= x:
            if self.north <= y and self.south >= y:
                if self.top <= z and self.botom >= z:
                    return True
        return False

    #Check the goal's team
    def get_team(self):
        return self.teamname

    def serialize(self):
        return {
            'id' : self.id,
            'label' : self.label,
            'team' : self.teamname,
            'xpos' : (self.west, self.east),
            'ypos' : (self.north, self.south),
            'zpos' : (self.top, self.botom)
        }


#This is main body of this script
def apply_script(protocol, connection, config):
    
    
    #Protocol means the setting of server
    #In Protocol "self" means the server itself
    class BasketBallProtocol(protocol):
        coat_edge_u = None
        coat_edge_d = None
        highest_id = None
        goals = None
        goal_json_dirty = False
        autosave_loop = None
        callback = None
        blue_spawn_pos = None
        green_spawn_pos = None

        #Setting of game beginning
        def on_map_change(self, map):
            self.flag_spawn_pos = CENTER			#Intel possition is center
            self.mode_throwin = False				#Init throwing setting
            self.throwin_team = None				#Init throwing team setting
            self.highest_id = -1
            self.goals = {}
            self.goal_json_dirty = False
            self.load_goal_json()				#load_goal_json()
            if not self.coat_edge_u:
                self.coat_edge_u = 240
                self.coat_edge_d = 271
            if not self.blue_spawn_pos:
                self.blue_team.spawn_pos = (231, 255, 60)
                self.green_team.spawn_pos = (280, 256, 60)
            else:
                self.blue_team.spawn_pos = self.blue_spawn_pos
                self.green_team.spawn_pos = self.green_spawn_pos
            return protocol.on_map_change(self, map)


        #This make Intel to spawn
        def bsk_flag_spawn(self, flag):
            z = self.map.get_z(self.flag_spawn_pos[0], self.flag_spawn_pos[1], 60)
            pos = (self.flag_spawn_pos[0], self.flag_spawn_pos[1], z)
            if flag is not None:
                flag.player = None
                flag.set(*pos)
                flag.update()
            return pos

        #This make the rocation of intel the same
        def bsk_reset_flags(self):
            self.bsk_flag_spawn(self.blue_team.flag)
            self.bsk_flag_spawn(self.green_team.flag)

        #Setting of game ending
        def on_game_end(self):
            self.flag_spawn_pos = CENTER
            self.bsk_reset_flags()
            return protocol.on_game_end(self)

        #Setting on flag spawning
        def on_flag_spawn(self, x, y, z, flag, entity_id):
            pos = self.bsk_flag_spawn(flag.team.other.flag)				#Get the rocation of the Intel
            protocol.on_flag_spawn(self, pos[0], pos[1], pos[2], flag, entity_id)	#Spawn the other in same rocation
            return pos

        #Setting of Illumination on goal successed
        def fog_flash(self, color):
            old_color = self.get_fog_color()			#Log the natural color of fog
            self.set_fog_color(color)				#Change the fog color to winning team color
            callLater(0.2, self.set_fog_color, old_color)	#Return the color to nature after 0.2sec


        #Set filename to save-load goal deta
        def get_goal_json_path(self):
            filename = self.map_info.rot_info.full_name + '_goal.txt'
            return os.path.join(DEFAULT_LOAD_DIR, filename)


        #Load goal data from map-metadata
        def load_goal_json(self):
            path = self.get_goal_json_path()
            if not os.path.isfile(path):
                return
            with open(path, 'r') as file:		#'r' means 'open file for Reading'
                data = json.load(file)
            ids =[]
            for goal_data in data['goals']:
                x1, x2 = goal_data['xpos']
                y1, y2 = goal_data['ypos']
                z1, z2 = goal_data['zpos']
                id = goal_data['id']
                teamname = goal_data['team']
                ids.append(id)
                goal = GoalObject(id, teamname, x1, x2, y1, y2, z1, z2)
                goal.label = goal_data['label']
                self.goals[id] = goal
            self.coat_edge_u = data['north_edge']
            self.coat_edge_d = data['south_edge']
            self.blue_spawn_pos = data['blue_spawn_pos']
            self.green_spawn_pos = data['green_spawn_pos']
            ids.sort()
            self.highest_id = ids[-1] if ids else -1
            self.goal_json_dirty = True					#goal_json_dirty

        def dump_goal_json(self):
            if(not self.goals and not self.goal_json_dirty):			#goal_json_dirty
                return
            data = {
                'goals' : [goal.serialize() for goal in self.goals.values()],	#serialize, values()
                'north_edge' : self.coat_edge_u,
                'south_edge' : self.coat_edge_d,
                'blue_spawn_pos' : self.blue_team.spawn_pos,
                'green_spawn_pos' : self.green_team.spawn_pos
            }
            path = self.get_goal_json_path()
            with open (path, 'w') as file:		#'w' means 'open file for Writing'
                json.dump(data, file, indent = 4)
            self.goal_json_dirty = True

        def is_goal(self, x, y, z):
            for goal in self.goals.itervalues():
                if goal.contains(x, y, z):
                    return goal
            return None


    #Connection means the setting of player action
    #In Connection "self" means the player
    class BasketBallConnection(connection):
        goal_making = False
        have_ball = False


        def reset_build(self):
            self.block1_x = None
            self.block1_y = None
            self.block1_z = None
            self.block2_x = None
            self.block2_y = None
            self.block2_z = None
            self.block3_x = None
            self.block3_y = None
            self.block3_z = None
            self.arguments = None
            self.callback = None
            self.select = False
            self.points = None
            self.label = None


        #This works when a player(=self) get the goal
        def goal_successed(self, teamname):				#goal_team is the team which lost the goal
            if teamname == 'blue':
                goal_team = self.protocol.blue_team
            elif teamname == 'green':
                goal_team = self.protocol.green_team
            else:
                goal_team = self.team.other
            old_team = self.team
            if self.team is goal_team:					#If owngoal
                self.drop_flag()
                self.send_chat('!!OWN GOAL!!')
                self.team = goal_team.other
                fill_create_player(self, self.team)				#Change his team
                self.protocol.send_contained(create_player, save = True)
                self.take_flag()
            goal_team.flag.player = self
            self.capture_flag()
            if old_team is goal_team:						#If his team is changed
                self.team = old_team
                fill_create_player(self, self.team)				#Return to original team
                self.protocol.send_contained(create_player, save = True)
            flash_color = goal_team.other.color				#Log the winning team color
            self.protocol.fog_flash(flash_color)				#Illumination
            callLater(0.5, self.protocol.fog_flash, flash_color)		#Illumination again after 0.4sec
            callLater(0.9, self.protocol.fog_flash, flash_color)		#Illumination third time after 0.8sec

        #This works when a player(=self) get the Intel
        def on_flag_take(self):
            if self.protocol.mode_throwin and self.protocol.throwin_team is not self.team:
                return False				#If enemy's throwing is going on, return 0(don't allow to take Intel)
            else:
                flag = self.team.flag
                if flag.player is None:
                    flag.set(*HIDE_POS)			#Hide the other Intel to HIDEPOS
                    flag.update()
                else:
                    return False
                self.refill()				#Fill his items when he get the Intel
                self.have_ball = True
                return connection.on_flag_take(self)	#Contenue on_flag_take()

        #This works when a player(=self) drop the Intel
        def on_flag_drop(self):
            flag = self.team.other.flag
            position = self.protocol.flag_spawn_pos
            x = position[0]
            y = position[1]
            z = self.protocol.map.get_z(x, y, 60)	#Get the ground height
            flag.set(x, y, z)				#Spawn enemy Intel
            flag.update()
            flag = self.team.flag
            flag.set(x, y, z)				#Spawn the other Intel on same possition to enemy Intel
            flag.update()
            self.have_ball = False
            return connection.on_flag_drop(self)	#Contenue on_flag_drop()
        
        
        #This works when a player destroy blocks 
        def on_block_destroy(self, x, y, z, mode):
            if self.god:
                if self.goal_making:
                    if self.block1_x == None:
                        self.block1_x = x
                        self.block1_y = y
                        self.block1_z = z
                        self.send_chat('first block was selected')
                    else:
                        if self.block1_x > x:
                            x1 = x
                            x2 = self.block1_x
                        else:
                            x1 = self.block1_x
                            x2 = x
                        if self.block1_y > y:
                            y1 = y
                            y2 = self.block1_y
                        else:
                            y1 = self.block1_y
                            y2 = y
                        if self.block1_z > z:
                            z1 = z
                            z2 = self.block1_z
                        else:
                            z1 = self.block1_z
                            z2 = z
                        self.protocol.highest_id += 1
                        id = self.protocol.highest_id
                        teamname = self.arguments[1]
                        if teamname == 'b' or teamname == 'blue':
                            belong_team = 'blue'
                        elif teamname == 'g' or teamname == 'green':
                            belong_team = 'green'
                        else:
                            belong_team = 'neutral'
                        goal = GoalObject(id, belong_team, x1, x2, y1, y2, z1, z2)
                        self.protocol.goals[id] = goal
                        self.goal_making = False
                        self.send_chat('goal was created')
                    return False
                else:
                    return connection.on_block_destroy(self, x, y, z, mode)
            else:
                if mode == GRENADE_DESTROY:
                    flag = self.team.other.flag
                    if checkHolder(flag, self):
                        self.protocol.flag_spawn_pos = (x, y, z)
                        goal = self.protocol.is_goal(x, y, z)
                        if goal:
                            self.goal_successed(goal.teamname)
                        if y <= self.protocol.coat_edge_u or y >= self.protocol.coat_edge_d:
                            self.protocol.mode_throwin = True
                            self.protocol.throwin_team = self.team.other
                            self.protocol.send_chat('THROW IN!!', global_message = True)
                        else:
                            self.protocol.mode_throwin = False
                        self.drop_flag()
                        self.have_ball = False
                return False
        
        
        def on_grenade_thrown(self, grenade):
            self.have_ball = False
            return connection.on_grenade_thrown(self, grenade)
        
        def on_block_build_attempt(self, x, y, z):
            if self.god:
                return connection.on_block_build_attempt(self, x, y, z)
            else:
                return False

        
        def on_line_build_attempt(self, points):
            if self.god:
                return connection.on_line_build_attempt(self, points)
            else:
                return False
        
        
        #This works when a player damage another player
        #In basketball this works for ball-tossing or ball-robbing
        def on_hit(self, hit_amount, hit_player, type, grenade):
            if type == MELEE_KILL and self.team != hit_player.team:
                if self.protocol.mode_throwin:
                    self.send_chat('!!Now on throw in!!')
                else:
                    flag = self.team.flag
                    if hit_player.have_ball:
                        hit_player.drop_flag()
                        hit_player.have_ball = False
                        self.take_flag()
                        self.have_ball = True
                        flag.set(*HIDE_POS)
                        flag.update()
            elif type == WEAPON_KILL or type == HEADSHOT_KILL:
                self.protocol.mode_throwin = False
                if self.team == hit_player.team:
                    flag = self.team.other.flag
                    if self.have_ball:
                        self.drop_flag()
                        self.have_ball = False
                        hit_player.take_flag()
                        hit_player.have_ball = True
                elif self.team != hit_player.team:
                    flag = hit_player.team.flag
                    if self.have_ball:
                        self.drop_flag()
                        self.have_ball = False
                        hit_player.take_flag()
                        hit_player.have_ball = True
                        flag.set(*HIDE_POS)
                        flag.update()
            return False
        
        def on_spawn_location(self, pos):
            return self.team.spawn_pos
        
        #This works when the player walks or crouch
        #In basketball when a Intel-holder go out the coat, penalty is given
        def on_position_update(self):
            flag = self.team.other.flag
            if self.have_ball:
                x, y, z = self.world_object.position.get()
                pos = (x, y, z)
                if not self.protocol.mode_throwin:
                    if y <= self.protocol.coat_edge_u or y >= self.protocol.coat_edge_d:
                        self.protocol.flag_spawn_pos = pos
                        self.drop_flag()
                        self.have_ball = False
                        self.kill(self, MELEE_KILL)
                        self.protocol.mode_throwin = True
                        self.protocol.throwin_team = self.team.other
                        self.protocol.send_chat('THROW IN!!', global_message = True)
                else:
                    if y > self.protocol.coat_edge_u and y < self.protocol.coat_edge_d:
                        if y < 256:
                            dy = self.protocol.coat_edge_u - 1
                        else:
                            dy = self.protocol.coat_edge_d + 1
                        self.protocol.flag_spawn_pos = (x, dy, z)
                        self.drop_flag()
                        self.have_ball = False
                        self.kill(self, MELEE_KILL)
                        self.protocol.mode_throwin = True
                        self.protocol.throwin_team = self.team.other
                        self.protocol.send_chat('THROW IN!!', global_message = True)
                        
    
    
    return BasketBallProtocol, BasketBallConnection