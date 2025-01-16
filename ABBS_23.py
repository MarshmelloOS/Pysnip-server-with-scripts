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
from random import uniform, randrange,gauss,random,choice,triangular,shuffle
from enet import Address
from twisted.internet.reactor import seconds, callLater
from pyspades.protocol import BaseConnection
from pyspades.contained import BlockAction, SetColor,ChatMessage
from pyspades.server import input_data, weapon_input, set_tool, set_color, make_color
from pyspades.world import Grenade
from pyspades.common import Vertex3
from pyspades.collision import vector_collision
from pyspades.constants import *
from commands import admin, add, name, get_team, alias
from pyspades import contained as loaders
from pyspades.packet import load_client_packet
from pyspades.bytes import ByteReader, ByteWriter

from math import floor,sin,cos,degrees,radians,atan2,acos,asin

LOGIC_FPS = 4.0
BOT_IN_BOTH=True
DEFAULT_BOT_NUM = 10
TARGET_POSITION_ASSIGNED = True
TOWmode = False
TDMmode = False#True
ARENAmode = True
ARENA_JUNKAI_SECT = 7

CPU_LV = [95,99] #BOTの強さレベル　最小値、最大値　（1～99）まで

BOTMUTE = False

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
add(botmute)

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
		bots = None
		botbullets = None
		ai_enabled = True
		bot_damage = True
		bullet_visual = False
		BOT_junkai_route = []
		
		tdm_tgt_calc = 100
		best_friends_pos = [Vertex3(255,255,0),Vertex3(255,255,0)]
		
		def add_bot(self, team):
			if len(self.connections) + len(self.bots) >= 32:
				return None
			bot = self.connection_class(self, None)
			bot.join_game(team)
			self.bots.append(bot)
			return bot

		def arena_begun(self):
			for bot in self.bots:
				bot.has_arena_tgt = False
		
		def on_world_update(self):
			if ARENAmode:
				extensions = self.map_info.extensions
				if extensions.has_key('BOT_junkai_route'):
					self.BOT_junkai_route = extensions['BOT_junkai_route']
			botonly = True
			for player in self.players.values():
				if not player.local:
					botonly = False
					break
			if not botonly:
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

				if TDMmode:
					if self.tdm_tgt_calc <= 0:
						self.tdm_tgt_calc = 100
				
						best_friends_blue = None
						best_friends_blue_dist = 99999

						for player in self.blue_team.get_players():
							dist=0
							for friend in player.team.get_players():
								dist += player.distance_calc(player.world_object.position.get(),friend.world_object.position.get())
							if dist<best_friends_blue_dist:
								best_friends_blue_dist=dist
								best_friends_blue = player

						best_friends_green = None
						best_friends_green_dist = 99999
						for player in self.green_team.get_players():
							dist=0
							for friend in player.team.get_players():
								dist += player.distance_calc(player.world_object.position.get(),friend.world_object.position.get())
							if dist<best_friends_green_dist:
								best_friends_green_dist=dist
								best_friends_green = player




						if best_friends_blue is not None:
							best_friends_blue = best_friends_blue.world_object.position
						else:
							best_friends_blue = Vertex3(255,255,0)

						if best_friends_green is not None:

							best_friends_green = best_friends_green.world_object.position
						else:
							best_friends_green = Vertex3(255,255,0)


						self.best_friends_pos = [best_friends_blue, best_friends_green]
					self.tdm_tgt_calc-=1


						
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
		xoff_tebure=0
		yoff_tebure=0
		vel=0
		xt,yt,zt=0,0,0
		dis=255
		jisatu=0
		digtime=0
		ikeru=[0,0,0,0]
		toolchangetime =0
		last_fire = 0
		sprinttime=0
		target_direction=[1,0,0]
		smg_shooting=0
		crouchkaihing=0	
		umaretate = 20
		aim_quit = 100
		damaged_block = []
		front_rcog = [[-1]*64, [-1]*64] # [R,L]
		long_recg=0
		crouchinputed = 0
		ave_d_theta=[0,0,0,0,0,0,0,0,0,0]
		ave_d_phi=[0,0,0,0,0,0,0,0,0,0]
		pre2ori_theta=0
		pre2ori_phi=0

		has_arena_tgt = False
		dir_arena_tgt = 1
		num_arena_tgt = 0
		route_arena_tgt=0
		jikuu_arena_tgt=0

		battle_distance = 60

		xoff_okure=0
		yoff_okure=0

		ois = False

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
				if CPU_LV[1]/100.0>self.cpulevel>CPU_LV[0]/100.0:
					break

		#	self.cpulevel = 0.6

			self.battle_distance = uniform(10,80)

			self.name = '%s %s' % (name,str(self.player_id + 1))
			self.team = team
			weapon_rdm = random()
			if weapon_rdm>0.4:
				self.set_weapon(RIFLE_WEAPON, True)
			elif weapon_rdm>0.15:
				self.set_weapon(SMG_WEAPON, True)
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
				if player.hp>0:
					if vector_collision(pos, player.world_object.position, 60+ self.cpulevel*65):
						if self.canseeY(pos,player.world_object.position)>=0:
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
							if max(self.cpulevel*100,45)>nasukaku:
								player_distances.append(((player.world_object.position - pos), player))
			
			if len(player_distances) > 0:
				nearestindex = min(range(len(player_distances)), key=lambda i: abs(player_distances[i][0].length_sqr()))
				self.aim_at = player_distances[nearestindex][1]
				self.aim_quit = 70
			else:
				self.aim_quit-=1
		
		def think(self):
			obj = self.world_object
			pos = obj.position
			if self.acquire_targets:
				self.find_nearest_player()
			# find nearby foes
		#	if self.acquire_targets:
		#	#	if self.botfindtimer == None:
			#		self.botfindtimer = callLater(max(1-(self.cpulevel)+0.1,0), self.find_nearest_player) #敵が認知界に入った時に、気づくまでの時間
			
			# replicate player functionality
		
		def bot_jumpfunc(self, a = None,b = None):
			if self.world_object.velocity.z**2>0.001:
				self.bot_jump = None
				self.input.add('jump')
				self.player_firing = callLater(0.3, self.player_stopfiring)	
		
		def bot_pinkblock_crouch(self):
			def uncrouch():
				self.player_firing = None
			if self.player_firing == None:
				self.player_firing = callLater(uniform(0.1, 0.4), uncrouch)

		def cast_sensor(self,SENSOR_LENGTH,orientation):
			x,y,z = orientation.get()
			self.world_object.set_orientation(x,y,z)				
			blk = self.world_object.cast_ray(SENSOR_LENGTH)
			if blk is not None:
				dist = self.distance_calc(blk,self.world_object.position.get())
			else:
				dist=0
			return dist	

		def orientation_calc(self, mypos,tgtpos):	
			d = self.distance_calc(mypos.get(),tgtpos.get())

			if d == 0:
				ori = Vertex3(1,0,0)
				d = 0
				return ori, d
			ori = tgtpos - mypos
			ori.x /=d 
			ori.y /=d 
			ori.z /=d 
			return ori, d

		def canseeY2(self,mypos,ori, d):
			if self.hp<=0:
				return None
			pos = [mypos.x,mypos.y,mypos.z]
			ori = ori.get()
			d_calc = 0.3 #bk

			for calc_do in xrange(int(d / d_calc)):
				pos[0] += ori[0]*d_calc
				pos[1] += ori[1]*d_calc
				pos[2] += ori[2]*d_calc
				
				round_pos = (floor(pos[0]), floor(pos[1]), floor(pos[2]))
				_x,_y,_z = round_pos
				
				if _x > 511 or _x < 0 or _y > 511 or _y < 0 or _z > 62 or _z < -20:
					return False
				if _z >= 0:
					if self.protocol.map.get_solid(*round_pos): 
						return False
			return True

		def canseeY(self,mypos,tgt_head, No_need_compx=False):
			fori = self.world_object.orientation.get()
			ori,d = self.orientation_calc(mypos,tgt_head)
			self.world_object.set_orientation(*ori.get())
			if self.world_object.cast_ray(d) is None:
				self.world_object.set_orientation(*fori)
				if No_need_compx:
					return 0
				if self.canseeY2(mypos,ori, d):
					return 0
			self.world_object.set_orientation(*fori)
			if No_need_compx:
				return -1

			tgt_karada=Vertex3(tgt_head.x,tgt_head.y,tgt_head.z+1)
			ori,d = self.orientation_calc(mypos,tgt_karada)
			self.world_object.set_orientation(*ori.get())
			if self.world_object.cast_ray(d) is None:
				self.world_object.set_orientation(*fori)
				if self.canseeY2(mypos,ori, d):
					return 1

			tgt_asi=Vertex3(tgt_head.x,tgt_head.y,tgt_head.z+2)
			ori,d = self.orientation_calc(mypos,tgt_asi)
			self.world_object.set_orientation(*ori.get())
			if self.world_object.cast_ray(d) is None:
				self.world_object.set_orientation(*fori)
				if self.canseeY2(mypos,ori, d):
					return 2
			self.world_object.set_orientation(*fori)
			return -1

		def forward_recognition(self,px,py,pz,distf,TGT_ORIENT,SENSOR_LENGTH):
			if TGT_ORIENT.y==0:
				Rx, Ry = floor(px-TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5+distf*TGT_ORIENT.x)+0.505, floor(py+TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5+distf*TGT_ORIENT.y)+0.505
 				Lx, Ly = floor(px+TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5+distf*TGT_ORIENT.x)+0.505, floor(py-TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5+distf*TGT_ORIENT.y)+0.505
			elif 0.05<((TGT_ORIENT.x/TGT_ORIENT.y)**2)**0.05<20:
				Rx, Ry = px-TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5+distf*TGT_ORIENT.x, py+TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5+distf*TGT_ORIENT.y
				Lx, Ly = px+TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5+distf*TGT_ORIENT.x, py-TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5+distf*TGT_ORIENT.y
			else:
				Rx, Ry = floor(px-TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5+distf*TGT_ORIENT.x)+0.505, floor(py+TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5+distf*TGT_ORIENT.y)+0.505
 				Lx, Ly = floor(px+TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5+distf*TGT_ORIENT.x)+0.505, floor(py-TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5+distf*TGT_ORIENT.y)+0.505
			for rl in range(2):
				for h in range(3):
					if self.front_rcog[rl][int(pz+h)]<0:
						if rl==0:
							RLx = Rx
							RLy = Ry
						else:
							RLx = Lx
							RLy = Ly
						self.world_object.position.set(RLx,RLy,pz+h)
						d=self.cast_sensor(SENSOR_LENGTH-distf, TGT_ORIENT)
						if d>0:d+=distf
						self.front_rcog[rl][int(pz+h)]=d

			c0r=self.front_rcog[0][int(pz)]
			c1r=self.front_rcog[0][int(pz+1)]
			c2r=self.front_rcog[0][int(pz+2)]

			c0l=self.front_rcog[1][int(pz)]
			c1l=self.front_rcog[1][int(pz+1)]
			c2l=self.front_rcog[1][int(pz+2)]

			pattern = 1
			AP = 0
			AP_CROUCH = 20
			AP_JUMP = 5
			AP_DANSA = 1
#		0	#		-1	#	   6661	#	   6662	#	  6663	#		666	#	
#	0		#	H	X	#	H	X	#	H	X	#	H	X	#	H	X	#	
#	1		#	B		#	B	 X	#	B	 X	#	B		#	B	r	#
#	2		#	B		#	B	 X	#	B		#	B	 X	#	B	r	#
################################################## 
			if c0r + c0l +  c1r + c1l +  c2r + c2l ==0  : # 前方障害なし
				pattern = 0
				AP+=0

			elif c1r + c1l +  c2r + c2l== 0 :# -1 しゃがめば通れる
				pattern = -1
				AP+=AP_CROUCH

			elif (0<c0r<=c1r+0.1 and 0<c0r<=c2r+0.1) or (0<c0l<=c1l+0.1 and 0<c0l<=c2l+0.1) : # DAME 無条件で前方障害有り判定
				pattern = 6661
				AP+=0
			elif (0<c0r<=c1r+0.1 and c2r==0) or (0<c0l<=c1l+0.1 and c2l==0) : # DAME 無条件で前方障害有り判定
				pattern = 6662
				AP+=0
			elif (0<c0r<=c2r+0.1 and c1r==0) or (0<c0l<=c2l+0.1 and c1l==0) : # DAME 無条件で前方障害有り判定
				pattern = 6663
				AP+=0
			if 0<pattern<666:
#		A	#		B	#		C	#		D	#	
#	0		#	H	 -	#	H	 X	#	0	 X-	#	
#	1		#	B	 X	#	B		#	1	X 	#
#	2	X	#	B	X	#	B	X	#	2	r-	#
################################################## 
				if c0r + c0l +  c1r + c1l == 0 : # A
					AP+=AP_DANSA
					pattern = 1
				elif c1r>c2r+0.1>0 or c1l>c2l+0.1>0: #B
					AP+=AP_DANSA
					pattern = 1 
				elif (c1r == 0 and c0r>c2r+0.1>0 )or(c1l==0 and c0l>c2l+0.1>0): #C
					AP+=AP_DANSA
					pattern = 1 

				elif (c0r>c1r+0.1>0 or c0r==0) or (c0l>c1l+0.1>0 or c0l==0): #D
					AP+=AP_JUMP
					pattern = 2
				else:
					pattern = -99
			dist=0
			if pattern ==1 or pattern == 2:
				UEtemae = 1.5
				if pattern ==1:
					if min(c2r,c2l)==0:
						dist = max(0,max(c2r,c2l)-UEtemae)	#土台ブロック存在地点の1.5bk手前から探索
					else:
						dist = max(0,min(c2r,c2l)-UEtemae)
				else:
					if min(c1r,c1l)==0:
						dist = max(0,max(c1r,c1l)-UEtemae)
					else:
						dist = max(0,min(c1r,c1l)-UEtemae)
				for rl in range(2):
					h = -1
					if self.front_rcog[rl][int(pz+h)]<0:
						if rl==0:
							RLx = Rx
							RLy = Ry
						else:
							RLx = Lx
							RLy = Ly
						self.world_object.position.set(RLx+(dist-distf)*TGT_ORIENT.x,RLy+(dist-distf)*TGT_ORIENT.y,pz+h)
						d=self.cast_sensor(SENSOR_LENGTH-dist, TGT_ORIENT)
						if d>0:d+=dist
						self.front_rcog[rl][int(pz+h)]=d
				cu1r=self.front_rcog[0][int(pz-1)]
				cu1l=self.front_rcog[1][int(pz-1)]
				if 0<cu1r<=c2r+0.1 or  0<cu1l<=c2l+0.1:
					pattern = 777
				elif pattern == 2:

					for rl in range(2):
						h = -2
						if self.front_rcog[rl][int(pz+h)]<0:
							if rl==0:
								RLx = Rx
								RLy = Ry
							else:
								RLx = Lx
								RLy = Ly
							self.world_object.position.set(RLx+(dist-distf)*TGT_ORIENT.x,RLy+(dist-distf)*TGT_ORIENT.y,pz+h)
							d=self.cast_sensor(SENSOR_LENGTH-dist, TGT_ORIENT)
							if d>0:d+=dist
							self.front_rcog[rl][int(pz+h)]=d
					cu2r=self.front_rcog[0][int(pz-2)]
					cu2l=self.front_rcog[1][int(pz-2)]

					if 0<cu2r<=c1r+0.1 or  0<cu2l<=c1l+0.1:
						pattern = 888					
			return pattern, AP,(dist+distf)
			


		def inputcrouch(self, crouchadd):
			inputedtime = seconds() - self.crouchinputed
			lostime = 0.7-(self.cpulevel/2)
			if inputedtime > lostime:
				if crouchadd:
					self.input.add('crouch') 	
					self.crouchinputed = seconds()			
			elif inputedtime < lostime/2:
				self.input.add('crouch')

		def new_gosa(self,fired):
			if fired:
				R = (1-self.cpulevel)*5+2
				theta = uniform(0,360)
				xoff = R*cos(radians(theta))
				yoff = R*sin(radians(theta))-3*(1-self.cpulevel)
			else:
				R = (1-self.cpulevel)*20+2
				theta = uniform(0,360)
				xoff = R*cos(radians(theta))
				yoff = R*sin(radians(theta))			
			return xoff, yoff

		def tgt_pos_update(self):
			px,py,pzo = self.world_object.position.get()

			if self.world_object.crouch:
				pz=pzo-1
			else:
				pz=pzo
			if TOWmode:
				n = 0
				hidari_team = self.protocol.entities[n].team
				while True:
					n += 1
					if self.protocol.entities[n].team != hidari_team:break
				if self.team != self.protocol.entities[n].team:
					tgt_entity = self.protocol.entities[n]
					ASSIGNED_POSITION = self.protocol.entities[n]
				else:
					tgt_entity = self.protocol.entities[n-1]
					ASSIGNED_POSITION = self.protocol.entities[n-1]
				collides = vector_collision(tgt_entity, 
					self.world_object.position, TC_CAPTURE_DISTANCE)
				if self in tgt_entity.players:
					ASSIGNED_POSITION = None
					if not collides:
						tgt_entity.remove_player(self)
				else:
					if collides:
						ASSIGNED_POSITION = None
						tgt_entity.add_player(self)

			elif TDMmode:
				if self.team == self.protocol.blue_team:
					ASSIGNED_POSITION = self.protocol.best_friends_pos[1]
				elif self.team == self.protocol.green_team:
					ASSIGNED_POSITION = self.protocol.best_friends_pos[0]

			elif ARENAmode:
				junkai_route = self.protocol.BOT_junkai_route
					
				if self.has_arena_tgt:
					ii = self.num_arena_tgt
					choiced_route = self.route_arena_tgt 
					tpos = junkai_route[choiced_route][ii] 
					d = self.distance_calc(tpos,self.world_object.position.get())
					if d < max(5, 0.3*ARENA_JUNKAI_SECT):
						self.jikuu_arena_tgt = 0
						ii+=self.dir_arena_tgt
						if 0 <= ii <= len(junkai_route[choiced_route])-1:
							self.num_arena_tgt = ii
							tpos = junkai_route[choiced_route][ii]
						else:
 							self.has_arena_tgt = False
					self.jikuu_arena_tgt += d
					if self.jikuu_arena_tgt > ARENA_JUNKAI_SECT * UPDATE_FPS * 10:
						self.has_arena_tgt = False
					ASSIGNED_POSITION=Vertex3(*tpos)
				else:
					self.jikuu_arena_tgt = 0
					routenum=len(junkai_route)
					routechoce = range(routenum)
					shuffle(routechoce)
					for choiced_route in routechoce:
						i = 0
						mie = []
						mind = 999
						for junkaipos in junkai_route[choiced_route]:
							d = self.distance_calc(junkaipos,self.world_object.position.get())
							if d<mind+2*ARENA_JUNKAI_SECT:
								if self.canseeY(self.world_object.position,Vertex3(*junkaipos),True)>=0:
									mie.append([i,d])
									if mind>=d:
										mind=d
							i+=1
						if mind<4*ARENA_JUNKAI_SECT:
							break
		
					kouho=[]
					for pt in mie:
						if pt[1]<=d+2*ARENA_JUNKAI_SECT:
							kouho.append(pt[0])
					if kouho !=[]:
						ii = choice(kouho)
						tpos = junkai_route[choiced_route][ii] 
						ASSIGNED_POSITION = Vertex3(*tpos)
						self.route_arena_tgt = choiced_route
						self.has_arena_tgt = True
						self.dir_arena_tgt = choice([-1,1])
						self.num_arena_tgt = ii
					else:
						ASSIGNED_POSITION=None


			if 	ASSIGNED_POSITION is None:
				dd = 0
			else:
				apx,apy,apz = ASSIGNED_POSITION.get()
				xd = apx - px
				yd = apy - py
				dd = (xd**2 + yd**2)**(0.5)
			if dd == 0:
				self.target_direction = Vertex3(1, 0, 0)
			else:
				self.target_direction = Vertex3(xd/dd, yd/dd, 0)

			#	self.protocol.green_team.base.set(ASSIGNED_POSITION.x,ASSIGNED_POSITION.y,ASSIGNED_POSITION.z)
			#	self.protocol.blue_team.base.set(self.world_object.position.x+xd/dd*4,self.world_object.position.y+yd/dd*4,self.world_object.position.z)

			#	self.protocol.update_entities()


			
		def update(self):
			if self.hp<=0:
				return
			second = seconds()
			obj = self.world_object
			pos = obj.position
			ori = obj.orientation
			spade_using =False
			digging = False
			
			dis=255
			obj.set_orientation(*ori.get())
			self.flush_input()
			xt,yt,zt=self.world_object.orientation.get()

			preori_theta = degrees(atan2(yt,xt))
			preori_phi = degrees(asin(zt))

	 
			d_phi = preori_phi - self.pre2ori_phi 
			if preori_theta > 0:
				if self.pre2ori_theta<0 and preori_theta - self.pre2ori_theta>180:
					d_theta = 360 - (preori_theta - self.pre2ori_theta)
				else:
					d_theta = preori_theta - preori_theta
			else:
				if self.pre2ori_theta>0 and preori_theta - self.pre2ori_theta<-180:
					d_theta = -360 - (preori_theta - self.pre2ori_theta)
				else:
					d_theta = preori_theta - self.pre2ori_theta

			self.ave_d_theta.pop(0)
			self.ave_d_theta.append(d_theta)
			self.ave_d_phi.pop(0)
			self.ave_d_phi.append(d_phi)

			if self.aim_at and self.aim_at.world_object: #射撃対象敵プレイヤー認識状態
				crouchadd = False

				self.vel+=gauss(0, (1-self.cpulevel)*2)-(self.vel*0.3)
				self.vel=max( min( (1-self.cpulevel)*5 , self.vel) , (1-self.cpulevel)*(-5))	#動目標の速度誤認係数

				aim_at_pos = self.aim_at.world_object.position
				aim_at_vel = self.aim_at.world_object.velocity
				target_obj = self.aim_at.world_object
				canseepos = self.canseeY(pos,aim_at_pos)
				xt,yt,zt=target_obj.orientation.get()
				aim_at_pos_future = Vertex3(aim_at_pos.x + aim_at_vel.x*self.vel, aim_at_pos.y + aim_at_vel.y*self.vel, aim_at_pos.z+canseepos + aim_at_vel.z*self.vel)
				#動目標の予測位置誤認後位置

				self.aim.set_vector(aim_at_pos_future)
				self.aim -= pos
				distance_to_aim = self.aim.normalize()
				if self.battle_distance < distance_to_aim:#目標遠いなら進む
					self.input.add('up')				
				if canseepos>=0:  #目標視認可能状況
					self.aim_quit=100
					self.target_orientation.set_vector(self.aim)
					if self.acquire_targets:
						if self.tool != BLOCK_TOOL:	#射撃指示					
							if self.smg_shooting>0:
								self.fire_weapon()
							elif distance_to_aim < 135 and self.fire_call is None and seconds() - self.sprinttime>0.5 and seconds() - self.toolchangetime>0.5: 
								self.fire_call = callLater(uniform(0,(1-self.cpulevel)*2.5)+1.1, self.fire_weapon) #射撃間隔

					#回避行動制御
					self.target_aim_final.set_vector(self.aim)
					
					diff = target_obj.orientation - self.target_aim_final
					diff = diff.length_sqr()
					if diff > 0.01 and self.cpulevel>0.3:
						p_dot = target_obj.orientation.perp_dot(self.target_aim_final)
						
						if 0.1 > p_dot > -0.1:
							if random()+self.cpulevel > 0.6: #レアケース　ジャンプ回避
								if self.bot_jump == None:
									self.bot_jump = callLater(uniform(0.01,0.1), self.bot_jumpfunc)

							if random() > 0.95 and self.cpulevel>0.4: #屈伸回避
								crouchadd = True
						if 0.1 > p_dot > 0.0:
							self.input.add('right')
						elif 0.0 > p_dot > -0.1:
							self.input.add('left')

					#狙点制御


					#誤差半径収束
				#	if sum(self.ave_d_theta)>1 or sum(self.ave_d_phi)>1:
				#		self.xoff_okure, self.yoff_okure = self.new_gosa()

				
					off_r = (self.xoff_okure**2+(self.yoff_okure*3)**2)**0.5
					offaddtheta= uniform(0,360)

					d_okure = 100
					d_backokure = d_okure - ((self.cpulevel/2)+0.5)
					if off_r<16:
						d_okure_r = (2-self.cpulevel)*((self.cpulevel/2)+0.5)
					else:
						d_okure_r = ((self.cpulevel/2)+0.5)

					xoffadd = cos(radians(offaddtheta))*off_r*d_okure_r/d_okure
					yoffadd = sin(radians(offaddtheta))*off_r*d_okure_r/d_okure/3

					self.xoff_okure = self.xoff_okure*d_backokure/d_okure + xoffadd
					self.yoff_okure = self.yoff_okure*d_backokure/d_okure + yoffadd

					#手ぶれ分
					self.xoff_tebure+=gauss(0, (1-self.cpulevel/2)*0.2)-(self.xoff_tebure*0.01)
					self.yoff_tebure+=gauss(0, (1-self.cpulevel/2)*0.2)-(self.yoff_tebure*0.01)
					self.xoff_tebure=max( min( (1-self.cpulevel)*15 , self.xoff_tebure) , (1-self.cpulevel)*(-15))
					self.yoff_tebure=max( min( (1-self.cpulevel)*5 , self.yoff_tebure) , (1-self.cpulevel)*(-5))

					theta = degrees(atan2(self.target_orientation.y,self.target_orientation.x))
					phi = degrees(asin(self.target_orientation.z))

					theta = theta + self.xoff_tebure + self.xoff_okure
					phi = phi + self.yoff_tebure + self.yoff_okure


					newz = sin(radians(phi))
					newxy = cos(radians(phi))

					newx = cos(radians(theta))*newxy
					newy = sin(radians(theta))*newxy

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
				else: #目標見えない
					self.aim_quit-=1
					self.smg_shooting=0
					if self.aim_quit<=0:
						self.aim_at=None #目標見えない状況が継続により目標指定解除

				self.inputcrouch(crouchadd)
				self.has_arena_tgt = False


			else:#射撃対象敵無し状態
				self.xoff_okure, self.yoff_okure = self.new_gosa(False)
				px,py,pzo = self.world_object.position.get()
				if TARGET_POSITION_ASSIGNED:   ##目的地点到達
					self.tgt_pos_update()

				if self.world_object.crouch:
					pz=pzo-1
				else:
					pz=pzo
				ox,oy,oz = self.world_object.orientation.get()
				SENSOR_LENGTH=30
				if ARENAmode:
					SENSOR_LENGTH = int(ARENA_JUNKAI_SECT/2)
				TGT_ORIENT = self.target_direction
				if TGT_ORIENT.y==0:
					Rx, Ry = floor(px-TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5)+0.505, floor(py+TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5)+0.505
 					Lx, Ly = floor(px+TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5)+0.505, floor(py-TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5)+0.505
				elif 0.05<((TGT_ORIENT.x/TGT_ORIENT.y)**2)**0.05<20:
					Rx, Ry = px-TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5, py+TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5
					Lx, Ly = px+TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5, py-TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5
				else:
					Rx, Ry = floor(px-TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5)+0.505, floor(py+TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5)+0.505
 					Lx, Ly = floor(px+TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5)+0.505, floor(py-TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5)+0.505


				#目標方向長距離障害探知

				if pz >= 60:#海
					if TGT_ORIENT.y==0:
						Rx, Ry = floor(px-TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5)+0.505, floor(py+TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5)+0.505
 						Lx, Ly = floor(px+TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5)+0.505, floor(py-TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5)+0.505
					elif 0.05<((TGT_ORIENT.x/TGT_ORIENT.y)**2)**0.05<20:
						Rx, Ry = px-TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5, py+TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5
						Lx, Ly = px+TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5, py-TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5
					else:
						Rx, Ry = floor(px-TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5)+0.505, floor(py+TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5)+0.505
 						Lx, Ly = floor(px+TGT_ORIENT.y*0.47-TGT_ORIENT.x*0.5)+0.505, floor(py-TGT_ORIENT.x*0.47-TGT_ORIENT.y*0.5)+0.505
					self.world_object.position.set(Rx,Ry,pz)
					c0r=self.cast_sensor(SENSOR_LENGTH, TGT_ORIENT)
					self.world_object.position.set(Rx,Ry,pz-1)
					c1r=self.cast_sensor(SENSOR_LENGTH, TGT_ORIENT)				
					self.world_object.position.set(Rx,Ry,pz-2)
					c2r=self.cast_sensor(SENSOR_LENGTH, TGT_ORIENT)	
					self.world_object.position.set(Lx,Ly, pz)
					c0l=self.cast_sensor(SENSOR_LENGTH, TGT_ORIENT)
					self.world_object.position.set(Lx,Ly, pz-1)
					c1l=self.cast_sensor(SENSOR_LENGTH, TGT_ORIENT)				
					self.world_object.position.set(Lx,Ly, pz-2)
					c2l=self.cast_sensor(SENSOR_LENGTH, TGT_ORIENT)	
					sumc = c0r+c1r+c2r+c0l+c1l+c2l
					if sumc >0:
						self.world_object.position.set(Rx,Ry,pz+1)		
						cdr=self.cast_sensor(SENSOR_LENGTH, TGT_ORIENT)
						self.world_object.position.set(Lx,Ly, pz+1)		
						cdl=self.cast_sensor(SENSOR_LENGTH, TGT_ORIENT)
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
					AP= sumc = c0r+c1r+c2r+c0l+c1l+c2l
					AP*=1000					
					self.world_object.position.set(px,py,pz) 
				else:	
					if self.long_recg>=10:
						z_plus = 0
						AP=0
						self.front_rcog = [[-1]*64, [-1]*64] # [R,L]
						dist=0
						for ii in range(5):
							pattern, APplus,dist = self.forward_recognition(px,py,pz-z_plus,dist,TGT_ORIENT,SENSOR_LENGTH)
							AP+=APplus
							z_plus+=pattern
							self.world_object.position.set(px,py,pz)
							if 0<pattern<666:
								continue
							break
						if pattern <666:
							sumc = 0
						else:
							sumc = pattern
							AP = pattern
						self.world_object.position.set(px,py,pzo)
						self.long_recg=0

			
						if AP>0:#長距離障害発見時、最適針路探索する
							nowori = Vertex3(ox,oy,oz) #現在進行方向
							z_plus = 0
							APn=0
							dist=0
							self.front_rcog = [[-1]*64, [-1]*64] # [R,L]
							for ii in range(5):
								
								pattern, APplus,dist = self.forward_recognition(px,py,pz-z_plus,dist,nowori,SENSOR_LENGTH)
								APn+=APplus
								z_plus+=pattern
								self.world_object.position.set(px,py,pz)
								if 0<pattern<666:
									continue
								break
							if pattern <666:
								sumc = 0
							else:
								sumc = pattern
								APn = pattern
							if APn>=AP-15:
								nowori = TGT_ORIENT
							else:
								AP=APn
							self.world_object.position.set(px,py,pz)	
							
							if self.world_object.velocity.z**2<0.01: #落下状態では進行方向制御しない
								if AP>666:	#進行不能針路
									self.world_object.position.set(Rx, Ry,pz)
									r0=self.cast_sensor(SENSOR_LENGTH, nowori)
									self.world_object.position.set(Rx, Ry,pz+1)
									r1=self.cast_sensor(SENSOR_LENGTH, nowori)
									if r0==0: 
										r0=SENSOR_LENGTH+2
									if r1==0: 
										r1=SENSOR_LENGTH+2
									self.world_object.position.set(Lx, Ly,pz)
									l0=self.cast_sensor(SENSOR_LENGTH, nowori)
									self.world_object.position.set(Lx, Ly,pz+1)
									l1=self.cast_sensor(SENSOR_LENGTH, nowori)
									if l0==0:
										l0=SENSOR_LENGTH+2
									if l1==0:
										l1=SENSOR_LENGTH+2
									self.world_object.position.set(px,py,pz)
									distc=min(r0,r1)+min(l0,l1)
									opt = [ox,oy,distc]
									
									if distc<SENSOR_LENGTH*2:
										AJ_DEG = max(min(90,177/(2-SENSOR_LENGTH)*distc/2+180-(177/(2-SENSOR_LENGTH)*2)),4)
										tdeg = degrees(atan2(TGT_ORIENT.y,TGT_ORIENT.x))
										deg = degrees(atan2(oy,ox))
										ttdddeg = (tdeg - deg)
										if ttdddeg>180:
											ttdddeg = ttdddeg-360
										for nn in range(5):

											if 45>ttdddeg>-45:
												trim=0.5
											elif -90>ttdddeg:
												trim = 1
											elif 90<ttdddeg:
												trim = 0
											elif 45<ttdddeg:
												trim = 0.2
											else:
												trim = 0.8
										
											ddeg =(random()-trim)*AJ_DEG #+-deg
											ddeg += deg
											oxi =cos(radians(ddeg))
											oyi =sin(radians(ddeg))
											norm = (oxi**2+oyi**2+oz**2)**0.5
											oxi /=norm 
											oyi /=norm  
											oz /=norm 
											optori =  Vertex3(oxi,oyi,oz)
											if oyi==0:
												Rx, Ry = floor(px-oyi*0.47-oxi*0.5)+0.505, floor(py+oxi*0.47-oyi*0.5)+0.505
						 						Lx, Ly = floor(px+oyi*0.47-oxi*0.5)+0.505, floor(py-oxi*0.47-oyi*0.5)+0.505
											elif 0.05<((oxi/oyi)**2)**0.05<20:
												Rx, Ry = px-oyi*0.47-oxi*0.5,py+oxi*0.47-oyi*0.5
												Lx, Ly = px+oyi*0.47-oxi*0.5,py-oxi*0.47-oyi*0.5
											else:
												Rx, Ry = floor(px-oyi*0.47-oxi*0.5)+0.505, floor(py+oxi*0.47-oyi*0.5)+0.505
						 						Lx, Ly = floor(px+oyi*0.47-oxi*0.5)+0.505, floor(py-oxi*0.47-oyi*0.5)+0.505

											self.world_object.position.set(Rx, Ry,pz)
											r0=self.cast_sensor(SENSOR_LENGTH, optori)
											self.world_object.position.set(Rx, Ry,pz+1)
											r1=self.cast_sensor(SENSOR_LENGTH, optori)
											if r0==0: 
												r0=SENSOR_LENGTH+2
											if r1==0: 
												r1=SENSOR_LENGTH+2
											self.world_object.position.set(Lx, Ly,pz)
											l0=self.cast_sensor(SENSOR_LENGTH, optori)
											self.world_object.position.set(Lx, Ly,pz+1)
											l1=self.cast_sensor(SENSOR_LENGTH, optori)
											if l0==0:
												l0=SENSOR_LENGTH+2
											if l1==0:
												l1=SENSOR_LENGTH+2
											self.world_object.position.set(px,py,pz)
											distc=min(r0,r1)+min(l0,l1)
											if distc<SENSOR_LENGTH*2:
												if distc>opt[2]:
													opt = [oxi,oyi,distc]
											else:
												opt = [oxi,oyi,999]
												break
										ox =opt[0]
										oy =opt[1]
									norm = (ox**2+oy**2+oz**2)**0.5
									ox /=norm 
									oy /=norm 
									oz /=norm 
								else:
									opt = [ox,oy]
									tdeg = degrees(atan2(TGT_ORIENT.y,TGT_ORIENT.x))
									deg = degrees(atan2(oy,ox))
									ttdddeg = (tdeg - deg)
									if ttdddeg>180:
										ttdddeg = ttdddeg-360
					#				if not -90<ttdddeg<90:


									for nn in range(max(1,min(3,AP))):

										if 45>ttdddeg>-45:
											trim=0.5
										elif -90>ttdddeg:
											trim = 1
										elif 90<ttdddeg:
											trim = 0
										elif 45<ttdddeg:
											trim = 0.2
										else:
											trim = 0.8
										ddeg = (random()-trim)*max(1,min(5,AP)) #+-deg

										ddeg += deg
										oxi =cos(radians(ddeg))
										oyi =sin(radians(ddeg))
										norm = (oxi**2+oyi**2+oz**2)**0.5
										oxi /=norm 
										oyi /=norm  
										oz /=norm 
										optori =  Vertex3(oxi,oyi,oz)
										z_plus = 0
										APn=0
										dist=0
										self.front_rcog = [[-1]*64, [-1]*64] # [R,L]
										for iii in range(5):
											

											pattern, APplus,dist = self.forward_recognition(px,py,pz-z_plus,dist,optori,SENSOR_LENGTH)
											APn+=APplus
											z_plus+=pattern
											self.world_object.position.set(px,py,pz)
											if 0<pattern<666:
												continue
											break
										if pattern <666:
											sumc = 0
										else:
											sumc = pattern
											APn = pattern
										if APn==0:
											opt = [oxi,oyi]
											break
										elif APn<AP:
											opt = [oxi,oyi]

											AP=APn		
									ox =opt[0]
									oy =opt[1]
									norm = (ox**2+oy**2+oz**2)**0.5
									ox /=norm 
									oy /=norm 
									oz /=norm 	
				
						else:#長距離障害なし、目的方向に進む
							AP=-1
							ox,oy,oz = TGT_ORIENT.get()
					else:
						AP=0
						self.long_recg+=1
				self.world_object.position.set(px,py,pzo)
				orient =ox,oy,oz
				obj.set_orientation(ox,oy,oz)
				self.aim.set_vector(obj.orientation)
				self.target_orientation.set_vector(self.aim)
				self.input.add('up')
				setori = Vertex3(ox,oy,oz)
				if AP>=0:
					SENSOR_LENGTH=3
					umi = 0
					if pz>=60:
						umi = 1
						SENSOR_LENGTH=2
					self.front_rcog = [[-1]*64, [-1]*64] # [R,L]
					dist=0
					pattern, APplus,dist = self.forward_recognition(px,py,pz-umi,dist,setori,SENSOR_LENGTH)
					self.world_object.position.set(px,py,pzo)
					frt = 1
					jumping = False
					if pattern+umi==0: #前方直近障害なし
						self.input.add('sprint')
					elif pattern+umi==1: #前方直近1段差
						self.input.discard('sprint')
					elif pattern+umi==-1: #しゃがめば通れる
						self.input.add('crouch')
					elif pattern+umi==2: #ジャンプでいける壁
						if dist<1.5:
							jumping = True
							self.input.add('jump')
						else:
							self.input.discard('sprint')

					else:
						SENSOR_LENGTH_I=10
						
						for i in range (5):

							if TGT_ORIENT.y==0:
								Rx, Ry = floor(px-TGT_ORIENT.y*(0.47+i)-TGT_ORIENT.x*0.5)+0.505, floor(py+TGT_ORIENT.x*(0.47+i)-TGT_ORIENT.y*0.5)+0.505
				 				Lx, Ly = floor(px+TGT_ORIENT.y*(0.47+i)-TGT_ORIENT.x*0.5)+0.505, floor(py-TGT_ORIENT.x*(0.47+i)-TGT_ORIENT.y*0.5)+0.505
							elif 0.05<((TGT_ORIENT.x/TGT_ORIENT.y)**2)**0.05<20:
								Rx, Ry = px-TGT_ORIENT.y*(0.47+i)-TGT_ORIENT.x*0.5, py+TGT_ORIENT.x*(0.47+i)-TGT_ORIENT.y*0.5
								Lx, Ly = px+TGT_ORIENT.y*(0.47+i)-TGT_ORIENT.x*0.5, py-TGT_ORIENT.x*(0.47+i)-TGT_ORIENT.y*0.5
							else:
								Rx, Ry = floor(px-TGT_ORIENT.y*(0.47+i)-TGT_ORIENT.x*0.5)+0.505, floor(py+TGT_ORIENT.x*(0.47+i)-TGT_ORIENT.y*0.5)+0.505
				 				Lx, Ly = floor(px+TGT_ORIENT.y*(0.47+i)-TGT_ORIENT.x*0.5)+0.505, floor(py-TGT_ORIENT.x*(0.47+i)-TGT_ORIENT.y*0.5)+0.505
							fr = 0
							for zz in range(3):
								self.world_object.position.set(Rx,Ry,pz+zz)				
								fr+=self.cast_sensor(SENSOR_LENGTH_I, TGT_ORIENT)
								if fr>0:break
							fl = 0
							for zz in range(3):
								self.world_object.position.set(Lx,Ly,pz+zz)				
								fl+=self.cast_sensor(SENSOR_LENGTH_I, TGT_ORIENT)
								if fl>0:break
							self.world_object.position.set(px,py,pzo)
							if fr==0:
								if TGT_ORIENT.y==0:
									Rx, Ry = floor(px-TGT_ORIENT.y*(0.47+i)+TGT_ORIENT.x*frt)+0.505, floor(py+TGT_ORIENT.x*(0.47+i)+TGT_ORIENT.y*frt)+0.505
								elif 0.05<((TGT_ORIENT.x/TGT_ORIENT.y)**2)**0.05<20:
									Rx, Ry = px-TGT_ORIENT.y*(0.47+i)+TGT_ORIENT.x*frt, py+TGT_ORIENT.x*(0.47+i)+TGT_ORIENT.y*frt
								else:
									Rx, Ry = floor(px-TGT_ORIENT.y*(0.47+i)+TGT_ORIENT.x*frt)+0.505, floor(py+TGT_ORIENT.x*(0.47+i)+TGT_ORIENT.y*frt)+0.505
								self.ikeru = [floor(Rx)+0.5,floor(Ry)+0.5,pz,200]
								break
							if fl==0:
								if TGT_ORIENT.y==0:
					 				Lx, Ly = floor(px+TGT_ORIENT.y*(0.47+i)+TGT_ORIENT.x*frt)+0.505, floor(py-TGT_ORIENT.x*(0.47+i)+TGT_ORIENT.y*frt)+0.505
								elif 0.05<((TGT_ORIENT.x/TGT_ORIENT.y)**2)**0.05<20:
									Lx, Ly = px+TGT_ORIENT.y*(0.47+i)+TGT_ORIENT.x*frt, py-TGT_ORIENT.x*(0.47+i)+TGT_ORIENT.y*frt
								else:
					 				Lx, Ly = floor(px+TGT_ORIENT.y*(0.47+i)+TGT_ORIENT.x*frt)+0.505, floor(py-TGT_ORIENT.x*(0.47+i)+TGT_ORIENT.y*frt)+0.505
								self.ikeru = [floor(Lx)+0.5,floor(Ly)+0.5,pz,200]

								break
					if self.ikeru[3]>0:
						self.ikeru[3]-=1
						oxi = (self.ikeru[0])-px
						oyi = (self.ikeru[1])-py
						ozi = 0
						norm = (oxi**2+oyi**2+ozi**2)**0.5
						if norm>frt-0.5:
							oxi /=norm 
							oyi /=norm 
							ozi /=norm 
							orient =oxi,oyi,ozi
							obj.set_orientation(oxi,oyi,ozi)
							self.aim.set_vector(obj.orientation)
							self.target_orientation.set_vector(self.aim)
						else:
							self.ikeru = [0,0,0,0]
					else:
						self.ikeru = [0,0,0,0]
						
					
					if  (self.world_object.velocity.x**2 + self.world_object.velocity.y**2)**0.5 < 0.0001:
						self.input.discard('sprint')
						if (self.ikeru[3]>0 and self.jisatu>10) or self.jisatu>30:
							spade_using = True
							if self.tool != SPADE_TOOL:
								self.set_tool(SPADE_TOOL)
								self.toolchangetime =  seconds()	
							if seconds() - self.toolchangetime>1.0 and self.tool == SPADE_TOOL:	
								if obj.orientation.y==0:
									Cx, Cy = floor(px-obj.orientation.x*0.7)+0.505, floor(py-obj.orientation.y*0.7)+0.505
									Rx, Ry = floor(px-obj.orientation.y*0.47-obj.orientation.x*0.7)+0.505, floor(py+obj.orientation.x*0.47-obj.orientation.y*0.7)+0.505
			 						Lx, Ly = floor(px+obj.orientation.y*0.47-obj.orientation.x*0.7)+0.505, floor(py-obj.orientation.x*0.47-obj.orientation.y*0.7)+0.505
								elif 0.05<((obj.orientation.x/obj.orientation.y)**2)**0.05<20:
									Cx, Cy = px-obj.orientation.x*0.7, py-obj.orientation.y*0.7
									Rx, Ry = px-obj.orientation.y*0.47-obj.orientation.x*0.7, py+obj.orientation.x*0.47-obj.orientation.y*0.7
									Lx, Ly = px+obj.orientation.y*0.47-obj.orientation.x*0.7, py-obj.orientation.x*0.47-obj.orientation.y*0.7
								else:
									Cx, Cy = floor(px-obj.orientation.x*0.7)+0.505, floor(py-obj.orientation.y*0.7)+0.505
									Rx, Ry = floor(px-obj.orientation.y*0.47-obj.orientation.x*0.7)+0.505, floor(py+obj.orientation.x*0.47-obj.orientation.y*0.7)+0.505
			 						Lx, Ly = floor(px+obj.orientation.y*0.47-obj.orientation.x*0.7)+0.505, floor(py-obj.orientation.x*0.47-obj.orientation.y*0.7)+0.505

								self.world_object.position.set(Cx,Cy,pz+1)			
								tgtblockc1 = self.world_object.cast_ray(3)
								self.world_object.position.set(Rx,Ry,pz+1)			
								tgtblockr1 = self.world_object.cast_ray(3)
								self.world_object.position.set(Lx,Ly,pz+1)	
								tgtblockl1 = self.world_object.cast_ray(3)
								type = SPADE_DESTROY
								if tgtblockl1 is None and tgtblockr1 is None and tgtblockc1 is None:
									self.world_object.position.set(Cx,Cy,pz)
									tgtblockc0 = self.world_object.cast_ray(3)
									self.world_object.position.set(Rx,Ry,pz)
									tgtblockr0 = self.world_object.cast_ray(3)
									self.world_object.position.set(Lx,Ly,pz)	
									tgtblockl0 = self.world_object.cast_ray(3)
									if tgtblockl0 is None and tgtblockr0 is None and tgtblockc0 is None:
										self.world_object.position.set(Cx,Cy,pz+2)
										tgtblockc2 = self.world_object.cast_ray(2)
										self.world_object.position.set(Rx,Ry,pz+2)
										tgtblockr2 = self.world_object.cast_ray(2)
										self.world_object.position.set(Lx,Ly,pz+2)	
										tgtblockl2 = self.world_object.cast_ray(2)
										if tgtblockc2 is not None:
											distc = self.distance_calc(tgtblockc2,(px,py,pzo+2))
										else:
											distc = 10
										if tgtblockr2 is not None:
											distr = self.distance_calc(tgtblockr2,(px,py,pzo+2))
										else:
											distr = 10
										if tgtblockl2 is not None:
											distl = self.distance_calc(tgtblockl2,(px,py,pzo+2))
										else:
											distl = 10
										if distc<10:
											tgtblock = tgtblockc2
											type = DESTROY_BLOCK
										else:
											if distr<distl:
												tgtblock = tgtblockr2
												type = DESTROY_BLOCK
											else:
												tgtblock = tgtblockl2
												type = DESTROY_BLOCK
									else:
										if tgtblockc0 is not None:
											distc = self.distance_calc(tgtblockc0,(px,py,pzo))
										else:
											distc = 10
										if tgtblockr0 is not None:
											distr = self.distance_calc(tgtblockr0,(px,py,pzo))
										else:
											distr = 10
										if tgtblockl0 is not None:
											distl = self.distance_calc(tgtblockl0,(px,py,pzo))
										else:
											distl = 10
										if distc<10:
											tgtblock = tgtblockc0
										else:
											if distr<distl:
												tgtblock = tgtblockr0
											else:
												tgtblock = tgtblockl0
								else:
									if tgtblockc1 is not None:
										distc = self.distance_calc(tgtblockc1,(px,py,pzo+1))
									else:
										distc = 10
									if tgtblockr1 is not None:
										distr = self.distance_calc(tgtblockr1,(px,py,pzo+1))
									else:
										distr = 10
									if tgtblockl1 is not None:
										distl = self.distance_calc(tgtblockl1,(px,py,pzo+1))
									else:
										distl = 10
									if distc<10:
										tgtblock = tgtblockc1
									else:
										if distr<distl:
											tgtblock = tgtblockr1
										else:
											tgtblock = tgtblockl1
								self.world_object.position.set(px,py,pzo)
								if tgtblock is not None:
									digging = True 
									if type == DESTROY_BLOCK:
										self.input.add('primary_fire')
									else:
										self.input.add('secondary_fire')
									if seconds() - self.digtime>0.5:
										self.digtime=seconds()
										if random()>0.95:
											self.digy(tgtblock[0],tgtblock[1],tgtblock[2]-2, type)	
										elif random()>0.7:
											self.digy(tgtblock[0],tgtblock[1],tgtblock[2]-1, type)	
										else:
											self.digy(tgtblock[0],tgtblock[1],tgtblock[2], type)	
							
						self.jisatu+=1

						if self.jisatu>100 and ARENAmode:
								self.jisatu=0
								self.has_arena_tgt = False
						if self.jisatu>1000:
							self.kill()					
					elif self.jisatu>0:
						self.jisatu-=1
					if jumping:
						if seconds() - self.jumptime>0.5:
							self.input.discard('sprint')
							self.jumptime=seconds()
						else:
							self.input.discard('jump')
				else:
					self.input.add('sprint') #前方長距離障害なし

			if self.world_object.velocity.z<-0.01:
				self.input.discard('sprint')

			if not digging:
				self.digtime=seconds()

			if self. tool == SPADE_TOOL and not spade_using:
				self.toolchangetime =  seconds()
				self.set_tool(WEAPON_TOOL)
			if self.world_object.sprint:
				self.sprinttime	=seconds()


			self.pre2ori_theta = preori_theta
			self.pre2ori_phi = preori_phi

			try:
				self.AHT_bot_orient()
			except:
				pass
		



			
		def distance_calc(self,a,b):
			dx = a[0] - b[0]
			dy = a[1] - b[1]
			dz = a[2] - b[2]
			return (dx**2+dy**2+dz**2)**0.5

		def digy(self,x,y,z,value = SPADE_DESTROY):
			if not (0<=x<=511 and 0<=y<=511 and 0<=z<=60):
				return
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
			if self.hp<=0:
				return None
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
						if player.world_object:
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

		def fire_weapon(self):
			if self:
				if self.world_object:
			#		self.update()
					self.fire_call = None
					distance_to_aim = self.aim.normalize()
					if self.weapon == SMG_WEAPON:
						cooltime = 0.11
					elif self.weapon == RIFLE_WEAPON:
						cooltime = 0.5
					elif self.weapon == SHOTGUN_WEAPON:
						cooltime = 1.0
					if seconds()-self.last_fire>cooltime:
						if self.aim_at and self.aim_at.world_object and self.world_object:
							aim_at_pos = self.aim_at.world_object.position
							if distance_to_aim < 135.0 and self.tool != BLOCK_TOOL:
								if self.weapon == SMG_WEAPON:
									if self.smg_shooting>0:
										self.smg_shooting-=1
									else:
										self.smg_shooting=int(triangular(1, 30, 7))

	
								self.input.add('primary_fire')
								self.xoff_okure, self.yoff_okure = self.new_gosa(True)


								if self.protocol.bot_damage == True:
									blkhit = self.bot_bullet()
									if blkhit:
										if blkhit in self.damaged_block:
											self.damaged_block.remove(blkhit)
											self.fire_block_break(*blkhit)
										else:
											self.damaged_block.append(blkhit)
									if self.weapon == SHOTGUN_WEAPON:
										for n in range(7):
											blkhit = self.bot_bullet()
											if blkhit:
												if blkhit in self.damaged_block:
													self.damaged_block.remove(blkhit)
													self.fire_block_break(*blkhit)

												else:
													self.damaged_block.append(blkhit)
												

								theta = degrees(atan2(self.world_object.orientation.y,self.world_object.orientation.x))
								phi = degrees(asin(self.world_object.orientation.z))
								DEFAULT_RECOIL_V=0.716
								DEFAULT_RECOIL_H=0.05
								if self.weapon == RIFLE_WEAPON:
									weapon_ratio = 4
								elif self.weapon == SMG_WEAPON:
									weapon_ratio = 1
								elif self.weapon == SHOTGUN_WEAPON:
									weapon_ratio = 4
								RECOIL_H=gauss(0, DEFAULT_RECOIL_H*weapon_ratio/3)
								ox = cos(radians(theta+RECOIL_H))
								oy = sin(radians(theta+RECOIL_H))
								oz = sin(radians(phi+DEFAULT_RECOIL_V*weapon_ratio))
								norm = (ox**2+oy**2+oz**2)**0.5
								ox /=norm 
								oy /=norm 
								oz /=norm 
								orient =ox,oy,oz
								self.world_object.set_orientation(ox,oy,oz)
								self.aim.set_vector(self.world_object.orientation)
								self.target_orientation.set_vector(self.aim)
								self.last_fire = seconds()

		def fire_block_break(self,x,y,z):
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
					if hitplayer.canseeY(hitplayer.world_object.position, self.world_object.position)>=0:
						#if hitplayer.aim_at == None:
							hitplayer.aim_at = self
			return connection.on_hit(self, damage, hitplayer, type, grenade)
	
		def bot_kesu_hantei(self):
				blue=0
				green = 0
				blueman = greenman = None
				for bot in self.protocol.players.values():
					if bot.local:	
						if bot.team == self.protocol.blue_team:
							blue+=1
							blueman = bot
						elif bot.team == self.protocol.green_team:
							green+=1
							greenman = bot
				if blue>2 and green >2:
					blueman.disconnect()
					greenman.disconnect()

		def bot_zougen(self):
			if not self.local:
				for add in range(DEFAULT_BOT_NUM):
					if len(self.protocol.connections) + len(self.protocol.bots) <= DEFAULT_BOT_NUM:
						if self.team.count() < self.team.other.count():
							self.protocol.add_bot(self.team)
						else:
							self.protocol.add_bot(self.team.other)
			else:
				hitoiru = False
				for player in self.protocol.players.values():
					if not player.local:
						if player.world_object:
							hitoiru =True
							break
				if hitoiru:
					if len(self.protocol.connections) + len(self.protocol.bots) > DEFAULT_BOT_NUM and  self.team.count() > self.team.other.count():
						if self.team.count()-1 > self.team.other.count()+1:
							self.set_team(self.team.other)
						else:
							self.protocol.add_bot(self.team.other)
			if len(self.protocol.connections) + len(self.protocol.bots) > 15 and len(self.protocol.bots) > 1:
				callLater(7,self.bot_kesu_hantei)


		def on_spawn(self, pos):
			callLater(0.1, self.bot_zougen)


			if not self.local:
				return connection.on_spawn(self, pos)
			if self.team == self.protocol.blue_team:
				self.target_direction = Vertex3(1,0,0)
			else:
				self.target_direction = Vertex3(-1,0,0)
			self.umaretate = 20
			self.world_object.set_orientation(*self.target_direction.get())
			self.aim.set_vector(self.world_object.orientation)
			self.target_orientation.set_vector(self.aim)
			self.set_tool(WEAPON_TOOL)
			self.aim_at = None
			self.jisatu=0
			self.has_arena_tgt = False
			self.damaged_block = []
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
			self.join_bot()
			connection.on_connect(self)

		def on_join(self):
			if self.local:
				return connection.on_join(self)
			self.join_bot()
			connection.on_join(self)

		def join_bot(self):
			protocol = self.protocol
			if len(protocol.bots) == 0:
				for i in xrange(DEFAULT_BOT_NUM):
					if BOT_IN_BOTH:
						if protocol.green_team.count() < protocol.blue_team.count():
							protocol.add_bot(protocol.green_team)
						else:
							protocol.add_bot(protocol.blue_team)	
					else:
						protocol.add_bot(protocol.green_team)	
			max_players = min(32, protocol.max_players)
			if len(protocol.connections) + len(protocol.bots) > max_players:
				protocol.bots[-1].disconnect()


		def on_team_join(self, team):
			if not self.local:
				if not self.ois:
					self.ois = True	
					for bot in self.protocol.bots:
						bot.bot_chat_choice("ois")
			connection.on_team_join(self, team)

		def bot_chat_choice(self,topic):
			message = "default_bot_message"
			if topic == "ois":
				list_ois = ("Hi","hi","Hi","hi","HI","hello","uis","os","ou","oiu","us","oiu","oiu","oiu","iu","hola","ois","ois","ois","ois","ois","oiu","us","iu","hisasiburi", "oius","oisu","ois", "hola", "hi","oi","u","ois","oiu")
				message=choice(list_ois)
				say_or_not=0.07
				say_time=10
			if topic == "sinda":
				list_sinda = ("sinda","uson","ee","fuck","fack","kuso","kusso","ti","tikusyo","aa","aaaaa","uaa","kuso","guu","gununu","ahii","tuyoi","umaina","hack","tii","yarareta","mumu","fuuuckkk","aaaaaa","kono","hack","hacker","majika", "kussooo","kusou","yabe", "fuee", "aan","an","kuu","kuso","sinda")
				message=choice(list_sinda)
				say_or_not=0.02
				say_time=1
			if random()<say_or_not:
				callLater(random()*say_time+0.3, self.bot_chat_say,message)

		def bot_chat_say(self, message):
			if not BOTMUTE:
				contained = ChatMessage()
				global_message = contained.chat_type == CHAT_ALL
				contained.chat_type = [CHAT_TEAM, CHAT_ALL][int(global_message)]
				contained.value = message
				contained.player_id = self.player_id
				self.protocol.send_contained(contained)
				self.on_chat(message, global_message)			


		def on_disconnect(self):
			for bot in self.protocol.bots:
				if bot.aim_at is self:
					bot.aim_at = None
			connection.on_disconnect(self)
		

		
		def on_kill(self, killer, type, grenade):
			if self.fire_call is not None:
				self.fire_call.cancel()
				self.fire_call = None
			for bot in self.protocol.bots:
				if bot.aim_at is self:
					bot.aim_at = None
			if self.local:
				if killer:
					if killer != self:
						self.bot_chat_choice("sinda")
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
			

		#至近弾検知で交戦開始	
		def on_orientation_update(self, ox, oy, oz):
			if self.world_object.primary_fire and self.tool == WEAPON_TOOL:
				for player in self.team.other.get_players():
					if player.local:
						if player.canseeY(player.world_object.position, self.world_object.position)>=0:
							ex,ey,ez = player.world_object.position.get()
							px,py,pz = self.world_object.position.get()
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

		def on_animation_update(self, jump, crouch, sneak, sprint):
			#if sneak:
			return connection.on_animation_update(self, jump, crouch, sneak, sprint)



	return BotProtocol, BotConnection