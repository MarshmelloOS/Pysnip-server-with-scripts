# -*- coding: utf-8 -*-
"""
どっかの外人さんの作った頭が良くて銃撃ってきてよけたり動いたりするボット
訳：yuyasato


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
from random import uniform, randrange,gauss,random,choice
from enet import Address
from twisted.internet.reactor import seconds, callLater
from pyspades.protocol import BaseConnection
from pyspades.contained import BlockAction, SetColor
from pyspades.server import input_data, weapon_input, set_tool, set_color, make_color
from pyspades.world import Grenade
from pyspades.common import Vertex3
from pyspades.collision import vector_collision
from pyspades.constants import *
from commands import admin, add, name, get_team, alias
from math import floor,sin,cos,degrees,radians,atan2,acos,asin

LOGIC_FPS = 4.0

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
@name('toggleai')	#BOTのAIを停止・回復させるコマンド
def toggle_ai(connection):
	protocol = connection.protocol
	protocol.ai_enabled = not protocol.ai_enabled
	if not protocol.ai_enabled:
		for bot in protocol.bots:
			bot.flush_input()
	state = 'enabled' if protocol.ai_enabled else 'disabled'
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

class LocalPeer:
	#address = Address(None, 0)
	address = Address('255.255.255.255', 0)
	roundTripTime = 0.0
	
	def send(self, *arg, **kw):
		pass
	
	def reset(self):
		pass
		
class Bullet:					#ボットの放つ弾丸を計算する部分
	orientation = None
	position = (0, 0, 0)
	connection = None
	protocol = None
	
	def __init__(self, player):
		self.orientation = player.world_object.orientation.get()
		self.position = list(player.get_location())
		self.connection = player
		self.protocol = player.protocol
		self.protocol.botbullets.append(self)
		print "bullet", self.orientation
		
	def update(self):
		if self.connection == None:
			return False
		
		self.position[0] += self.orientation[0]*0.3
		self.position[1] += self.orientation[1]*0.3
		self.position[2] += self.orientation[2]*0.3
		
		round_pos = (floor(self.position[0]), floor(self.position[1]), floor(self.position[2]))
		_x,_y,_z = round_pos
		
		if self.connection.world_object != None:
			connectionpos = self.connection.get_location()
			if abs(self.position[0] - connectionpos[0]) > 120.0 or abs(self.position[1] - connectionpos[1]) > 120.0 or abs(self.position[2] - connectionpos[2]) > 120.0:
				return False
		
		if _x > 510 or _x < 1 or _y > 510 or _y < 1 or _z > 63 or _z < 1:
			return False
		if self.protocol.map.get_solid(*round_pos):
			return False

		if self.connection.team != None:
			for player in self.connection.team.other.get_players():
				player_pos_pz1 = (floor(player.world_object.position.x),floor(player.world_object.position.y),floor(player.world_object.position.z)+1)
				player_pos = (floor(player.world_object.position.x),floor(player.world_object.position.y),floor(player.world_object.position.z))
			#	if vector_collision(Vertex3(*self.position), player.world_object.position, 0.6):
			#		print "vector_collision head"
			#	elif vector_collision(Vertex3(self.position[0],self.position[1],self.position[2]+0.6), player.world_object.position, 0.6) or vector_collision(Vertex3(self.position[0],self.position[1],self.position[2]+0.9), player.world_object.position, 0.6) :
			#		print "vector_collision body"
			#	elif vector_collision(Vertex3(self.position[0],self.position[1],self.position[2]+1.3), player.world_object.position, 0.6):
			#		print "vector_collision asi"
				if round_pos == player_pos: # headshot
						print "headshot"
					#if self.connection.on_hit(100, player, HEADSHOT_KILL, None) != False:
					#	player.hit(100, self.connection, HEADSHOT_KILL)
						return False
				elif round_pos == player_pos_pz1: #body shot
						print "bodyshot"
					#if self.connection.on_hit(49, player, WEAPON_KILL, None) != False:
					#	player.hit(49, self.connection, WEAPON_KILL)
						return False
			if floor(player.world_object.position.x) == _x:
				print "bullet ps",player.world_object.position

		if self.protocol.bullet_visual:			
			bulletBlock(self.connection, round_pos)		#弾道をブロックで表示する部分
		
		return True	


def apply_script(protocol, connection, config):
	class BotProtocol(protocol):
		bots = None
		botbullets = None
		ai_enabled = True
		bot_damage = True
		bullet_visual = False
		
		def add_bot(self, team):
			if len(self.connections) + len(self.bots) >= 32:
				return None
			bot = self.connection_class(self, None)
			bot.join_game(team)
			self.bots.append(bot)
			return bot
		
		def on_world_update(self):
			if self.bots and self.ai_enabled:
				do_logic = self.loop_count % int(UPDATE_FPS / LOGIC_FPS) == 0
				for bot in self.bots:
					if do_logic:
						bot.think()
					bot.update()
			if self.botbullets:
				for bullet in self.botbullets[::-1]:
					if not bullet.update():
						self.botbullets.remove(bullet)
					
			protocol.on_world_update(self)
		
		def on_map_change(self, map):
			self.bots = []
			self.botbullets = []
			protocol.on_map_change(self, map)
		
		def on_map_leave(self):
			for bot in self.bots[:]:
				bot.disconnect()
			self.bots = None
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
		player_pinkblock = False
		bot_pinkblock_changed = False
		last_pos = (0,0,0)
		player_firing = None
		fire_call = None
		botfindtimer = None
		bot_jump = None
		bot_forceaimat = None
		cpulevel=1
		bot_damage_player = True
		jumptime=0
		xoff=0
		yoff=0
		vel=0
		xt,yt,zt=0,0,0
		dis=255
		jisatu=0
		digtime=0
		ikeru=[0,0,0,0]
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
			name = 'The Zero'
			if self.player_id==1:
				name = 'Itti'
			if self.player_id==2:
				name = 'Huta'
			if self.player_id==3:
				name = 'Mii'
			if self.player_id==4:
				name = 'SISI'
			if self.player_id==5:
				name = 'Go is God'
			if self.player_id==6:
				name = 'rock'
			if self.player_id==7:
				name = '007'
			if self.player_id==8:
				name = 'hatti'
			if self.player_id==9:
				name = 'Qtaro-'
			if self.player_id==10:
				name = 'A-10'
			if self.player_id==11:
				name = 'yutasaito'
			if self.player_id==12:
				name = 'nekomimi'
			if self.player_id==13:
				name = 'golgo13'
			if self.player_id==14:
				name = 'simesaba'
			if self.player_id==15:
				name = 'OMUSUBI'
			if self.player_id==16:
				name = 'kikumon*'
			if self.player_id==17:
				name = 'jhon'
			if self.player_id==18:
				name = 'bipei'
			if self.player_id==19:
				name = 'otimpo'
			if self.player_id==20:
				name = 'aeria'
			if self.player_id==21:
				name = 'gapoi'
			if self.player_id==22:
				name = 'niwaka'
			if self.player_id==23:
				name = 'moukin'
			if self.player_id==24:
				name = 'isitubute'
			if self.player_id==25:
				name = 'nijugorou'
			if self.player_id==26:
				name = 'yujikato'
			if self.player_id==27:
				name = 'nubou'
			if self.player_id==28:
				name = 'tako'
			if self.player_id==29:
				name = 'oniku'
			if self.player_id==30:
				name = 'sanju-'
			if self.player_id==31:
				name = 'sa-ti-wan'
			if self.player_id==32:
				name = 'The LAst'
			if self.player_id==33:
				name = 'GOD_EXIST'

			while True:
				self.cpulevel=random()
				if 0.8>self.cpulevel:
					break

			self.name = 'BOT%s [LV.%s]' % (str(self.player_id), str(int(self.cpulevel*99)))	#'%s %s' % (name,str(self.player_id + 1))
			self.team = team
			if random()>0:#0.8:
				self.set_weapon(RIFLE_WEAPON, True)
			else:
				self.set_weapon(SHOTGUN_WEAPON, True)
			self.aimOffset = (0,0,0)#(uniform(-0.4, 0.4), uniform(-0.4, 0.4), 0)
			self.protocol.players[(self.name, self.player_id)] = self
			self.on_login(self.name)
			self.spawn()
		
		def disconnect(self, data = 0):
			if not self.local:
				return connection.disconnect(self)
			if self.disconnected:
				return
			self.protocol.bots.remove(self)
			self.disconnected = True
			self.on_disconnect()
		
		def find_nearest_player(self):
			if self.bot_forceaimat != None:
				return
				
			self.botfindtimer = None
			obj = self.world_object
			if not obj:
				return
			pos = obj.position
			player_distances = []
			
			for player in self.team.other.get_players():
				if vector_collision(pos, player.world_object.position, 60+ self.cpulevel*65):
					if player.world_object.can_see(*pos.get()):
						ex,ey,ez = player.world_object.position.get()
						px,py,pz = pos.get()
						ox,oy,oz = obj.orientation.get()
						nx,ny,nz = ex-px, ey-py, ez-pz
						dist = (nx**2+ny**2+nz**2)**0.5
						nx/=dist
						ny/=dist
						nz/=dist
						naiseki = nx*ox + ny*oy + nz*oz
						if naiseki>1:
							naiseki=1
						if naiseki<-1:
							naiseki=-1
						nasukaku = degrees(acos(naiseki))
						if max(self.cpulevel*100,20)>nasukaku:
							player_distances.append(((player.world_object.position - pos), player))
			
			if len(player_distances) > 0:
				nearestindex = min(range(len(player_distances)), key=lambda i: abs(player_distances[i][0].length_sqr()))
				self.aim_at = player_distances[nearestindex][1]
			else:
				self.aim_at = None
		
		def think(self):
			obj = self.world_object
			pos = obj.position
			
			# find nearby foes
			if self.acquire_targets:
				if self.botfindtimer == None:
					self.botfindtimer = callLater(max(3-(self.cpulevel*3)+gauss(0,0.7),0), self.find_nearest_player) #敵が認知界に入った時に、気づくまでの時間
			
			# replicate player functionality
		
		def bot_jumpfunc(self, a = None,b = None):
			if self.world_object.velocity.z**2>0.001:
				self.bot_jump = None
				self.input.add('jump')
				if random() < 0.03:
					self.input.add('crouch')
				self.player_firing = callLater(0.3, self.player_stopfiring)	
		
		def bot_pinkblock_crouch(self):
			def uncrouch():
				self.player_firing = None
			if self.player_firing == None:
				self.player_firing = callLater(uniform(0.1, 0.4), uncrouch)

		def cast_sensor(self,SENSOR_LENGTH,x,y,z):
			self.world_object.set_orientation(x,y,z)				
			dist = self.world_object.cast_ray(SENSOR_LENGTH)
			if dist is not None:
				dist = self.distance_calc(dist,self.world_object.position.get())
			else:
				dist=0
			return dist		
		
		def update(self):
			obj = self.world_object
			pos = obj.position
			ori = obj.orientation
			spade_using =False
			dis=255
			obj.set_orientation(*ori.get())
			self.flush_input()
			xt,yt,zt=self.world_object.orientation.get()
			if self.aim_at and self.aim_at.world_object: #射撃対象敵プレイヤー認識状態
				self.xoff+=gauss(0, (1-self.cpulevel/2)*0.2)-(self.xoff*0.01)
				self.yoff+=gauss(0, (1-self.cpulevel/2)*0.2)-(self.yoff*0.01)
				if self.xoff>(1-self.cpulevel)*15:
					self.xoff=(1-self.cpulevel)*15
				elif self.xoff<-(1-self.cpulevel)*15:
					self.xoff=-(1-self.cpulevel)*15
				if self.yoff>(1-self.cpulevel)*15:
					self.yoff=(1-self.cpulevel)*15
				elif self.yoff<-(1-self.cpulevel)*15:
					self.yoff=-(1-self.cpulevel)*15
				aim_at_pos = self.aim_at.world_object.position
				aim_at_vel = self.aim_at.world_object.velocity
				target_obj = self.aim_at.world_object
				xt,yt,zt=target_obj.orientation.get()
				self.vel+=gauss(0, (1-self.cpulevel)*2)-(self.xoff*0.3)
				if self.vel>(1-self.cpulevel)*10:
					self.vel=(1-self.cpulevel)*10
				elif self.vel<-(1-self.cpulevel)*10:
					self.vel=-(1-self.cpulevel)*10
				aim_at_pos_future = Vertex3(aim_at_pos.x + aim_at_vel.x*self.vel, aim_at_pos.y + aim_at_vel.y*self.vel, aim_at_pos.z + aim_at_vel.z*self.vel)
	
				self.aim.set_vector(aim_at_pos_future)
				self.aim -= pos
				distance_to_aim = self.aim.normalize() # don't move this line

				# look at the target if it's within sight
				if obj.can_see(*aim_at_pos.get()):
					self.target_orientation.set_vector(self.aim)
					if self.acquire_targets:
						if self.tool != BLOCK_TOOL:
							#射撃指示
							if distance_to_aim < 80+self.cpulevel*45 and self.fire_call is None:
								self.fire_call = callLater(uniform(0,(1-self.cpulevel)*2.5)+1.1, self.fire_weapon)#射撃間隔

				#回避行動制御
				if target_obj.can_see(*pos.get()):
					if self.aim_at.player_pinkblock and not self.aim_at.has_intel:
						self.set_tool(BLOCK_TOOL)
						if self.player_firing == None:
							callLater(uniform(0.1, 0.4), self.bot_pinkblock_crouch)
						else:
							self.input.add('crouch')
					else:
						self.set_tool(WEAPON_TOOL)
						self.target_aim_final.set_vector(self.aim)
						
						diff = target_obj.orientation - self.target_aim_final
						diff = diff.length_sqr()
						if diff > 0.01 and self.cpulevel>0.3:
							p_dot = target_obj.orientation.perp_dot(self.target_aim_final)
							
							if 0.1 > p_dot > -0.1:
								if self.aim_at.player_firing != None:
									if self.aim_at.player_firing == 2:
										self.input.add('sprint')
									else:
										if random()+self.cpulevel > 0.6:
											self.input.add('sprint')
											if self.bot_jump == None:
												self.bot_jump = callLater(uniform(0.01,0.1), self.bot_jumpfunc)
										if random()+self.cpulevel > 1.3 and self.cpulevel>0.5:
											self.input.add('crouch')
											if  self.cpulevel-random()> 0.995:
												self.input.add('sprint')
												if self.bot_jump == None:
													self.bot_jump = callLater(uniform(0.05,0.5), self.bot_jumpfunc)
								if random()+random()+(1-self.cpulevel) < 0.01 and self.cpulevel>0.7:
									self.input.add('sprint')
									if self.bot_jump == None:
										self.bot_jump = callLater(uniform(0.01,0.05), self.bot_jumpfunc)
								if self.cpulevel-random()>0.88 and self.cpulevel>0.4:
									self.input.add('crouch')
									if random() < 0.001 and self.cpulevel>0.8:
										self.input.add('sprint')
										if self.bot_jump == None:
											self.bot_jump = callLater(uniform(0.05,0.1), self.bot_jumpfunc)

							if 0.1 > p_dot > 0.0:
								self.input.add('right')
							elif 0.0 > p_dot > -0.1:
								self.input.add('left')


				#狙点制御
				# orientate towards target
				theta = atan2(self.target_orientation.y,self.target_orientation.x)
				phi = asin(self.target_orientation.z)
				newx = cos(theta+radians(self.xoff))
				newy = sin(theta+radians(self.xoff))
				newz = sin(phi+radians(self.yoff))
				self.target_orientation =Vertex3(newx,newy,newz)
				diff = ori - self.target_orientation 
				diff.z = 0.0
				diff = diff.length_sqr()
				if diff > 0.001:
					p_dot = ori.perp_dot(self.target_orientation)
					if p_dot > 0.0:
						ori.rotate(self._turn_vector)
					else:
						ori.unrotate(self._turn_vector)
					new_p_dot = ori.perp_dot(self.target_orientation)
					if new_p_dot * p_dot < 0.0:
						ori.set_vector(self.target_orientation)
				else:
					ori.set_vector(self.target_orientation)


			else:#射撃対象敵プレイヤー無し状態
				px,py,pz = self.world_object.position.get()
				ox,oy,oz = self.world_object.orientation.get()
				SENSOR_LENGTH=30

				#目標方向長距離障害探知

				if pz >= 60:#海
					self.world_object.position.set(px+1,py-0.65,pz)
					c0r=self.cast_sensor(SENSOR_LENGTH, -1,0,0)
					self.world_object.position.set(px+1,py-0.65,pz-1)
					c1r=self.cast_sensor(SENSOR_LENGTH, -1,0,0)				
					self.world_object.position.set(px+1,py-0.65,pz-2)
					c2r=self.cast_sensor(SENSOR_LENGTH, -1,0,0)	
					self.world_object.position.set(px+1,py+0.65,pz)
					c0l=self.cast_sensor(SENSOR_LENGTH, -1,0,0)
					self.world_object.position.set(px+1,py+0.65,pz-1)
					c1l=self.cast_sensor(SENSOR_LENGTH, -1,0,0)				
					self.world_object.position.set(px+1,py+0.65,pz-2)
					c2l=self.cast_sensor(SENSOR_LENGTH, -1,0,0)	
					sum = c0r+c1r+c2r+c0l+c1l+c2l
					if sum >0:
						self.world_object.position.set(px+1,py-0.65,pz+1)		
						cdr=self.cast_sensor(SENSOR_LENGTH, -1,0,0)
						self.world_object.position.set(px+1,py+0.65,pz+1)		
						cdl=self.cast_sensor(SENSOR_LENGTH, -1,0,0)
						if c2r>0 and c1r>0:
							if c2r>c1r:c2r=0
						if c1r>0 and c0r>0:
							if c1r>c0r:c1r=0
						if c0r>0 and cdr>0:
							if c0r>cdr:c0r=0	
						if c2l>0 and c1l>0:
							if c2l>c1l:c2l=0
						if c1l>0 and c0l>0:
							if c1l>c0l:c1l=0
						if c0l>0 and cdl>0:
							if c0l>cdl:c0l=0	
					sum = c0r+c1r+c2r+c0l+c1l+c2l					
					self.world_object.position.set(px,py,pz) 
				else:	
					self.world_object.position.set(px,py-0.65,pz)
					c0r=self.cast_sensor(SENSOR_LENGTH, -1,0,0)
					self.world_object.position.set(px,py-0.65,pz+1)
					c1r=self.cast_sensor(SENSOR_LENGTH, -1,0,0)
					self.world_object.position.set(px,py+0.65,pz)
					c0l=self.cast_sensor(SENSOR_LENGTH, -1,0,0)
					self.world_object.position.set(px,py+0.65,pz+1)
					c1l=self.cast_sensor(SENSOR_LENGTH, -1,0,0)				
					if c1r>0:
						self.world_object.position.set(px,py-0.65,pz+2)				
						c2r=self.cast_sensor(SENSOR_LENGTH, -1,0,0)
					else:
						c2r=0
					if c1l>0:
						self.world_object.position.set(px,py+0.65,pz+2)
						c2l=self.cast_sensor(SENSOR_LENGTH, -1,0,0)
					else:
						c2l=0
					
					self.world_object.position.set(px,py,pz)
					c00r = 0
					c11r=0
					c00l = 0
					c11l=0					
					if c0r>c1r>0:
						c00r = c0r
						c0r=0
					if c1r>c2r>0:
						c11r = c1r
						c1r=0
					if c0l>c1l>0:
						c00l = c0l
						c0l=0
					if c1l>c2l>0:
						c11l = c1l
						c1l=0
								
					sum = c0r+c1r+c0l+c1l
					if (c00r>0 or c11r>0) and sum == 0:
						self.world_object.position.set(px,py-0.65,pz-1)
						cu1r=self.cast_sensor(SENSOR_LENGTH, -1,0,0)
						if c00r>=cu1r>0:
							sum=100
						if c11r<=0:
							sum=100
						if sum==0:
							self.world_object.position.set(px,py-0.65,pz-2)
							cu2r=self.cast_sensor(SENSOR_LENGTH, -1,0,0)
							if cu1r>=cu2r>0:
								sum=100		

					if (c00l>0 or c11l>0) and sum == 0:
						self.world_object.position.set(px,py+0.65,pz-1)
						cu1l=self.cast_sensor(SENSOR_LENGTH, -1,0,0)
						if c00l>=cu1l>0:
							sum=100
						if c11l<=0:
							sum=100
						if sum==0:
							self.world_object.position.set(px,py+0.65,pz-2)
							cu2l=self.cast_sensor(SENSOR_LENGTH, -1,0,0)
							if cu1l>=cu2l>0:
								sum=100					

					self.world_object.position.set(px,py,pz)
	
				
				if sum>0:#長距離障害発見時、最適針路探索する
					if self.world_object.velocity.z**2<0.01:
						self.world_object.position.set(px-oy*0.65-ox*0.5,py+ox*0.65-oy*0.5,pz)
						r0=self.cast_sensor(SENSOR_LENGTH, ox,oy,oz)
						if r0==0:
						 r0=SENSOR_LENGTH+2
						self.world_object.position.set(px+oy*0.65-ox*0.5,py-ox*0.65-oy*0.5,pz)
						l0=self.cast_sensor(SENSOR_LENGTH, ox,oy,oz)
						if l0==0:
						 l0=SENSOR_LENGTH+2
						self.world_object.position.set(px,py,pz)
						distc=r0+l0
						opt = [0,distc]
						if distc<SENSOR_LENGTH*2:
							for nn in range(10):
									ddeg =(random()-0.5)*0.5
									oyi =oy + ddeg
									norm = (ox**2+oyi**2+oz**2)**0.5
									ox /=norm 
									oyi /=norm 
									oz /=norm 
									self.world_object.position.set(px-oy*0.65-ox*0.5,py+ox*0.65-oy*0.5,pz)
									r0=self.cast_sensor(SENSOR_LENGTH, ox,oyi,oz)
									if r0==0:
									 r0=SENSOR_LENGTH+2
									self.world_object.position.set(px+oy*0.65-ox*0.5,py-ox*0.65-oy*0.5,pz)
									l0=self.cast_sensor(SENSOR_LENGTH, ox,oyi,oz)
									if l0==0:
									 l0=SENSOR_LENGTH+2
									self.world_object.position.set(px,py,pz)
									distc=r0+l0
									if distc<SENSOR_LENGTH*2:
										if distc>opt[1]:
											opt = [ddeg,distc]
									else:
										opt = [ddeg,999]
										break
							oy +=opt[0]
						norm = (ox**2+oy**2+oz**2)**0.5
						ox /=norm 
						oy /=norm 
						oz /=norm 
						if ox>-0.001:
							ox=-0.01
							norm = (ox**2+oy**2+oz**2)**0.5
							ox /=norm 
							oy /=norm 
							oz /=norm 
				else:#長距離障害なし、目的方向に進む
					ox,oy,oz = -1,0,0
					
				orient =ox,oy,oz
				obj.set_orientation(ox,oy,oz)
				self.aim.set_vector(obj.orientation)
				self.target_orientation.set_vector(self.aim)
				self.input.add('up')
				px,py,pz = self.world_object.position.get()
				ox,oy,oz = self.world_object.orientation.get()
				SENSOR_LENGTH=3
				if pz>=60:
					SENSOR_LENGTH=2
				self.world_object.position.set(px-oy*0.65-ox*0.5,py+ox*0.65-oy*0.5,pz)
				r0=self.cast_sensor(SENSOR_LENGTH, ox,oy,oz)
				self.world_object.position.set(px+oy*0.65-ox*0.5,py-ox*0.65-oy*0.5,pz)
				l0=self.cast_sensor(SENSOR_LENGTH, ox,oy,oz)
				self.world_object.position.set(px-oy*0.65-ox*0.5,py+ox*0.65-oy*0.5,pz+1)
				r1=self.cast_sensor(SENSOR_LENGTH, ox,oy,oz)
				self.world_object.position.set(px+oy*0.65-ox*0.5,py-ox*0.65-oy*0.5,pz+1)
				l1=self.cast_sensor(SENSOR_LENGTH, ox,oy,oz)
				self.world_object.position.set(px-oy*0.65-ox*0.5,py+ox*0.65-oy*0.5,pz+2)
				r2=self.cast_sensor(SENSOR_LENGTH, ox,oy,oz)
				self.world_object.position.set(px+oy*0.65-ox*0.5,py-ox*0.65-oy*0.5,pz+2)
				l2=self.cast_sensor(SENSOR_LENGTH, ox,oy,oz)
				self.world_object.position.set(px,py,pz)
				if pz>=60:
					r2=l2=0
				self.world_object.position.set(px-oy*0.65-ox*0.5,py+ox*0.65-oy*0.5,pz-1)
				ru1=self.cast_sensor(SENSOR_LENGTH, ox,oy,oz)
				self.world_object.position.set(px+oy*0.65-ox*0.5,py-ox*0.65-oy*0.5,pz-1)
				lu1=self.cast_sensor(SENSOR_LENGTH, ox,oy,oz)
				self.world_object.position.set(px-oy*0.65-ox*0.5,py+ox*0.65-oy*0.5,pz-2)
				ru2=self.cast_sensor(SENSOR_LENGTH, ox,oy,oz)
				self.world_object.position.set(px+oy*0.65-ox*0.5,py-ox*0.65-oy*0.5,pz-2)
				lu2=self.cast_sensor(SENSOR_LENGTH, ox,oy,oz)

				self.world_object.position.set(px,py,pz)

				jumping = False
				if r0+l0+r1+r2+l1+l2 <=0: #前方直近障害なし
					self.input.add('sprint')
				if l2+r2>0.0 or r1+l1>0.0:
					self.input.discard('sprint')
				if (1.5>r1>0.0 or 1.5>l1>0.0) and r0+l0+ru1+ru2+lu1+lu2<=0:
					if random()<0.005:
						if seconds() - self.digtime>1.3:
							self.digtime=seconds()
							self.digy(px+ox,py+oy,pz+1)
					else:
						self.input.add('jump')
						jumping=True
				if (r0+l0)*(r1+l1)>0 or (r1+l1)*(ru1+lu1+lu2+ru2)>0  and self.ikeru[3]==0:
					PM=choice([-1,1])
					for yyy in [0,-1,1,-2,2,-3,3]:
						ikeruka = True
						for xxx in range(5):
							if self.protocol.map.get_solid(px-xxx,py+yyy*PM,pz):
								ikeruka=False
								break
						if ikeruka:
							for xxx in range(5):
								if self.protocol.map.get_solid(px-xxx,py+yyy*PM,pz+1):
									ikeruka=False
									break	
								if self.protocol.map.get_solid(px-xxx,py+yyy*PM,pz+2):
									ikeruka=False
									break
						if ikeruka:
							for zzz in [0,1,2]:
								if yyy*PM<0:
									for yyyy in range(yyy*PM,0):
										if self.protocol.map.get_solid(px,py+yyyy,pz+zzz):
											ikeruka=False
											break
								elif yyy*PM>0:
									for yyyy in range(yyy*PM):
										if self.protocol.map.get_solid(px,py+yyyy,pz+zzz):
											ikeruka=False
											break
									
						if ikeruka:
							self.ikeru = [floor(px)-0.2,floor(py)+yyy*PM+0.5,pz,200]
							break
						ikeruka=False
					if not ikeruka:
						if seconds() - self.digtime>1.3:
							self.digtime=seconds()
							self.digy(px+ox,py+oy,pz+1)	
				if self.ikeru[3]>0:
					if (self.ikeru[0])<px:
						self.ikeru[3]-=1
						ox = (self.ikeru[0])-px
						oy = (self.ikeru[1])-py
						oz = 0
						norm = (ox**2+oy**2+oz**2)**0.5
						ox /=norm 
						oy /=norm 
						oz /=norm 
						orient =ox,oy,oz
						obj.set_orientation(ox,oy,oz)
						self.aim.set_vector(obj.orientation)
						self.target_orientation.set_vector(self.aim)
					else:
						self.ikeru = [0,0,0,0]
						

					
				if r2+l2+r1+l1<=0 and r0+l0>0:
					self.input.add('chrouch')
					self.input.discard('sprint')
				
				if  (self.world_object.velocity.x**2 + self.world_object.velocity.y**2)**0.5 < 0.0001:
					if self.world_object.velocity.z**2<0.01:
						for yyyyy in [-1,1]:
							sayuukakunin = True
							for zzzzz in [0,1,2]:
								if sayuukakunin:
									for xxxxx in [0,-1]:
										if self.protocol.map.get_solid(px+-xxxxx,py+yyyyy,pz+zzzzz):
											sayuukakunin = False
											break
							if sayuukakunin:
								orient =0,yyyyy,0
								obj.set_orientation(0,yyyyy,0)
								self.aim.set_vector(obj.orientation)
								self.target_orientation.set_vector(self.aim)
								break
						
						if self.jisatu>50:
							PM=choice([-1,1])
							for yyy in [0,-1,1,-2,2,-3,3]:
								ikeruka = True
								for xxx in range(5):
									if self.protocol.map.get_solid(px-xxx,py+yyy*PM,pz):
										ikeruka=False
										break
								if ikeruka:
									for xxx in range(5):
										if self.protocol.map.get_solid(px-xxx,py+yyy*PM,pz+1):
											ikeruka=False
											break	
										if self.protocol.map.get_solid(px-xxx,py+yyy*PM,pz+2):
											ikeruka=False
											break
								if ikeruka:
									for zzz in [0,1,2]:
										if yyy*PM<0:
											for yyyy in range(yyy*PM,0):
												if self.protocol.map.get_solid(px,py+yyyy,pz+zzz):
													ikeruka=False
													break
										elif yyy*PM>0:
											for yyyy in range(yyy*PM):
												if self.protocol.map.get_solid(px,py+yyyy,pz+zzz):
													ikeruka=False
													break
								if ikeruka:
									self.ikeru = [floor(px)-0.2,floor(py)+yyy*PM+0.5,pz,200]
									break
								ikeruka=False
					self.jisatu+=1
					if self.jisatu>500:
						self.kill()
					self.input.discard('sprint')
					if self.ikeru[3]<3:
						if self.world_object.velocity.z<0.01 and random()<0.3:
							self.input.add('jump')
							jumping=True
						if random()<0.01:
							if seconds() - self.digtime>1.3:
								self.digtime=seconds()
								self.digy(px+ox,py+oy,pz+1)						
				elif self.jisatu>0:
					self.jisatu-=1

				if self.protocol.map.get_solid(px-1,py,pz) and self.protocol.map.get_solid(px-1,py,pz+1) and( 
					(self.protocol.map.get_solid(px-1,py+1,pz) and self.protocol.map.get_solid(px-1,py+1,pz+1))or
						(self.protocol.map.get_solid(px-1,py-1,pz) and self.protocol.map.get_solid(px-1,py-1,pz+1)) ):
					if random()<0.05:
						if seconds() - self.digtime>1.3:
							self.digtime=seconds()
							self.digy(px-1,py,pz+1)
				if self.protocol.map.get_solid(px-1,py,pz+2) and (self.protocol.map.get_solid(px-1,py,pz-1) or self.protocol.map.get_solid(px,py,pz-1)) and( 
					(self.protocol.map.get_solid(px,py+1,pz+2) and (self.protocol.map.get_solid(px,py+1,pz-1) or self.protocol.map.get_solid(px,py,pz-1))) or
						(self.protocol.map.get_solid(px,py-1,pz+2) and (self.protocol.map.get_solid(px,py-1,pz-1) or self.protocol.map.get_solid(px,py,pz-1))) ):
					if random()<0.05:
						if seconds() - self.digtime>1.3:
							self.digtime=seconds()
							self.digy(px-1,py,pz+2,DESTROY_BLOCK)
				if jumping:
					if seconds() - self.jumptime>0.5:
						self.jumptime=seconds()
					else:
						self.input.discard('jump')





			if self. tool == SPADE_TOOL and not spade_using:
				self.set_tool(WEAPON_TOOL)	
			# orientate towards target
			
		def distance_calc(self,a,b):
			dx = a[0] - b[0]
			dy = a[1] - b[1]
			dz = a[2] - b[2]
			return (dx**2+dy**2+dz**2)**0.5

		def digy(self,x,y,z,value = SPADE_DESTROY):
			map = self.protocol.map
			if not map.get_solid(x, y, z):
				return
			pos = self.world_object.position
			if self.on_block_destroy(x, y, z, value) == False:
				return
			elif value == DESTROY_BLOCK:
				if map.destroy_point(x, y, z):
					self.blocks = min(50, self.blocks + 1)
					self.on_block_removed(x, y, z)
			elif value == SPADE_DESTROY:
				if map.destroy_point(x, y, z):
					self.on_block_removed(x, y, z)
				if map.destroy_point(x, y, z + 1):
					self.on_block_removed(x, y, z + 1)
				if map.destroy_point(x, y, z - 1):
					self.on_block_removed(x, y, z - 1)
			block_action = BlockAction()
			block_action.x = x
			block_action.y = y
			block_action.z = z
			block_action.value = value
			block_action.player_id = self.player_id
			self.protocol.send_contained(block_action, save = True)
			self.protocol.update_entities()
			

		def dig(self, digpos):		 
			obj = self.world_object
			ori = obj.orientation
			pos = obj.position
			map = self.protocol.map
			for zz in [0,-1,-2]:
				x = digpos[0]
				y = digpos[1]
				z = digpos[2]+zz
				x = int(floor(x))
				y = int(floor(y))
				z = int(floor(z))
				if 0<=x<=511 and 0<=y<=511 :
					if z < 61:
						if map.get_solid(x, y, z):
							map.check_node(x, y, z, True)
							self.on_block_removed(x, y, z)
							self.block_destroying(x,y,z)
			for zz in [0,-1,-2]:
				x = pos.x
				y = pos.y
				z = pos.z+zz
				x = int(floor(x))
				y = int(floor(y))
				z = int(floor(z))
				if 0<=x<=511 and 0<=y<=511 :
					if z < 61:
						if map.get_solid(x, y, z):
							map.check_node(x, y, z, True)
							self.on_block_removed(x, y, z)
							self.block_destroying(x,y,z)

		def block_destroying(self,x,y,z):
				block_action = BlockAction()
				block_action.player_id = 32
				block_action.value = 1
				block_action.x = x
				block_action.y = y
				block_action.z = z
				self.protocol.send_contained(block_action)
				self.protocol.map.remove_point(x, y, z)

		
		def flush_input(self):
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
		
		def set_tool(self, tool):
			if self.on_tool_set_attempt(tool) == False:
				return
			self.tool = tool
			if self.tool == WEAPON_TOOL:
				self.on_shoot_set(self.world_object.primary_fire)
				self.weapon_object.set_shoot(self.world_object.primary_fire)
			self.on_tool_changed(self.tool)
			if self.filter_visibility_data:
				return
			set_tool.player_id = self.player_id
			set_tool.value = self.tool
			self.protocol.send_contained(set_tool)
		
		def bot_set_color(self, color):
			if self.on_color_set_attempt(color) == False:
				return
			self.color = color
			self.on_color_set(color)
			
			set_color.value = make_color(*color)
			set_color.player_id = self.player_id
			self.protocol.send_contained(set_color, sender = self, save = True)
		
		def bot_bullet(self):
			botpos = self.world_object.position.get()
			botori = self.world_object.orientation.get()
			pos = [botpos[0],botpos[1],botpos[2]]
			ori = [botori[0],botori[1],botori[2]]
			d_calc = 0.3 #bk

			for calc_do in xrange(int(128 / d_calc)):
				pos[0] += ori[0]*d_calc
				pos[1] += ori[1]*d_calc
				pos[2] += ori[2]*d_calc
				
				round_pos = (floor(pos[0]), floor(pos[1]), floor(pos[2]))
				_x,_y,_z = round_pos
				
				if _x > 511 or _x < 0 or _y > 511 or _y < 0 or _z > 62 or _z < 0:
					return True
				if self.protocol.map.get_solid(*round_pos):
					return True
				if self.team != None:
					for player in self.team.other.get_players():
						if vector_collision(Vertex3(*pos), player.world_object.position, 0.6):
						#	print "vector_collision head"
							if self.on_hit(100, player, HEADSHOT_KILL, None) != False:
								player.hit(100, self, HEADSHOT_KILL)
								return True

						elif vector_collision(Vertex3(pos[0],pos[1],pos[2]+0.6), player.world_object.position, 0.6) or vector_collision(Vertex3(pos[0],pos[1],pos[2]+0.9), player.world_object.position, 0.6) :
						#	print "vector_collision body"
							if self.on_hit(49, player, WEAPON_KILL, None) != False:
								player.hit(49, self, WEAPON_KILL)
								return True
						elif vector_collision(Vertex3(pos[0],pos[1],pos[2]+1.3), player.world_object.position, 0.6):
						#	print "vector_collision asi"
							if self.on_hit(33, player, WEAPON_KILL, None) != False:
								player.hit(33, self, WEAPON_KILL)
								return True			

		def fire_weapon(self):
			if self:
				if self.world_object:
					self.update()
					self.fire_call = None
					distance_to_aim = self.aim.normalize()
					if self.aim_at and self.aim_at.world_object and self.world_object:
						aim_at_pos = self.aim_at.world_object.position
						if distance_to_aim < 130.0 and self.tool != BLOCK_TOOL:
							self.input.add('primary_fire')
							if self.protocol.bot_damage == True:
								self.bot_bullet() 

		def unforce_aimat(self):
			self.bot_forceaimat = None

		def force_aimat(self, player):
			if player == None:
				return
				
			self.aim_at = player
			self.bot_forceaimat = callLater(7.0, self.unforce_aimat)
		
		def on_hit(self, damage, hitplayer, type, grenade):
			if self.local:
				if hitplayer.bot_damage_player == True or hitplayer.has_intel:
					return connection.on_hit(self, damage, hitplayer, type, grenade)
				else:
					return False
			if hitplayer.local:
				if self.team != hitplayer.team:
					if self.world_object.can_see(*hitplayer.world_object.position.get()):
						if hitplayer.aim_at == None:
							hitplayer.aim_at = self
			return connection.on_hit(self, damage, hitplayer, type, grenade)
	
		def on_spawn(self, pos):
			if not self.local:
				return connection.on_spawn(self, pos)
			self.world_object.set_orientation(-1.0, 0.0, 0.0)
			self.aim.set_vector(self.world_object.orientation)
			self.target_orientation.set_vector(self.aim)
			self.set_tool(WEAPON_TOOL)
			self.aim_at = None
			self.jisatu=0
			self.acquire_targets = True
			connection.on_spawn(self, pos)
			self.color = (0xDF, 0x00, 0xDF)
			self.bot_set_color(self.color) 
		
		def on_tool_changed(self, tool):
			if connection.on_tool_changed(self, tool) == False:
				return False
			if not self.local:
				if tool == BLOCK_TOOL:
					if self.color == (0xDF, 0x00, 0xDF):
						self.player_pinkblock = True
					else:
						self.player_pinkblock = False
				else:
					self.player_pinkblock = False
			
		def on_color_set(self, color):
			if connection.on_color_set(self, color) == False:
				return False
			if not self.local:
				if self.tool == BLOCK_TOOL:
					if color == (0xDF, 0x00, 0xDF):
						self.player_pinkblock = True
					else:
						self.player_pinkblock = False
				else:
					self.player_pinkblock = False
		
		def on_flag_take(u):
			u.has_intel = True
			return connection.on_flag_take(u)

		def on_flag_drop(still_u):
			still_u.has_intel = False
			return connection.on_flag_drop(still_u)

		def on_flag_capture(its_u_again):
			its_u_again.has_intel = False
			return connection.on_flag_capture(its_u_again)
		
		def on_connect(self):
			if self.local:
				return connection.on_connect(self)
			protocol = self.protocol
			if len(protocol.bots) == 0:
				for i in xrange(30):
					protocol.add_bot(protocol.green_team)
			max_players = min(32, self.protocol.max_players)
			if len(protocol.connections) + len(protocol.bots) > max_players:
				protocol.bots[-1].disconnect()
			connection.on_connect(self)
		
		def on_disconnect(self):
			for bot in self.protocol.bots:
				if bot.aim_at is self:
					bot.aim_at = None
			if not self.local:
				if len(self.protocol.connections) + len(self.protocol.bots) == 31:
					callLater(0.2, lambda:self.protocol.add_bot(self.protocol.green_team))
			connection.on_disconnect(self)
		

		
		def on_kill(self, killer, type, grenade):
			if self.fire_call is not None:
				self.fire_call.cancel()
				self.fire_call = None
			for bot in self.protocol.bots:
				if bot.aim_at is self:
					bot.aim_at = None
			return connection.on_kill(self, killer, type, grenade)
		
		def player_stopfiring(self):
			self.player_firing = None
		
		def on_shoot_set(self, first):
			if not self.local:
				if self.tool == WEAPON_TOOL:
					if self.weapon == RIFLE_WEAPON or self.weapon == SHOTGUN_WEAPON:
						if first:
							 if self.player_firing == None:
									self.player_firing = callLater(0.2, self.player_stopfiring)
					else:
						if first:
							self.player_firing = 2 # True != 2, and it isn't a timer, so why not
						else:
							self.player_firing = None
			return connection.on_shoot_set(self, first)
		
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
			
		def _on_reload(self):
			connection._on_reload(self)
			self.refill()


		#至近弾検知で交戦開始	
		def on_orientation_update(self, ox, oy, oz):
			if self.world_object.primary_fire:
				px,py,pz = self.world_object.position.get()
				for player in self.team.other.get_players():
					if player.world_object.can_see(px,py,pz):
						ex,ey,ez = player.world_object.position.get()
						nx,ny,nz = ex-px, ey-py, ez-pz
						dist = (nx**2+ny**2+nz**2)**0.5
						if dist<125:
							nx/=dist
							ny/=dist
							nz/=dist
							naiseki = nx*ox + ny*oy + nz*oz
							if naiseki>1:
								naiseki=1
							if naiseki<-1:
								naiseki=-1
							nasukaku = degrees(acos(naiseki))
							if nasukaku<10:
								if player.aim_at == None:
									player.aim_at = self
			return connection.on_orientation_update(self, ox, oy, oz)

	return BotProtocol, BotConnection