# -*- coding: utf-8 -*-
"""
Advanced Battle Bot System

basicbot をもとに改造　20190130 yuyasato


"""




# BASIC BOTS

# fakes a connection and partially replicates player behavior
# 
# pathfinding was stripped out since it is unfinished and depended
# on the C++ navigation module
# 
# requires adding the 'local' attribute to server.py's ServerConnection
# 
# *** 201,206 ****
# --- 201,207 ----
#	   last_block = None
#	   map_data = None
#	   last_position_update = None
# +	 local = False
#	   
#	   def __init__(self, *arg, **kw):
#		   BaseConnection.__init__(self, *arg, **kw)
# *** 211,216 ****
# --- 212,219 ----
#		   self.rapids = SlidingWindow(RAPID_WINDOW_ENTRIES)
#	   
#	   def on_connect(self):
# +		 if self.local:
# +			 return
#		   if self.peer.eventData != self.protocol.version:
#			   self.disconnect(ERROR_WRONG_VERSION)
#			   return
# 
# bots should stare at you and pull the pin on a grenade when you get too close
# /addbot [amount] [green|blue]
# /toggleai

from math import cos, sin, floor
from random import uniform, randrange,gauss,random,choice,triangular
from enet import Address
from twisted.internet.reactor import seconds, callLater
from pyspades.protocol import BaseConnection
from pyspades.contained import BlockAction, SetColor,ChatMessage
from pyspades.server import input_data, weapon_input, set_tool, set_color, make_color
from pyspades.world import Grenade
from pyspades.common import Vertex3
from pyspades.collision import vector_collision
from pyspades.contained import *
from pyspades.server import *
from pyspades.common import *
from pyspades.constants import *

from commands import admin, add, name, get_team, alias
from pyspades import contained as loaders
from pyspades.packet import load_client_packet
from pyspades.bytes import ByteReader, ByteWriter

from math import floor,sin,cos,degrees,radians,atan2,acos,asin

LOGIC_FPS = 4.0
BOT_IN_BOTH=True
DEFAULT_BOT_NUM = 16
TARGET_POSITION_ASSIGNED = True
TOWmode = True

BOTMUTE = True

def bulletBlock(self, pos):
	x, y, z = pos

	set_color = SetColor()
	set_color.value = make_color(*self.color)
	set_color.player_id = self.player_id
	self.protocol.send_contained(set_color, save = True)
	
	block_action = BlockAction()
	block_action.x = x
	block_action.y = y
	block_action.z = z
	block_action.player_id = self.player_id
	def destroy():
		block_action.value = DESTROY_BLOCK
		self.protocol.send_contained(block_action, save = True)
		self.protocol.map.destroy_point(x, y, z)
	callLater(0.1, destroy)
	block_action.value = BUILD_BLOCK
	self.protocol.send_contained(block_action, save = True)
	self.protocol.map.set_point(x, y, z, self.color)

@admin
@name('addbot')		#BOT追加コマンド 例 : /addbot 5 green
def add_bot(connection, amount = None, team = None):
	protocol = connection.protocol
	if team:
		bot_team = get_team(connection, team)
	blue, green = protocol.blue_team, protocol.green_team
	amount = int(amount or 1)
	for i in xrange(amount):
		if not team:
			bot_team = blue if blue.count() < green.count() else green
		bot = protocol.add_bot(bot_team)
		if not bot:
			return "Added %s bot(s)" % i
	return "Added %s bot(s)" % amount

@admin
@name('botmute')		#BOTmute
def botmute(connection):
	global BOTMUTE
	BOTMUTE = not BOTMUTE
	return "BOTMUTE %s" % BOTMUTE

@admin
@name('toggleai')	#BOTのAIを停止・回復させるコマンド
def toggle_ai(connection):
	protocol = connection.protocol
	protocol.ai_enabled_GUN = not protocol.ai_enabled_GUN
	if not protocol.ai_enabled_GUN:
		for bot in protocol.bots_GUN:
			bot.flush_input()
	state = 'enabled' if protocol.ai_enabled_GUN else 'disabled'
	protocol.send_chat('AI %s!' % state)
	protocol.irc_say('* %s %s AI' % (connection.name, state))
	
@admin
@name('togglebotdamageglobal')  	#不明
@alias('tbdg')
def toggle_bot_damage_global(connection):
	protocol = connection.protocol
	protocol.bot_damage = not protocol.bot_damage
	state = 'enabled' if protocol.bot_damage else 'disabled'
	protocol.send_chat('Bot damage has been %s!' % state)
	protocol.irc_say('* %s %s bot damage' % (connection.name, state))

@admin
@name('nr')  	
@alias('nr')
def nr(connection):
	connection.protocol.add_bot_GUN(connection.team,connection,0)
	connection.protocol.add_bot_GUN(connection.team,connection,1)	
	return "called"

@admin
@name('togglebulletvisuals')	#BOTの銃弾の弾道がブロックで残る
@alias('tbv')
def toggle_bullet_visuals(connection):
	protocol = connection.protocol
	protocol.bullet_visual = not protocol.bullet_visual
	state = 'enabled' if protocol.bullet_visual else 'disabled'
	protocol.send_chat('Bullet visuals have been %s!' % state)
	protocol.irc_say('* %s %s bullet visuals' % (connection.name, state))
	
@admin
@name('botdamage')		#BOTの攻撃によるダメージを受けるか否か
@alias('bd')
def toggle_bot_damage(connection):
	connection.bot_damage_player = not connection.bot_damage_player
	state = 'now' if connection.bot_damage_player else 'no longer'
	connection.send_chat('You will %s take damage from bots!' % state)
@admin	
@name('refill')			#自分が回復
def practice_refill(connection):
	connection.refill()
	connection.send_chat("Refilled!")

add(add_bot)
add(toggle_ai)
add(toggle_bot_damage)
add(toggle_bot_damage_global)
add(toggle_bullet_visuals)
add(practice_refill)
add(botmute)
add(nr)

class LocalPeer:
	#address = Address(None, 0)
	address = Address('255.255.255.255', 0)
	roundTripTime = 0.0
	
	def send(self, *arg, **kw):
		pass
	
	def reset(self):
		pass


def apply_script(protocol, connection, config):
	class BotProtocol(protocol):
		bots_GUN = None
		ai_enabled_GUN = True
		
		def add_bot_GUN(self, team, parent = None, right = 2):
			if len(self.connections) + len(self.bots_GUN) >= 32:
				return None
			bot = self.connection_class(self, None)
			bot.parent = parent
			bot.right = right
			bot.join_game(team)

			self.bots_GUN.append(bot)
			return bot
		
		def on_world_update(self):
			if self.bots_GUN and self.ai_enabled_GUN:
				do_logic = self.loop_count % int(UPDATE_FPS / LOGIC_FPS) == 0
				for bot in self.bots_GUN:
					bot.update_GUN()
					
			protocol.on_world_update(self)
		
		def on_map_change(self, map):
			self.bots_GUN = []
			self.botbullets = []
			protocol.on_map_change(self, map)
		
		def on_map_leave(self):
			for bot in self.bots_GUN[:]:
				bot.disconnect()
			self.bots_GUN = None
			self.botbullets = None
			protocol.on_map_leave(self)
	
	class BotConnection(connection):
		has_intel = False
	
		aim = None
		aimOffset = None
		aim_at = None
		target_aim = None
		input = None
		acquire_targets = True
		
		damaged_block = []
		lastfire=0
		fire_right=False

		parent = None
		right = 2

		_turn_speed = None
		_turn_vector = None
		def _get_turn_speed(self):
			return self._turn_speed
		def _set_turn_speed(self, value):
			self._turn_speed = value
			self._turn_vector = Vertex3(cos(value), sin(value), 0.0)
		turn_speed = property(_get_turn_speed, _set_turn_speed)
		
		def __init__(self, protocol, peer):
			if peer is not None:
				return connection.__init__(self, protocol, peer)
			self.local = True
			connection.__init__(self, protocol, LocalPeer())
			self.on_connect()
			#~ self.saved_loaders = None
			self._send_connection_data()
			self.send_map()
			
			self.aim = Vertex3()
			self.target_aim = Vertex3()
			self.target_orientation = Vertex3()
			self.target_aim_final = Vertex3()
			self.turn_speed = 0.15 # rads per tick
			self.input = set()
			bot_damage_player = True
			
			self.color = (0xDF, 0x00, 0xDF)
			self.bot_set_color(self.color)
		
		def join_game(self, team):
			if self.parent:
				name = 'RR'
				self.name =  'GUN%s' % str(self.player_id)
				self.team = team
				self.set_weapon(RIFLE_WEAPON, True)
				self.aimOffset = (0,0,0)
				self.protocol.players[(self.name, self.player_id)] = self
				self.on_login(self.name)
				self.spawn()
			else:
				return connection.join_game(self, team)
		
		def disconnect(self, data = 0):
			if not self.local:
				return connection.disconnect(self)
			if self.disconnected:
				return
			if self.protocol.bots_GUN is not None:
				self.protocol.bots_GUN.remove(self)
			self.disconnected = True
			self.on_disconnect()


		def resend_tool(self):
			set_tool.player_id = self.player_id
			set_tool.value = self.tool
			self.protocol.send_contained(set_tool)
			self.send_contained(weapon_reload)
		
		def update_GUN(self):
			if self.parent and self.parent.world_object:
				if self.parent.hp<=0:
					self.disconnect()
				else:
					obj = self.world_object
					pos = obj.position
					ori = obj.orientation
					spos = self.parent.world_object.position.get()
					sori = self.parent.world_object.orientation.get()

					x_xy = sori[0]
					y_xy = sori[1]
					n_xy = (x_xy**2 + y_xy**2)**0.5
					x_xy /= n_xy
					y_xy /= n_xy

					if self.right ==1 : #right
						x, y ,z = spos[0]-y_xy-x_xy, spos[1]+x_xy-y_xy,  spos[2]
					elif self.right ==0 : #left
						x, y ,z  = spos[0]+y_xy-x_xy, spos[1]-x_xy-y_xy,  spos[2]

				
					self.world_object.set_position(x, y, z)						
					position_data.x = x
					position_data.y = y
					position_data.z = z
					self.send_contained(position_data)

					obj.set_orientation(*sori)
					self.aim.set_vector(obj.orientation)
					self.target_orientation.set_vector(self.aim)

					if self.parent.world_object.secondary_fire:
						self.input.add('primary_fire')
						if seconds() - self.parent.lastfire >0.06:
							if self.right == self.parent.fire_right:
								self.resend_tool()
								self.fire_weapon_GUN()

								self.parent.lastfire = seconds()
								self.parent.fire_right = not self.parent.fire_right
					self.flush_input_GUN()
			else:
				self.disconnect()




		
		def flush_input_GUN(self):
			input = self.input
			world_object = self.world_object
			z_vel = world_object.velocity.z
			if 'jump' in input and not (z_vel >= 0.0 and z_vel < 0.017):
				input.discard('jump')
			input_changed = not (
				('up' in input) == world_object.up and
				('down' in input) == world_object.down and
				('left' in input) == world_object.left and
				('right' in input) == world_object.right and
				('jump' in input) == world_object.jump and
				('crouch' in input) == world_object.crouch and
				('sneak' in input) == world_object.sneak and
				('sprint' in input) == world_object.sprint)
			if input_changed:
				if not self.freeze_animation:
					world_object.set_walk('up' in input, 'down' in input,
						'left' in input, 'right' in input)
					world_object.set_animation('jump' in input, 'crouch' in input,
						'sneak' in input, 'sprint' in input)
				if (not self.filter_visibility_data and
					not self.filter_animation_data):
					input_data.player_id = self.player_id
					input_data.up = world_object.up
					input_data.down = world_object.down
					input_data.left = world_object.left
					input_data.right = world_object.right
					input_data.jump = world_object.jump
					input_data.crouch = world_object.crouch
					input_data.sneak = world_object.sneak
					input_data.sprint = world_object.sprint
					self.protocol.send_contained(input_data)
			primary = 'primary_fire' in input
			secondary = 'secondary_fire' in input
			shoot_changed = not (
				primary == world_object.primary_fire and
				secondary == world_object.secondary_fire)
			if shoot_changed:
				if primary != world_object.primary_fire:
					if self.tool == WEAPON_TOOL:
						self.weapon_object.set_shoot(primary)
					if self.tool == WEAPON_TOOL or self.tool == SPADE_TOOL:
						self.on_shoot_set(primary)
				world_object.primary_fire = primary
				world_object.secondary_fire = secondary
				if not self.filter_visibility_data:
					weapon_input.player_id = self.player_id
					weapon_input.primary = primary
					weapon_input.secondary = secondary
					self.protocol.send_contained(weapon_input)
			input.clear()

		
		def bot_bullet_GUN(self):
			botpos = self.world_object.position.get()
			botori = self.world_object.orientation.get()
			if self.weapon == RIFLE_WEAPON:
				bure = 1
			elif self.weapon == SMG_WEAPON:
				bure = 2
			elif self.weapon == SHOTGUN_WEAPON:
				bure = 6
			theta = degrees(atan2(botori[1],botori[0]))
			phi = degrees(asin(botori[2]))
			V_bure = gauss(0,bure/2)
			H_bure = gauss(0,bure/2)
			oxy = cos(radians(phi+V_bure))

			ox = oxy*cos(radians(theta+H_bure))
			oy = oxy*sin(radians(theta+H_bure))
			oz = sin(radians(phi+V_bure))




			pos = [botpos[0],botpos[1],botpos[2]]
			ori = [ox,oy,oz]
			d_calc = 0.3 #bk

			for calc_do in xrange(int(128 / d_calc)):
				pos[0] += ori[0]*d_calc
				pos[1] += ori[1]*d_calc
				pos[2] += ori[2]*d_calc
				
				round_pos = (floor(pos[0]), floor(pos[1]), floor(pos[2]))
				_x,_y,_z = round_pos
				
				if _x > 511 or _x < 0 or _y > 511 or _y < 0 or _z > 62 or _z < -20:
					return None
				if _z >= 0:
					if self.protocol.map.get_solid(*round_pos): 
						return round_pos
				if self.team != None:
					for player in self.team.other.get_players():
						if vector_collision(Vertex3(*pos), player.world_object.position, 0.6):
							if self.weapon == RIFLE_WEAPON:
								dmg = 100
							elif self.weapon == SMG_WEAPON:
								dmg = 75
							elif self.weapon == SHOTGUN_WEAPON:
								dmg = 37
							if self.on_hit(dmg, player, HEADSHOT_KILL, None) != False:
								player.hit(dmg, self, HEADSHOT_KILL)
								return None

						elif vector_collision(Vertex3(pos[0],pos[1],pos[2]+0.6), player.world_object.position, 0.6) or vector_collision(Vertex3(pos[0],pos[1],pos[2]+0.9), player.world_object.position, 0.6) :
							if self.weapon == RIFLE_WEAPON:
								dmg = 49
							elif self.weapon == SMG_WEAPON:
								dmg = 29
							elif self.weapon == SHOTGUN_WEAPON:
								dmg = 26
							if self.on_hit(dmg, player, WEAPON_KILL, None) != False:
								player.hit(dmg, self, WEAPON_KILL)
								return None
						elif vector_collision(Vertex3(pos[0],pos[1],pos[2]+1.3), player.world_object.position, 0.6):
							if self.weapon == RIFLE_WEAPON:
								dmg = 33
							elif self.weapon == SMG_WEAPON:
								dmg = 18
							elif self.weapon == SHOTGUN_WEAPON:
								dmg = 16
							if self.on_hit(dmg, player, WEAPON_KILL, None) != False:
								player.hit(dmg, self, WEAPON_KILL)
								return None			

		def fire_weapon_GUN(self):
			if self:
				if self.world_object:
					if self.protocol.bot_damage == True:
						blkhit = self.bot_bullet_GUN()
						if blkhit:
							if blkhit in self.damaged_block:
								self.damaged_block.remove(blkhit)
								self.fire_block_break_GUN(*blkhit)
							else:
								self.damaged_block.append(blkhit)


		def fire_block_break_GUN(self,x,y,z):
			if not (0<=x<=511 and 0<=y<=511 and 0<=z<=60):
				return
			value = DESTROY_BLOCK
			map = self.protocol.map
			if not map.get_solid(x, y, z):
				return
			pos = self.world_object.position
			if self.on_block_destroy(x, y, z, value) == False:
				return
			if map.destroy_point(x, y, z):
				self.on_block_removed(x, y, z)
				block_action = BlockAction()
				block_action.x = x
				block_action.y = y
				block_action.z = z
				block_action.value = value
				block_action.player_id = self.player_id
				self.protocol.send_contained(block_action, save = True)
				self.protocol.update_entities()

		def on_kill(self, killer, type, grenade):
			if killer:
				if killer.parent:
					killer = killer.parent
			return connection.on_kill(self, killer, type, grenade)	

		def on_hit(self, damage, hitplayer, type, grenade):
			if self.local:
				if self.parent is not None:
					if hitplayer.team != self.team:
						hitplayer.hit(damage, self.parent, type)
			if hitplayer.local:
				if hitplayer.parent is not None:
					if hitplayer.team != self.team:
						hitplayer.parent.hit(damage, self, type)					
			return connection.on_hit(self, damage, hitplayer, type, grenade)	
	
		def on_spawn(self, pos):
			if not self.local:
				return connection.on_spawn(self, pos)
			if not self.parent:
				return connection.on_spawn(self, pos)
			
			self.world_object.set_orientation(0,0,1)
			self.aim.set_vector(self.world_object.orientation)
			self.target_orientation.set_vector(self.aim)
			self.set_tool(WEAPON_TOOL)
			self.aim_at = None
			self.jisatu=0
			self.damaged_block = []
			self.acquire_targets = True
			connection.on_spawn(self, pos)
			self.color = (0xDF, 0x00, 0xDF)
			self.bot_set_color(self.color) 
		
		def _send_connection_data(self):
			if self.local:
				if self.player_id is None:
					self.player_id = self.protocol.player_ids.pop()
				return
			connection._send_connection_data(self)
		
		def send_map(self, data = None):
			if self.local:
				self.on_join()
				return
			connection.send_map(self, data)
		
		def timer_received(self, value):
			if self.local:
				return
			connection.timer_received(self, value)
		
		def send_loader(self, loader, ack = False, byte = 0):
			if self.local:
				return
			return connection.send_loader(self, loader, ack, byte)
			



	return BotProtocol, BotConnection