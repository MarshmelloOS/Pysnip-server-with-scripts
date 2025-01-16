"""
PUBG

script by yuyasato 20170722

"""
from pyspades.server import fog_color
from pyspades.common import make_color
from pyspades.world import Grenade
from math import floor,sin,cos,degrees,radians,atan2
from pyspades.common import Vertex3
from random import randint
from twisted.internet.reactor import callLater, seconds
from twisted.internet.task import LoopingCall
from pyspades.contained import BlockAction, SetColor
from pyspades.contained import *
from pyspades.server import *
from pyspades.common import *
from pyspades.constants import *
from pyspades.server import set_tool, weapon_reload, create_player, set_hp, block_action
from pyspades.server import ServerConnection
from random import randint, uniform, choice,triangular
from copy import deepcopy
from commands import alias, admin, add, name, get_team, get_player

TOW_MAN_CELL = True
BLACKOUTNEEDHIT=20
NOFF=True

CPS = 20    #calclation per sec
AREA_DAMAGE = 1 #dmg per 1/CPS sec
MAP_DESTROY_TIME = 60	#sec
VVTIME = 0.5 # sec
ARMOR_RATIO=0.95
MACHINEGUN_SPEED=0.12	#sec per bullet
BLOCK_SET_SPEED=0.01	#sec
ITEM_NUM=500
FOG_NORMAL = (128, 232, 255)
FOG_WARNING = (255,255,0)
FOG_WARNING_HIGH = (255,128,0)
FOG_DAMAGE = (255,0,0)
FOG_BLACKOUT = (20, 20, 0)
DESTROYED_MARGIN=5 #sec
MED_TIME=5 #sec
HMG_TIME=1 #sec
BOMBER_SPEED=0.5
BOMBER_TURNING=0.5
BOMBING_INTERVAL=60 #sec


MESSAGE_NEXTDESTROY = "[ C A U T I O N ]   koko tugi sinu"
MESSAGE_NEXTDESTROY_HIGH = "[ W A R N I N G ]  koko sinu"
MESSAGE_DESTROYED = "[ D A N G E R ]    koko damage"

@alias('b')
@name('bombstart')
def bombstart(connection):
	if connection.protocol.final_type!=0:
		return "moudame"
	if connection.hp>0:
		return "dead only"
	if seconds() - connection.bombingtime<BOMBING_INTERVAL:
		return "wait %d sec"%(BOMBING_INTERVAL-(seconds() - connection.bombingtime))
	connection.bombingtime=seconds()
	connection.bombing()
	callLater(BOMBING_INTERVAL, connection.bomb_enable)
	return "bomb release"
add(bombstart)

@alias('hp')
@name('hpshow')
def hpshow(connection, name = None):
	if name is None:
		player = connection
	else:
		player = get_player(connection.protocol, name)
	return "%s  HP:%s"%(player.name, player.hp)
add(hpshow)

@alias('sq')
@name('squadteam')
def squadteam(connection, name = None):
	if TOW_MAN_CELL:
		if name is None:
			return "hairu squad no namae kake!!"
		else:
			connection.sq = name
			return "you joined squad '%s'"%name
	return "this is not squad mode"
add(squadteam)

@alias('tms')
@name('toggletwomancell')
def toggletwomancell(connection):
	if connection.protocol.prestart_time:
		global TOW_MAN_CELL
		TOW_MAN_CELL = not TOW_MAN_CELL
		return connection.protocol.send_chat("TOW_MAN_CELL : %s"%TOW_MAN_CELL)
	return "owatte kara yatte"
add(toggletwomancell)

@alias('chk')
@name('squadcheck')
def squadcheck(connection, name = None):
	if TOW_MAN_CELL:
		if name == "full":
			usename=[]
			for playera in connection.protocol.blue_team.get_players():
				if not playera.name in usename:
					samesqmem = []
					for playerb in connection.protocol.blue_team.get_players():
						if playera.sq == playerb.sq:
							usename.append(playerb.name)
							samesqmem.append(playerb.name)
					connection.protocol.send_chat('%s : "%s"'%(samesqmem, playera.sq) )	
			return 
			

		else:
			sqmem=False
			for player in connection.protocol.blue_team.get_players():
				if player != connection:
					if connection.sq==player.sq:
						connection.send_chat("%s : %s"%(player.name, player.sq))
						sqmem=True
			if not sqmem:
				connection.send_chat("no one in your squad")
			return 
			

	return "this is not squad mode"
add(squadcheck)


@alias('start')
@name('startpubg')
def startpubg(connection):
	if TOW_MAN_CELL:
		if connection.protocol.prestart_time:
			usename=[]
			bottisq=0
			for playera in connection.protocol.blue_team.get_players():
				if not playera.name in usename:
					samesqmem = []
					for playerb in connection.protocol.blue_team.get_players():
						if playera.sq == playerb.sq:
							usename.append(playerb.name)
							samesqmem.append(playerb.name)
					connection.protocol.send_chat('%s : "%s"'%(samesqmem, playera.sq) )	
					if len(samesqmem) <=1:
						bottisq +=1
						if bottisq >=2:
							return 	connection.protocol.send_chat('botti 2nin ijou iruzo. ti-mu tukure')
					if len(samesqmem)>2:
						return 	connection.protocol.send_chat('3nin ijou iru kumi aruzo')
	


			connection.protocol.start_pubg()

			connection.protocol.send_chat("Ctrl : open parachute")
			return connection.protocol.send_chat('-- game start --')
		else:
			return connection.protocol.send_chat('already started')

	else:
		if connection.protocol.prestart_time:
			connection.protocol.start_pubg()
			connection.protocol.send_chat("Ctrl : open parachute")
			return connection.protocol.send_chat('-- game start --')
		else:
			return connection.protocol.send_chat('already started')
add(startpubg)

@alias('main')
@alias('m')
@name('main_weapon_change')
def main_weapon_change(connection,weapon):
	weapon = int(weapon)
	if weapon<len(weapon_name):
		if not connection.weapon_have[weapon]:
			return "you dont have this weapon now"	
		if connection.main_weapon == weapon:
			return "main_weapon is already %s"%weapon	
		connection.main_weapon = weapon
		if connection.weapon_ms_now==0:
			connection.resend_tool()
			connection.ammo[connection.weapon_now][0]=connection.weapon_object.current_ammo
			connection.ammo[connection.weapon_now][1]=connection.weapon_object.current_stock
			connection.weapon_now = weapon
			connection.weapon_change_pubg()
		return "main_weapon_change %s"%weapon
	return "num over"
add(main_weapon_change)

@alias('sub')
@alias('s')
@name('sub_weapon_change')
def sub_weapon_change(connection,weapon):
	weapon = int(weapon)
	if weapon<len(weapon_name):
		if not connection.weapon_have[weapon]:
			return "you dont have this weapon now"	
		if connection.sub_weapon == weapon:
			return "sub_weapon is already %s"%weapon	
		connection.sub_weapon = weapon
		if connection.weapon_ms_now==1:
			connection.resend_tool()
			connection.ammo[connection.weapon_now][0]=connection.weapon_object.current_ammo
			connection.ammo[connection.weapon_now][1]=connection.weapon_object.current_stock
			connection.weapon_now = weapon
			connection.weapon_change_pubg()
		return "sub_weapon_change %s"%weapon
	return "num over"
add(sub_weapon_change)

color_bolt    =(255, 190, 190)
color_rifle   =(255, 120, 120)
color_hmg     =(255, 0, 0)
color_hand    =(180, 180, 255)
color_smg     =(125, 125, 255) 
color_ar      =(0, 0, 255)
color_sg      =(170,255, 170)
color_med     =(255,255,255)
color_armor   =(120, 121, 119)
color_helmet =(27,81,5)

color_box=[
	color_bolt   ,
	color_rifle  ,
	color_hmg    ,
	color_hand   ,
	color_smg  ,  
	color_ar   ,  
	color_sg ,  
	color_med ,   
	color_armor,  
	color_helmet]

item_probability=[
	30   ,       #bolt  
	10  ,        #rifle 
	5    ,       #hmg   
	30   ,       #hand  
	10  ,        #smg
	5   ,        #ar 
	10 ,         #sg 
	20 ,         #med
	10,          #armor
	10]          #helmet

weapon_name=[
	"SPADE",
	"BOLTACT",
	"RIFLE",
	"HMG",
	"HANDGUN",
	"SMG",  
	"AR",  
	"SHOTGUN"]

DEF_AMMO = [[0,0], [1,0],[10,0],[2,20],[6,0],[30,0],[20,0],[2,0]]
DEF_UNLOCK =[True,False,False,False,False,False,False,False]


class PUBGTerritory(Territory):
    
	def add_player(self, player):
		return

	def update_rate(self):
		return

	def send_progress(self):
		return

	def finish(self):
		return

	def get_progress(self, set = False):
		return

def apply_script(protocol, connection, config):

	class PUBGConnection(connection):
		weapon_change_killing = False
		ammo=deepcopy(DEF_AMMO)

		weapon_now=0 #0 spade,  1 bolt ,2 rifle, 3hmg  4hand , 5 smg ,6AR, 7 sg
		weapon_ms_now = 0 # 0:main  , 1:sub
		main_weapon=0
		sub_weapon=0
		weapon_have=deepcopy(DEF_UNLOCK)
		medkit=0
		the_hp=100
		sneaktime=0
		armor = 0
		helmet=0
		rapid_loop = None
		static_loop = None
		in_area = 0 #0:normal 1:next_destroy  2:next_destroy_yabai 3:destroyed
		destroyed_margin = 0
		static = False
		static_time=0
		hmg_can = False
		spawn_first=True
		bombingtime=0
		sq=None
		blackout=False
		blackhit=0


		def on_join(self):
			self.state_reset()
			return connection.on_join(self)

		def state_reset(self):
			self.weapon_change_killing = False
			self.ammo=deepcopy(DEF_AMMO)
			self.weapon_now=0 
			self.weapon_ms_now = 0 
			self.main_weapon=0
			self.sub_weapon=0
			self.weapon_have=deepcopy(DEF_UNLOCK)
			self.medkit=0
			self.sneaktime=0
			self.armor = 0
			self.helmet=0
			self.the_hp=100
			self.in_area=0
			self.destroyed_margin = 0
			self.static = False
			self.static_time=0
			self.hmg_can = False
			self.bombingtime=0
			self.blackout=False
			self.blackhit=0

		def bomb_enable(self):
			if self:
				if self.hp<=0:
					if self.bombingtime!=0:
						self.send_chat("airstrike readied.")

		def bombing(self):
			for t in range(15):
				callLater(t/5.0,self.air_bombdrop)

		def air_bombdrop(self):
			x=self.protocol.ac_x-cos(radians(self.protocol.deg))*6
			y=self.protocol.ac_y-sin(radians(self.protocol.deg))*6
			z=-80
			a=(cos(radians(self.protocol.deg)))*(BOMBER_SPEED+uniform(-5,5))/31.5
			b=(sin(radians(self.protocol.deg)))*(BOMBER_SPEED+uniform(-5,5))/31.5
			c=0
			t=0
			while t<1000:
				xg=x+a*t
				yg=y+b*t
				zg=0.0315*(t**2)/2.0 + c*t + z
				t+=0.1
				if self.protocol.map.get_solid(xg,yg,zg) or (not 0<xg<511) or (not 0<yg<511) or (zg>63) :
					t=t/32.1
					break

			grenade_packet.value = t
			grenade_packet.player_id = self.player_id
			grenade_packet.position = (x,y,z)
			grenade_packet.velocity = (a,b,c)
			self.protocol.send_contained(grenade_packet)
			reactor.callLater(t, self.high_explosive, xg, yg, zg)

		def high_explosive(self,x,y,z):
			count = 0
			grenade = self.protocol.world.create_object(Grenade,count,Vertex3(x,y,z),None,Vertex3(0,0,0.001),self.grenade_exploded)
			grenade.name = 'airst_HE'
			grenade_packet.value=count
			grenade_packet.player_id=self.player_id
			grenade_packet.position=(x,y,z)
			grenade_packet.velocity=(0,0,0.001)
			self.protocol.send_contained(grenade_packet)
			while count<5: 
				callLater(count/10000.0, self.makegre,x,y,z,count<3)				
				count+=1

		def makegre(self,x,y,z,exp):
			sigma=1.1
			(xg,yg,zg)=(random.gauss(0, sigma),random.gauss(0, sigma),random.gauss(0, sigma))
			xp, yp, zp = x+xg, y+yg, z+zg
			grenade = self.protocol.world.create_object(Grenade,0,Vertex3(xp,yp,zp),None,Vertex3(0,0,0),self.grenade_exploded)
			grenade.name = 'airst_HE'
			if exp:
				grenade_packet.value=0
				grenade_packet.player_id=self.player_id
				grenade_packet.position=(xp,yp,zp)
				grenade_packet.velocity=(0,0,0)
				self.protocol.send_contained(grenade_packet)

		def check_refill(self):
			pass

		def flight(self,x,y,z,zvel=0.015,para=False):
			if self.world_object and self.hp>0:
				ox,oy,oz = self.world_object.orientation.get()
				r = (ox**2+oy**2)**(1/2.0)
				if not para:
					para = self.world_object.crouch
					if para:
						self.send_chat("para opened")
						zvel=0.008
				else:
					if zvel>0.003:
						zvel -=0.000001
				hvel=0.025-zvel
				ax=ox/r
				ay=oy/r
				cx=x+ax
				cy=y+ay
				npcl= not(self.protocol.map.get_solid(cx, cy, z+2) or self.protocol.map.get_solid(cx, cy, z+1) or self.protocol.map.get_solid(cx, cy, z))
				isgr=  self.protocol.map.get_solid(x, y, z+3) and self.protocol.map.get_solid(cx, cy, z+3)
				xbuff=x+ax*hvel
				ybuff=y+ay*hvel

				if 0<xbuff<511:
					x=xbuff
				if 0<ybuff<511:
					y=ybuff
				z+=zvel
				if npcl and (not isgr) and z<62:
					self.world_object.set_position(x, y, z)						
					position_data.x = x
					position_data.y = y
					position_data.z = z
					self.send_contained(position_data)
					callLater(0.001, self.flight,x,y,z,zvel,para)
					return
				if isgr and npcl and zvel<=0.003:
					dmg = 0
				elif isgr and npcl:
					dmg = ((zvel-0.002)*1000)**2
				elif not npcl and zvel<=0.003:
					dmg =50
				else:
					dmg = ((zvel-0.002)*1000)**2 + 50
				hpset=self.hp-dmg
				self.set_hp(max(hpset,1),type = FALL_KILL)
			

		def weapon_change_pubg(self):
			self.the_hp=self.hp
			if (self.weapon==0 and 1<=self.weapon_now<=3) or (self.weapon==1 and 4<=self.weapon_now<=6) or (self.weapon==2 and 7<=self.weapon_now):
				self.reload_after(True)
				self.resend_tool()
			else:
				x,y,z = self.world_object.position.get()
				pos = Vertex3(x,y,z+2)
				self.on_spawn(pos)
				self.resend_tool()

		def set_weapon(self, weapon, local = False, no_kill = True):
			self.weapon = weapon
			if self.weapon_object is not None:
				self.weapon_object.reset()
			self.weapon_object = WEAPONS[weapon](self._on_reload)
			if not local:
				self.protocol.send_contained(change_weapon, save = True)
				if not no_kill:
					self.kill(type = CLASS_CHANGE_KILL)

		def respawn(self):
			if self.team.spectator or self.weapon_change_killing:
				if self.weapon_change_killing:
					self.weapon_change_killing=False
				self.spawn_call = callLater(0.01, self.spawn)
			else:
				if self.spawn_call is None:
					self.spawn_call = callLater(114514,None)
				return False
			return connection.respawn(self)		

		def checkend(self):
			allplayer=0
			livingplayer=0
			living=self
			for player in self.protocol.blue_team.get_players():
				allplayer+=1
				if not player.world_object.dead:
					livingplayer+=1	
					living= player
								
			self.protocol.send_chat("now surviver %s/%s"%(livingplayer, allplayer))

			if TOW_MAN_CELL:
				if livingplayer<=2:
					winsq="defaultnamedayo"
					if livingplayer==2:
						winsq="none1145141919"
						samesq=False
						for player in self.protocol.blue_team.get_players():
							if not player.world_object.dead:
								if winsq != player.sq:
									winsq = player.sq
								else:
									samesq=True
					else:
						winsq=living.sq
						samesq=True
					if samesq:
						self.protocol.reset_game(self)
						self.protocol.on_game_end()
						kome=""
						for len in winsq:
							kome+="*"
						self.protocol.send_chat("********%s*****************"%kome)
						self.protocol.send_chat("******  %s  win !!!! ******"%winsq)
						self.protocol.send_chat("********%s*****************"%kome) 
				
			else:
				if livingplayer<=1:
					self.protocol.reset_game(self)
					self.protocol.on_game_end()
					kome=""
					for len in living.name:
						kome+="*"
					self.protocol.send_chat("********%s*****************"%kome)
					self.protocol.send_chat("******  %s  win !!!! ******"%living.name)
					self.protocol.send_chat("********%s*****************"%kome) 

		def on_kill(self, killer, type, grenade):
			if type>=5:
				self.weapon_change_killing=True
			else:
				self.respawn_time = -1

				callLater(0.001, self.checkend)
				player = self
				weapon = player.weapon_object
				x, y, z = player.world_object.position.get()
				create_player.weapon = player.weapon
				create_player.player_id = player.player_id
				create_player.name = player.name
				create_player.team = player.team.id
				create_player.x = x
				create_player.y = y
				create_player.z = z
				player.protocol.send_contained(create_player)
				zz = self.protocol.map.get_z(x,y,z)-1
				x=int(x)
				y=int(y)
				zz=int(zz)
				self.make_drop(x,y,zz)
				if killer:
					if killer!=self:
						if killer.hp<=0:
							if grenade is not None:
								if grenade.name == 'airst_HE':
									x=self.protocol.ac_x-cos(radians(self.protocol.deg))*6
									y=self.protocol.ac_y-sin(radians(self.protocol.deg))*6
									z=-80
									killer.spawn_first=True
									killer.spawn((x,y,z))	
			return connection.on_kill(self, killer, type, grenade)				

		
		def make_drop(self,x,y,z):
			box_num=self.weapon_now-1
			color = color_box[box_num]
			block_action = BlockAction()
			set_color = SetColor()
			set_color.value = make_color(*color)
			set_color.player_id = 32
			self.protocol.send_contained(set_color)
			block_action.player_id = 32
			block_action.value=BUILD_BLOCK
			block_action.x = x
			block_action.y = y
			block_action.z = z
			self.protocol.send_contained(block_action)
			self.protocol.map.set_point(x, y, z, color)
			self.protocol.drop_items[(x,y,z)] = (self.weapon_now,sum(self.ammo[self.weapon_now]), self.medkit,self.armor,self.helmet)

		def on_team_join(self,team):
			if team==self.protocol.green_team:
				return self.protocol.blue_team
			return connection.on_team_join(self,team)

		def _on_reload(self):
			callLater(0.01, self.reload_after)			
			return connection._on_reload(self)
	   
		def reload_after(self, change=False,spade=False):
			if spade:
				weapon_reload.player_id = self.player_id
				weapon_reload.clip_ammo = self.weapon_object.current_ammo = 0
				weapon_reload.reserve_ammo = self.weapon_object.current_stock = 0	
				self.send_contained(weapon_reload)
			else:
				if self.weapon_now==1:
					mag=1
					stock=5
					if change:
						mag=self.ammo[self.weapon_now][0]
						stock=self.ammo[self.weapon_now][1]
				elif self.weapon_now==2:
					mag=10
					stock=0
					if change:
						mag=self.ammo[self.weapon_now][0]
						stock=self.ammo[self.weapon_now][1]
				elif self.weapon_now==3:
					mag=0
					stock=20
					if change:
						mag=0
						stock=self.ammo[self.weapon_now][1]
				elif self.weapon_now==4:
					mag=6
					stock=0
					if change:
						mag=self.ammo[self.weapon_now][0]
						stock=self.ammo[self.weapon_now][1]
				elif self.weapon_now==5:
					mag=30
					stock=0
					if change:
						mag=self.ammo[self.weapon_now][0]
						stock=self.ammo[self.weapon_now][1]
				elif self.weapon_now==6:
					mag=20
					stock=0
					if change:
						mag=self.ammo[self.weapon_now][0]
						stock=self.ammo[self.weapon_now][1]
				elif self.weapon_now==7:
					mag=2
					stock=0
					if change:
						mag=self.ammo[self.weapon_now][0]
						stock=self.ammo[self.weapon_now][1]		
						self.weapon_object.slow_reload=False
				weapon_reload.player_id = self.player_id
				if not change:
					stock = self.weapon_object.current_stock + self.weapon_object.current_ammo - mag
					if stock<0:
						mag+=stock
						stock=0
				weapon_reload.clip_ammo = self.weapon_object.current_ammo = mag
				weapon_reload.reserve_ammo = self.weapon_object.current_stock = stock	
				self.send_contained(weapon_reload)

				if 1<=self.weapon_now<=6:
					self.ammo[self.weapon_now][0]=mag
					self.ammo[self.weapon_now][1]=stock

		def on_spawn(self,pos):
			if not self.protocol.prestart_time:
				if self.spawn_first:
					player = self
					weapon = player.weapon_object
					x=self.protocol.ac_x-cos(radians(self.protocol.deg))*6
					y=self.protocol.ac_y-sin(radians(self.protocol.deg))*6
					z=-80
					create_player.weapon = player.weapon
					create_player.player_id = player.player_id
					create_player.name = player.name
					create_player.x = x
					create_player.y = y
					create_player.z = z
					if TOW_MAN_CELL:
						for other_player in self.protocol.players.values():
							if other_player.sq == player.sq:
								create_player.team = player.team.other.id
							else:
								create_player.team = player.team.id
							other_player.send_contained(create_player)
					else:
						for other_player in self.protocol.players.values():
							if other_player == player:
								create_player.team = player.team.other.id
							else:
								create_player.team = player.team.id
							other_player.send_contained(create_player)
					self.reload_after(True,self.weapon_now==0)
					self.spawn_first=False
					self.send_chat("Ctrl : open parachute")
					self.flight(x,y,z)
					return connection.on_spawn(self,pos)
			self.spawn_first=False

			if self.weapon_now<=3:
				self.set_weapon(RIFLE_WEAPON,False,True)
				self.weapon=0
				self.weapon_object = WEAPONS[0](self._on_reload)
			elif 4<=self.weapon_now<=6:
				self.set_weapon(SMG_WEAPON,False,True)
				self.weapon=1
			elif 7<=self.weapon_now:
				self.set_weapon(SHOTGUN_WEAPON,False,True)
				self.weapon=2
			player = self
			weapon = player.weapon_object
			x, y, z = player.world_object.position.get()
			create_player.weapon = player.weapon
			create_player.player_id = player.player_id
			create_player.name = player.name
			create_player.x = x
			create_player.y = y
			create_player.z = z+2

			if TOW_MAN_CELL:
				for other_player in self.protocol.players.values():
					if other_player.sq == player.sq:
						create_player.team = player.team.other.id
					else:
						create_player.team = player.team.id
					other_player.send_contained(create_player)
			else:
				for other_player in self.protocol.players.values():
					if other_player == player:
						create_player.team = player.team.other.id
					else:
						create_player.team = player.team.id
					other_player.send_contained(create_player)
			self.reload_after(True,self.weapon_now==0)
			self.set_hp(self.the_hp,type = FALL_KILL)
			return connection.on_spawn(self,pos)
			

		def on_animation_update(self, jump, crouch, sneak, sprint):
			if sneak and not self.world_object.sneak:
				if seconds() - self.sneaktime < VVTIME:
					self.VV()
					self.sneaktime=0
				else:
					self.sneaktime = seconds()
			if not sneak and self.world_object.sneak:
				if self.sneaktime >0:
					if seconds() - self.sneaktime > VVTIME:
						self.V_V()			

			vz = (self.world_object.velocity.z)**2
			vw = self.world_object.up
			vs = self.world_object.down
			va = self.world_object.left
			vd = self.world_object.right
			vel = vz+va+vs+vd+vw
			if vel<0.001 and (self.world_object.crouch or crouch):
					self.static_start()
			elif vel>=0.001 or (not self.world_object.crouch) or (not crouch )or jump:
					self.static_end()

			return connection.on_animation_update(self, jump, crouch, sneak, sprint)

		def hmg_ok(self):
			if not self.hmg_ready:
				if self.weapon_now==3:
					if self.ammo[3][1]>1 and self.weapon_object.current_ammo<2:
						weapon_reload.player_id = self.player_id
						stock = self.ammo[3][1] - 2
						self.weapon_object.reset()
						weapon_reload.clip_ammo = self.weapon_object.current_ammo = 2
						weapon_reload.reserve_ammo = self.weapon_object.current_stock = self.ammo[3][1] = stock	
						self.weapon_object.set_shoot(True)
						self.send_contained(weapon_reload)	
					if self.ammo[3][1]==1 and self.weapon_object.current_ammo<2:
						weapon_reload.player_id = self.player_id
						stock = 0
						self.weapon_object.reset()
						weapon_reload.clip_ammo = self.weapon_object.current_ammo = 1
						weapon_reload.reserve_ammo = self.weapon_object.current_stock = self.ammo[3][1] = stock	
						self.weapon_object.set_shoot(True)
						self.send_contained(weapon_reload)
			self.hmg_ready=True

		def static_start(self):
			self.static = True

		def static_end(self):
			self.static = False
			self.hmg_ready=False
			if self.weapon_now==3:
				weapon_reload.player_id = self.player_id
				stock = self.ammo[3][1] + self.weapon_object.current_ammo
				self.weapon_object.reset()
				weapon_reload.clip_ammo = self.weapon_object.current_ammo = 0
				weapon_reload.reserve_ammo = self.weapon_object.current_stock = self.ammo[3][1] = stock	
				self.weapon_object.set_shoot(False)
				self.send_contained(weapon_reload)	

		def VV(self):
			self.resend_tool()
			self.weapon_ms_now = not self.weapon_ms_now
			self.send_chat("-----------------------------------")
			self.send_chat("main:%s     sub:%s"%(weapon_name[self.main_weapon],weapon_name[self.sub_weapon]))
			self.send_chat("%sNow"%["  ","             "][self.weapon_ms_now])

			if self.sub_weapon == self.main_weapon:
				return
			self.ammo[self.weapon_now][0]=self.weapon_object.current_ammo
			self.ammo[self.weapon_now][1]=self.weapon_object.current_stock
			if self.weapon_ms_now==0:
				self.weapon_now = self.main_weapon
			else:
				self.weapon_now = self.sub_weapon
			self.weapon_change_pubg()

		def V_V(self):
			self.send_chat("main:%s (%d) sub:%s (%d) "%(weapon_name[self.main_weapon],sum(self.ammo[self.main_weapon]),weapon_name[self.sub_weapon],sum(self.ammo[self.sub_weapon])))
			s=""
			for weapon in [1,2,3]:
				if self.weapon_have[weapon]:
					s+="%d:%s(%d),   "%(weapon,weapon_name[weapon],sum(self.ammo[weapon]))
			self.send_chat(s)
			s=""
			for weapon in [4,5,6]:
				if self.weapon_have[weapon]:
					s+="%d:%s(%d),   "%(weapon,weapon_name[weapon],sum(self.ammo[weapon]))
			self.send_chat(s)
			s=""
			if self.weapon_have[7]:
				s+="7:%s(%d),   "%(weapon_name[7],sum(self.ammo[7]))
			armor = self.armor/2.0
			helm = self.helmet/2.0
			s+="Medkit(%d),   ARMOR (%d),   HELMET (%d)"%(self.medkit,armor,helm)
			self.send_chat(s)
			allplayer=0
			livingplayer=0
			living=self
			for player in self.protocol.blue_team.get_players():
				allplayer+=1
				if not player.world_object.dead:
					livingplayer+=1	
					living= player
			self.send_chat("now surviver %s/%s"%(livingplayer, allplayer))

		def grenade_exploded(self, grenade):

			if self.name is None or self.team.spectator:
				return
			if grenade.team is not None and grenade.team is not self.team:
				# could happen if the player changed team
				return
			position = grenade.position
			x = position.x
			y = position.y
			z = position.z
			if x < 0 or x > 512 or y < 0 or y > 512 or z < 0 or z > 63:
				return
			x = int(x)
			y = int(y)
			z = int(z)
			for player_list in (self.team.other.get_players(), self.team.get_players()):
				for player in player_list:
					if not player.hp:
						continue
					damage = grenade.get_damage(player.world_object.position)
					if damage == 0:
						continue
					returned = self.on_hit(damage, player, GRENADE_KILL, grenade)
					if returned == False:
						continue
					elif returned is not None:
						damage = returned
					player.set_hp(player.hp - damage, self, 
						hit_indicator = position.get(), type = GRENADE_KILL,
						grenade = grenade)
			if self.on_block_destroy(x, y, z, GRENADE_DESTROY) == False:
				return
			map = self.protocol.map
			for nade_x in xrange(x - 1, x + 2):
				for nade_y in xrange(y - 1, y + 2):
					for nade_z in xrange(z - 1, z + 2):
						if map.destroy_point(nade_x, nade_y, nade_z):
							self.on_block_removed(nade_x, nade_y, nade_z)
			block_action.x = x
			block_action.y = y
			block_action.z = z
			block_action.value = GRENADE_DESTROY
			block_action.player_id = self.player_id
			self.protocol.send_contained(block_action, save = True)
			self.protocol.update_entities()		

		def on_hit(self, hit_amount, hit_player, type, grenade):
			if self.protocol.prestart_time:
				return False
			if self.blackout:			
				return False
			if TOW_MAN_CELL:
				if self.sq==hit_player.sq:
					if type ==2 and hit_player.blackout:
						hit_player.blackhit+=1
						if hit_player.blackhit>=BLACKOUTNEEDHIT:
							hit_player.blackout=False
							hit_player.set_hp(10)	
							hit_player.blackhit=0
							x,y,z=hit_player.world_object.position.get()
							color = FOG_NORMAL
							fog_color.color = make_color(*color)
							hit_player.send_contained(fog_color)
							hit_player.world_object.set_position(x, y, z-3)						
						return False
					if NOFF and self!=hit_player:
						return False						

			connection.on_hit(self, hit_amount, hit_player, type, grenade)

			xp,yp,zp=self.world_object.position.get()
			xv,yv,zv=hit_player.world_object.position.get()
			dist = ((xp-xv)**2+(yp-yv)**2+(zp-zv)**2)**(1/2.0)
			if type <=3:
				hit_amount*=0.25
				if type <=1:  #1:HS,0:body
					dmgdef      = 0
					drange    = 0
					Attenuation = 0
					if self.weapon_now == 1:
						dmgdef      = 50.0
						drange       = 180.0
						Attenuation = 0.03
					elif self.weapon_now == 2 : 
						dmgdef      = 35.0
						drange       = 180.0
						Attenuation = 0.02
					elif self.weapon_now == 3 : 
						dmgdef      = 40.0
						drange       = 150.0
						Attenuation = 0.03
					elif self.weapon_now == 4 : 
						dmgdef      = 35.0
						drange       = 15.0
						Attenuation = 0.4
					elif self.weapon_now == 5 : 
						dmgdef      = 25.0
						drange       = 50.0
						Attenuation = 0.07
					elif self.weapon_now == 6 : 
						dmgdef      = 25.0
						drange       = 90.0
						Attenuation = 0.05
					elif self.weapon_now == 7 : 
						dmgdef      = 10.0
						drange       = 10.0
						Attenuation = 0.03
					hit_amount = dmgdef / (1.0+((1.0+Attenuation)**(dist-drange)))-1.0
					if type==0:
						hit_amount/=3
					hit_amount = min(100,max(0,hit_amount))
				if type ==2: #spade
					if self.weapon_now == 0:
						hit_amount = 10
					else:
						hit_amount = 0
				if type ==3: #gre
					hit_amount=min(250, hit_amount)
					hit_amount/=2.0
				if type==0 or type==3:
					reduce = hit_amount*hit_player.armor/200.0
					hit_player.armor-=reduce
					if hit_player.armor<=0:
						hit_player.armor=0
				elif type==1 or type==2:
					if type==2:
						reduce = hit_player.helmet - 50
					else:
						reduce = hit_amount*hit_player.helmet/200.0
					hit_player.helmet-=reduce
					if hit_player.helmet<=0:
						hit_player.helmet=0

				hit_amount-=min(100,max(0,reduce))
				hit_amount = min(100,max(0,hit_amount))
				
			if TOW_MAN_CELL:			
				after_hp = hit_player.hp - hit_amount
				if after_hp<=0:
					if not hit_player.blackout:
						for playerb in self.protocol.blue_team.get_players():
							if playerb.blackout:
								if playerb.sq == hit_player.sq:	
									playerb.blackout=False
									playerb.set_hp(0)	
									playerb.blackhit=0
									color = FOG_NORMAL
									fog_color.color = make_color(*color)
									playerb.send_contained(fog_color)
									return hit_amount
						hit_amount= hit_player.hp - 20
						hit_player.blackout = True
						x,y,z=hit_player.world_object.position.get()
						z = self.protocol.map.get_z(x,y,z)-1
						color = FOG_BLACKOUT
						fog_color.color = make_color(*color)
						hit_player.send_contained(fog_color)
						for xx in range(-3,4):
							for yy in range(-3,4):
								for zz in range(-3,4):
									r = xx**2+yy**2+zz**2
									if (-1<=xx<=1 and -1<=yy<=1 and -1<=zz<=1) or randint(0,30)>r:
										blood_red=randint(170,255)
										if z+zz<63:
											if self.protocol.map.get_solid(x+xx,y+yy,z+zz):
												hit_player.blood_set(x+xx,y+yy,z+zz,(blood_red,0,0),True)
						callLater(0.001, hit_player.blackout_do,x,y,z,0)
					else:
						color = FOG_NORMAL
						fog_color.color = make_color(*color)
						hit_player.send_contained(fog_color)
						hit_player.blackout = False
					
			return hit_amount

		def blackout_do(self,x,y,z,counter):
			if self.world_object and self.blackout and self.hp:
				self.world_object.set_position(x, y, z)						
				position_data.x = x
				position_data.y = y
				position_data.z = z
				self.send_contained(position_data)
				counter+=1
				if counter>=3000:
					counter=0						
					self.set_hp(self.hp - 1)	

				callLater(0.001, self.blackout_do,x,y,z,counter)

		def blood_set(self,x,y,z,color,blooding):
			m = [(x-1,y,z),(x+1,y,z),(x,y-1,z),(x,y+1,z),(x,y,z-1),(x,y,z+1)]
			h = 0
			for k in m:
				h += self.protocol.map.get_solid(k[0],k[1],k[2])	== True
			if h < 6:		
				if self.protocol.map.get_solid(x,y,z):
					block_action = BlockAction()
					block_action.player_id = self.player_id
					block_action.value = DESTROY_BLOCK
					block_action.x = x
					block_action.y = y
					block_action.z = z
					self.protocol.send_contained(block_action)
					self.protocol.map.remove_point(x, y, z)
					set_color = SetColor()
					set_color.value = make_color(*color)
					set_color.player_id = 32
					self.protocol.send_contained(set_color)
					block_action.player_id = 32
					block_action.value=BUILD_BLOCK
					self.protocol.send_contained(block_action)
					self.protocol.map.set_point(x, y, z, color)

		def on_block_destroy(self, x, y, z, mode):
			if self.blackout:			
				return False
			return connection.on_block_destroy(self, x, y, z, mode)

		def on_grenade(self, time_left):
			if self.blackout:			
				return False
			return connection.on_grenade(self, time_left)

		def on_block_build_attempt(self, x, y, z):
			if self.blackout:			
				return False
			return connection.on_block_build_attempt(self, x, y, z)

		def on_line_build_attempt(self, points):
			if self.blackout:			
				return False
			return connection.on_line_build_attempt(self, points)

		def on_fall(self, damage):
			if self.blackout:			
				return False
			return connection.on_fall(self, damage)

		def on_animation_update(self, jump, crouch, sneak, sprint):
			if self.blackout:			
				return False
			return connection.on_animation_update(self, jump, crouch, sneak, sprint)

		def on_command(self, command, parameters):
			if self.blackout:
				if command in ["m", "main", "s", "sub"]:			
					return False
			return connection.on_command(self, command, parameters)					

		def resend_tool(self,MG=False):
			set_tool.player_id = self.player_id
			set_tool.value = self.tool
			if self.weapon_object.shoot:
				self.protocol.send_contained(set_tool)
			else:
				self.send_contained(set_tool)
			if MG:
				if self.ammo[3][1]>=1:
					weapon_reload.player_id = self.player_id
					stock = self.ammo[3][1] - 1
					self.weapon_object.reset()
					weapon_reload.clip_ammo = self.weapon_object.current_ammo = 2
					weapon_reload.reserve_ammo = self.weapon_object.current_stock = self.ammo[3][1] = stock	
					self.weapon_object.set_shoot(True)
					self.send_contained(weapon_reload)


		def on_position_update(self):
			if self and self.world_object:
				vz = (self.world_object.velocity.z)**2
				vw = self.world_object.up
				vs = self.world_object.down
				va = self.world_object.left
				vd = self.world_object.right
				vel = vz+va+vs+vd+vw
				if vel<0.001 and self.world_object.crouch :
						self.static_start()
				else:
						self.static_end()
			return connection.on_position_update(self)

		def rapid_looping(self):
			self.rapid_loop = None
			if self and self.world_object and self.tool==2:
				vz = (self.world_object.velocity.z)**2
				vw = self.world_object.up
				vs = self.world_object.down
				va = self.world_object.left
				vd = self.world_object.right
				vel = vz+va+vs+vd+vw				
				if vel<0.001 and self.world_object.crouch:
					self.resend_tool(True)
					self.rapid_loop = callLater(MACHINEGUN_SPEED, self.rapid_looping)
				else:
					self.static_end()

		def on_shoot_set(self, fire):
			if self.tool==2:				
				if self.weapon_now==3:
					vz = (self.world_object.velocity.z)**2
					vw = self.world_object.up
					vs = self.world_object.down
					va = self.world_object.left
					vd = self.world_object.right
					vel = vz+va+vs+vd+vw
					if fire:
						if vel<0.001 and self.world_object.crouch:
							if self.rapid_loop is not None:
								self.rapid_loop.cancel()
							self.rapid_loop = None
							self.rapid_loop = callLater(MACHINEGUN_SPEED, self.rapid_looping)
					else:
						if self.rapid_loop is not None:
							self.rapid_loop.cancel()
						self.rapid_loop = None
						if self.ammo[3][1]>=1 and vel<0.005 and self.world_object.crouch:
							weapon_reload.player_id = self.player_id
							stock = self.ammo[3][1] - 1
							self.weapon_object.reset()
							weapon_reload.clip_ammo = self.weapon_object.current_ammo = 2
							weapon_reload.reserve_ammo = self.weapon_object.current_stock = self.ammo[3][1] = stock	
							self.weapon_object.set_shoot(True)
							self.send_contained(weapon_reload)

				if not fire:
					if self.weapon_object.current_ammo <=0:	
						weapon_reload.player_id = self.player_id
						weapon_reload.clip_ammo = self.weapon_object.current_ammo = 0	
						self.send_contained(weapon_reload)
					self.ammo[self.weapon_now][0]=self.weapon_object.current_ammo
					self.ammo[self.weapon_now][1]=self.weapon_object.current_stock


			return connection.on_shoot_set(self, fire)

		def ammo_get(self,weapon,num):
			self.ammo[weapon][1]+=num
			if self.ammo[weapon][1]<255:
				if weapon == self.weapon_now:
					weapon_reload.player_id = self.player_id
					weapon_reload.reserve_ammo = self.weapon_object.current_stock = self.ammo[weapon][1]	
					self.send_contained(weapon_reload)
			else:
				self.send_chat("you have too much ammo.")

		def on_color_set_attempt(self, color):
			if not self.protocol.prestart_time:
				aim = self.world_object.cast_ray(5)
				if aim is not None:
					if aim in self.protocol.drop_items:
						value = self.protocol.drop_items[aim]
						weapon = value[0]
						num = value[1]
						if weapon!=0:
							if self.weapon_have[weapon]:
								self.ammo_get(weapon,num)
								self.send_chat("You got %d %s ammo. (%s:%d)"%(num,weapon_name[weapon],weapon_name[weapon],self.ammo[weapon][1]))
							else:
								self.send_chat("You got %s. (NUM:%d)"%(weapon_name[weapon],weapon))
								self.weapon_have[weapon]=True
						mednum= value[2]
						self.medkit+=mednum
						self.send_chat("you got medkits.  (MEDKIT:%d)"%self.medkit)
						armornum= value[3]
						if self.armor<armornum:
							self.armor=armornum
							self.send_chat("you got new armor.")
						helmetnum= value[4]
						if self.helmet<helmetnum:
							self.helmet=helmetnum
							self.send_chat("you got new helmet.")
						self.destroy_drop(aim[0],aim[1],aim[2])

				if sum(self.color)<5:
					if color in color_box:
						blk = self.world_object.cast_ray(7)
						if blk is not None:
							blkcolor = self.protocol.map.get_point(blk[0],blk[1],blk[2])[1]
							if (blk[0],blk[1],blk[2],blkcolor) in self.protocol.weapon_box:
								weapon = 0
								if color == color_bolt :
									weapon=1
									num=floor(triangular(2, 7))
								elif color == color_rifle :	
									weapon=2
									num=floor(triangular(3, 10))
								elif color == color_hmg :
									weapon=3
									num=floor(triangular(10, 30))
								elif color == color_hand :
									weapon=4
									num=floor(triangular(4, 18))
								elif color == color_smg :
									weapon=5
									num=floor(triangular(7, 20))
								elif color == color_ar :
									weapon=6
									num=floor(triangular(10, 15))
								elif color ==  color_sg:
									weapon=7
									num=floor(triangular(1, 8))

								if weapon!=0:
									if self.weapon_have[weapon]:
										self.ammo_get(weapon,num)
										self.send_chat("You got %d %s ammo. (%s:%d)"%(num,weapon_name[weapon],weapon_name[weapon],self.ammo[weapon][1]))

									else:
										self.send_chat("You got %s. (NUM:%d)"%(weapon_name[weapon],weapon))
										self.weapon_have[weapon]=True

								if color ==  color_med:
									num=floor(triangular(1, 8,3))
									num*=10
									self.medkit+=num
									self.send_chat("you got %d medkits.  (MEDKIT:%d)"%(num,self.medkit))
								elif color ==  color_armor:
									self.armor=200
									self.send_chat("you got a new armor.")
								elif color ==  color_helmet:
									self.helmet=200
									self.send_chat("you got a new helmet.")


								self.destroy_box(blk[0],blk[1],blk[2],blkcolor)	
			return connection.on_color_set_attempt(self, color)

		def destroy_drop(self,x,y,z):
			block_action = BlockAction()
			block_action.player_id = 32
			block_action.value = DESTROY_BLOCK
			block_action.x = x
			block_action.y = y
			block_action.z = z
			self.protocol.send_contained(block_action)
			self.protocol.map.remove_point(x, y, z)
			del self.protocol.drop_items[(x,y,z)]

		def destroy_box(self,x,y,z,color):
			for xd in (-1,0,1):			
				for yd in (-1,0,1):	
					xx,yy,zz = x+xd,y+yd,z
					block_action = BlockAction()
					block_action.player_id = 32
					block_action.value = DESTROY_BLOCK
					block_action.x = xx
					block_action.y = yy
					block_action.z = zz
					self.protocol.send_contained(block_action)
					self.protocol.map.remove_point(xx, yy, zz)
			self.protocol.weapon_box.remove((x,y,z,color))

		def cps_do(self):
			if self.static:
				self.static_time+=1
			else:
				self.static_time=0
			if self.static_time>MED_TIME*CPS:
				self.use_medkit()
			if self.static_time>HMG_TIME*CPS:
				self.hmg_ok()

		def area_damage(self):
			if self.hp>0:
				self.set_hp(self.hp - AREA_DAMAGE)

		def use_medkit(self):
			if self.tool == BLOCK_TOOL:
				if 100<=self.hp:
					return
				if self.medkit<=0:
					return
				if self.hp<0:
					return
				self.medkit-=1
				hp = min(100,self.hp + 1)
				self.set_hp(hp,type = FALL_KILL)

		def in_normalarea(self):
			if self.destroyed_margin>=1:
				self.destroyed_margin-=1
			if self.in_area != 0:
				self.in_area = 0
				color = FOG_NORMAL
				fog_color.color = make_color(*color)
				self.send_contained(fog_color)

		def in_next_destroy(self):
			if self.destroyed_margin>=1:
				self.destroyed_margin-=1
			if self.in_area != 1:
				self.in_area = 1
				color = FOG_WARNING
				fog_color.color = make_color(*color)
				self.send_contained(fog_color)
			if self.in_area != 2 and self.protocol.minute_timer>=MAP_DESTROY_TIME*CPS/2:
				self.in_area = 2
				color = FOG_WARNING_HIGH
				fog_color.color = make_color(*color)
				self.send_contained(fog_color)
			if self.protocol.minute_timer%CPS ==0:
				if self.in_area == 1:
					self.send_chat(MESSAGE_NEXTDESTROY)
				elif self.in_area == 2:
					self.send_chat(MESSAGE_NEXTDESTROY_HIGH)

		def in_destroyed(self):
			self.destroyed_margin+=1
			if self.in_area != 3:
				self.in_area = 3
				color = FOG_DAMAGE
				fog_color.color = make_color(*color)
				self.send_contained(fog_color)
			if self.protocol.minute_timer%CPS ==0:
				self.send_chat(MESSAGE_DESTROYED)
			if self.destroyed_margin>=DESTROYED_MARGIN*CPS:
				self.area_damage()

	class PUBGProtocol(protocol):
		game_mode = TC_MODE

		prestart_time=False
		minute_timer=0
		destroy_call = None
		warning_call = None
		notice_call=None
		lastnotice_call= None
		final_type=0
		final_damage=0
		final_lines=[]
		weapon_box = []
		drop_items={}
		area_x = ["A","B","C","D","E","F","G","H"]
		area_y = ["1","2","3","4","5","6","7","8"]
		destroyed_area=[]
		nextdestroyarea = []
		next_marking_square_x=[]
		next_marking_square_y=[]
		next_marking_slash=[]
		autobomb=0
		ac_x=250
		ac_y=250
		deg=0

		def on_map_change(self, map):
	#		callLater(60, self.start_pubg)
			self.weapon_box=[]
			while len(self.weapon_box) < ITEM_NUM:
				self.make_weapon_box()
			self.prestart_time=True
			self.area_x = ["A","B","C","D","E","F","G","H"]
			self.area_y = ["1","2","3","4","5","6","7","8"]
			self.destroyed_area=[]
			self.destroy_call = None
			self.warning_call = None
			self.nextdestroyarea = []
			self.next_marking_square_x=[]
			self.next_marking_square_y=[]
			self.next_marking_slash=[]
			self.drop_items={}
			self.final_type=0
			self.final_damage=0
			self.final_lines=[]
			for player in self.players.values():
				player.spawn_first=True
			return protocol.on_map_change(self,map)		


		def make_weapon_box(self):
			puted=False
			while True:
				item_no = choice(range(len(color_box)))
				probability = item_probability[item_no]
				if probability > randint(0,sum(item_probability)):
					break
			color = color_box[item_no]
			for j in range(32800):
				zz=61
				while zz >60:
					x,y = randint(3,508),randint(3,508)
					zz = self.map.get_z(x,y)
				for i in range(63):	
					zzz = randint(zz+1,62)
					zzzz = self.map.get_z(x,y,zzz)-1
					if self.is_space_weapon_box(x,y,zzzz):
						self.weapon_box_put(x,y,zzzz,color)
						self.weapon_box.append((x,y,zzzz,color))
						puted = True
						break
				if puted:break
			return puted

		def weapon_box_put(self,x,y,z,color):
			for xd in (-1,0,1):			
				for yd in (-1,0,1):	
					if not (xd==0 and yd==0):
						self.paint_ground(x+xd,y+yd,z,(0,0,0))
				
			self.paint_ground(x,y,z,color)

		def is_space_weapon_box(self,x,y,z):
			for xd in (-1,0,1):
				for yd in (-1,0,1):	
					for zd in (-2,-1,0):				
						if self.map.get_solid(x+xd, y+yd, z+zd):
							return	False
			for xd in (-1,0,1):
				for yd in (-1,0,1):	
					if not self.map.get_solid(x+xd, y+yd, z+1):
						return	False		
			for xd in (-2,-1,0,1,2):
				for yd in (-2,-1,0,1,2):	
					if self.map.get_z(x+xd, y+yd) > z-3:
						return	False	
			return True			
			
		def start_pubg(self):
			self.area_x = ["A","B","C","D","E","F","G","H"]
			self.area_y = ["1","2","3","4","5","6","7","8"]
			self.destroyed_area=[]
			self.nextdestroyarea = []
			self.next_marking_square_x=[]
			self.next_marking_square_y=[]
			self.next_marking_slash=[]
			self.destroy_call = None
			self.warning_call = None
			self.notice_call=None
			self.lastnotice_call= None
			self.prestart_time=False
			self.drop_items={}
			self.final_type=0
			self.final_damage=0
			self.final_lines=[]
			self.autobomb=0

			for player in self.blue_team.get_players():
				player.state_reset()
				x=y=255
				x+=uniform(-40,40)
				y+=uniform(-40,40)
				z=-80
				pos = (x, y, z)				
				player.spawn(pos)
				player.set_location(pos)
				player.flight(x,y,z)
			self.minute_timer=0
			callLater(1, self.pubg_timer)

		def pubg_timer(self):
			if not self.prestart_time:
				self.minute_timer+=1
				self.seconds_do()
				if self.minute_timer==MAP_DESTROY_TIME*CPS:
					self.minutes_do()
					self.minute_timer=0				
				callLater(1.0/CPS, self.pubg_timer)

		def minutes_do(self):
			if len(self.nextdestroyarea)!=1:
				self.area_destroy()

		def seconds_do(self):
			average = self.player_position_check()
			if self.final_type==0:
				self.autopilot(average)
			else:
				self.ac_x=-100
				self.ac_y=-100		
				self.deg=0

		def autopilot(self,target):
			if self.final_type==0:
				x1=target[0]
				y1=target[1]
				x2=self.ac_x
				y2=self.ac_y
				dx=(x1-x2)
				dy=(y1-y2)
				phi=degrees(atan2(dy,dx))
				theta=radians(self.deg)
				delta = (self.deg-phi+360)%360
				if 1<delta <359:
					if delta <180:
						rd=-1
					else:
						rd=1
				else:
					rd=0
				pos=[(0,0),(0,3),(0,6),(0,9),(0,12),(0,15),(3,15),(-3,15),(3,4),(6,5),(9,6),(12,7),(-3,4),(-6,5),(-9,6),(-12,7)]
#figher			pos=[(0,0),(0,2),(0,10),(0,13),(3,7),(1,8),(1,5),(4,9),(6,10),(2,14),(-3,7),(-1,8),(-1,5),(-4,9),(-6,10),(-2,14)]
#vippei			pos=[(0,0),(0,0),(0,0),(0,0),(0,0),(0,-3),(0,-6),(0,-9),(-1,-10),(1,-10),(3,-3),(3,-4),(6,-3),(-3,-3),(-3,-4),(-6,-3)]
				entitys=[]
				theta=radians(self.deg)
				for i in range(16):
					move_object.object_type = i
					move_object.state = 1
					x,y = pos[i][1]/-1.5,pos[i][0]/1.5
					xx=x*cos(theta) - y*sin(theta)
					yy=x*sin(theta) + y*cos(theta)
					xx+=self.ac_x
					yy+=self.ac_y
					z=-80
					move_object.x = xx
					move_object.y = yy
					move_object.z = z
					entity_new=Territory(i,self,x,y,z)
					entity_new.progress=0.5
					entity_new.team=self.green_team
					entitys.append(entity_new)
					self.send_contained(move_object)
				self.entities = entitys
				self.ac_x+=cos(theta)*BOMBER_SPEED
				self.ac_y+=sin(theta)*BOMBER_SPEED
				self.deg+=BOMBER_TURNING*rd			
			else:
				self.ac_x=-100
				self.ac_y=-100		
				self.deg=0

		def player_position_check(self):
			sumx,sumy,pnum=0,0,0
			kakutei=(0,0,0,99999,None) #TF,x,y,d
			if not self.prestart_time:
				for player in self.blue_team.get_players():	
					if player.world_object:
						if player.hp>0:	
							player.cps_do()
							x,y,z = player.world_object.position.get()
							sumx+=x
							sumy+=y
							pnum+=1
							range90deg=(BOMBER_SPEED/BOMBER_TURNING)*180/3.1416
							if (x-self.ac_x)**2 + (y-self.ac_y)**2 < (192.0)**2:
								dx=(x-self.ac_x)
								dy=(y-self.ac_y)
								phi=degrees(atan2(dy,dx))
								theta=radians(self.deg)
								delta = (self.deg-phi+360)%360
								if not 45<delta<315:
									if (x-self.ac_x)**2 + (y-self.ac_y)**2<(range90deg*1.4142)**2:
										theta=radians(self.deg)
										x2,y2=-60*sin(theta), 60*cos(theta)
										x3,y3=60*sin(theta), -60*cos(theta)
										d2=(x-self.ac_x+x2)**2 + (y-self.ac_y+y2)**2
										d3=(x-self.ac_x+x3)**2 + (y-self.ac_y+y3)**2
										if d2>range90deg**2 and d3>range90deg**2:
											d1=(d2-d3)**2
											if d1<kakutei[3]:
												kakutei=(1,x,y,d1,player)	
									if kakutei[0]==0:
										if not 5<delta<355:
											kakutei=(1,x,y,kakutei[3],player)	

										
							now_area = to_coordinates(x,y)
							if self.final_type>0:
								final_block = "%s%s"%(self.area_x[0],self.area_y[0])
								if now_area == final_block:
									if self.final_type==1:
										y+=32
									elif self.final_type==2:
										y-=32
									elif self.final_type==3:
										x+=32
									elif self.final_type==4:
										x-=32
									danger = False
									if 0<=x<=511 and 0<=y<=511:
										now_area = to_coordinates(x,y)
										if now_area in self.destroyed_area:
											danger=True
									else:
										danger=True
									if danger:
										if self.final_damage:
											player.in_destroyed()										
										else:
											player.in_next_destroy()
									else:
										player.in_normalarea()
								else:
									player.in_destroyed()
							else:
								if now_area in self.destroyed_area:
									player.in_destroyed()
								elif now_area in self.nextdestroyarea:
									player.in_next_destroy()
								else:
									player.in_normalarea()
						else:
							player.in_normalarea()
			if pnum==0:
				return (0,0)
			if kakutei[0]==0:
				return (float(sumx/pnum), float(sumy/pnum))
			else:
				deader=False
				for player in self.blue_team.get_players():	
					if player.hp<=0:
						deader=True
						break
				if not deader:
					if (kakutei[1]-self.ac_x)**2 + (kakutei[2]-self.ac_y)**2<15**2:
						if seconds() - self.autobomb>30:
							kakutei[4].bombing()
							self.autobomb=seconds()
				return (kakutei[1],kakutei[2])

				

		def reset_game(self, player = None, territory = None):
			if self.destroy_call is not None:
				self.destroy_call.cancel()
				self.destroy_call=None
			if self.warning_call is not None:
				self.warning_call.cancel()
				self.warning_call= None
			if self.notice_call is not None:
				self.notice_call.cancel()
				self.notice_call=None
			if self.lastnotice_call is not None:
				self.lastnotice_call.cancel()
				self.lastnotice_call= None
			self.area_x = ["A","B","C","D","E","F","G","H"]
			self.area_y = ["1","2","3","4","5","6","7","8"]
			self.destroyed_area=[]
			self.nextdestroyarea = []
			self.drop_items={}
			self.final_type=0
			self.final_damage=0
			self.final_lines=[]
			self.autobomb=0

			tentpos=[]
			entitys=[]
			for i in range(16):
				move_object.object_type = i
				move_object.state = 1
				x,y = 0,0
				tentpos.append((x,y))
				z=0
				move_object.x = x
				move_object.y = y
				move_object.z = z
				entity_new=Territory(i,self,x,y,z)
				entity_new.progress=0.5
				entity_new.team=self.green_team
				entitys.append(entity_new)
				self.send_contained(move_object)
			self.entities = entitys

			self.next_marking_square_x=[]
			self.next_marking_square_y=[]
			self.next_marking_slash=[]
			self.prestart_time=True
			return protocol.reset_game(self, player, territory)

		def paint_ground(self,x,y,z,color):
			if 0<=x<=511 and 0<=y<=511 and z<=62:
				block_action = BlockAction()
				if z<0:
					z=0

					block_action.player_id = 32
					block_action.value = DESTROY_BLOCK
					block_action.x = x
					block_action.y = y
					block_action.z = z
					self.send_contained(block_action)
					self.map.remove_point(x, y, z)
				set_color = SetColor()
				set_color.value = make_color(*color)
				set_color.player_id = 32
				self.send_contained(set_color)
				block_action.player_id = 32
				block_action.value=BUILD_BLOCK
				block_action.x = x
				block_action.y = y
				block_action.z = z
				self.send_contained(block_action)
				self.map.set_point(x, y, z, color)

		def notice(self, message,type):
			if type == 0:
				self.notice_call = None
			elif type == 1:
				self.lastnotice_call = None
			self.send_chat(message)
			
		def area_destroy(self):
			self.destroyed_area.extend(self.nextdestroyarea)
			if len(self.area_x)>1:
				del_x = choice([0,-1])
				del_y = choice([0,-1])
				destroy_x = self.area_x.pop(del_x)
				destroy_y = self.area_y.pop(del_y)
				c_block = "%s%s"%(destroy_x,destroy_y)

				info = "Next destroy area is  '%s' and  '%s'."%(destroy_x,destroy_y)
				self.send_chat("%s  (%s sec later)"%(info, MAP_DESTROY_TIME))
				self.notice_call = callLater(MAP_DESTROY_TIME/2,self.notice, "%s  (%s sec later)"%(info, MAP_DESTROY_TIME/2),0)
				self.last_notice_call = callLater(MAP_DESTROY_TIME-5,self.notice, "%s  (5 sec later)"%info,1)

				self.nextdestroyarea = [c_block]
				for block_y in self.area_y:
					if block_y != destroy_y:
						self.nextdestroyarea.append("%s%s"%(destroy_x,block_y))
				for block_x in self.area_x:
					if block_x != destroy_x:
						self.nextdestroyarea.append("%s%s"%(block_x,destroy_y))
				line_x=1
				line_y=1
				toright=-1
				todown=-1
				if del_x==0:
					line_x = 63
					toright=1
				if del_y==0:
					line_y = 63
					todown=1
				x, y = coordinates(c_block)
				color = (255,0,0)
				self.next_marking_square_x=[]
				self.next_marking_square_y=[]
				self.next_marking_slash=[]
				for xx in range(512):
					yy=y+line_y
					if not (to_coordinates(xx,yy) in self.destroyed_area or to_coordinates(xx,yy) == c_block):
						self.next_marking_square_x.append((xx,yy))
				for yy in range(512):
					xx=x+line_x
					if not (to_coordinates(xx,yy) in self.destroyed_area or to_coordinates(xx,yy) == c_block):
						self.next_marking_square_y.append((xx,yy))

				for xx in range(512):
					for bb in range(32):
						yy=bb*32+xx*-1
						if 0<=yy<=511:
							xyarea = to_coordinates(xx,yy)
							if not xyarea in self.destroyed_area:
								if xyarea in self.nextdestroyarea:
									self.next_marking_slash.append((xx,yy))

				len_x = len(self.next_marking_square_x)
				len_y = len(self.next_marking_square_y)
				len_s = len(self.next_marking_slash)
				len_all = max(len_x, len_y) + len_s/2
				drawtime = len_all*BLOCK_SET_SPEED #sec
				self.warning_call = callLater(BLOCK_SET_SPEED,self.area_destroy_warning, toright, todown,0)
				self.destroy_call = callLater(MAP_DESTROY_TIME-drawtime-5,self.area_destroy_destroy, toright, todown,0)
			else:
				if self.final_type==0:
					self.final_line()
					self.nextdestroyarea = []
				self.final_destroy(True)

		def final_line(self):
			final_block = "%s%s"%(self.area_x[0],self.area_y[0])
			xc, yc = coordinates(final_block)
			self.final_lines=[]
			for xx in range(64):
				self.final_lines.append((xc+xx,yc+32))
			for yy in range(64):
				self.final_lines.append((xc+32,yc+yy))
			for xx in range(64):
				self.final_lines.append((xc+xx,yc))
				self.final_lines.append((xc+xx,yc+63))
			for yy in range(64):
				self.final_lines.append((xc,yc+yy))
				self.final_lines.append((xc+63,yc+yy))
			self.final_line_draw()

		def final_line_draw(self):
			color = (255,0,0)				
			self.final_line_call=None
			if len(self.final_lines)>1:
				x,y = self.final_lines.pop(-1)
				for z in range(63):
					if self.map.get_solid(x,y,z) and not (self.map.get_solid(x,y,z-1) or self.map.get_solid(x,y,z-2) or self.map.get_solid(x,y,z-3)):
						if not self.map.get_point(x,y,z)[1] == color:
							self.paint_ground(x,y,z-1,color)	
				self.final_line_call = callLater(BLOCK_SET_SPEED,self.final_line_draw)
			else:
				for (x,y) in self.final_lines:
					for z in range(63):
						if self.map.get_solid(x,y,z) and not (self.map.get_solid(x,y,z-1) or self.map.get_solid(x,y,z-2) or self.map.get_solid(x,y,z-3)):
							if not self.map.get_point(x,y,z)[1] == color:
								self.paint_ground(x,y,z-1,color)	

		def final_destroy(self,warning):
			limpos=[(0,0),(0,4),(4,0),(4,4),(8,0),(8,4),(1,1),(1,3),(2,2),(3,1),(3,3),(5,1),(5,3),(6,2),(7,1),(7,3)]
			final_block = "%s%s"%(self.area_x[0],self.area_y[0])
			xc, yc = coordinates(final_block)
			if warning:
				self.final_type = randint(1,4)
			self.final_damage = not warning
			entitys=[]
			for i in range(16):
				tx,ty = limpos[i][0]*8, limpos[i][1]*8
				if self.final_type%2:
					ty+=32
				if self.final_type>=3:
					x,y = xc+ty,yc+tx
				else:
					x,y = xc+tx,yc+ty
				move_object.object_type = i
				move_object.state = self.final_damage
				z=self.map.get_z(x,y)
				move_object.x = x
				move_object.y = y
				move_object.z = z
				entity_new=Territory(i,self,x,y,z)
				entity_new.progress=0
				entity_new.team=self.blue_team
				entitys.append(entity_new)
				self.send_contained(move_object)
			self.entities = entitys
			if warning:
				self.final_destroy_call = callLater(MAP_DESTROY_TIME/3,self.final_destroy,False)



		def area_destroy_warning(self, toright, todown, phase):
			self.warning_call = None
			color = (255,120,0)				
			finish=False
			if len(self.next_marking_square_x)>phase:
				x,y = self.next_marking_square_x[phase*toright]
				y += todown*-1
				if not self.map.get_point(x,y, self.map.get_z(x,y))[1] == color:
					self.paint_ground(x,y,self.map.get_z(x,y)-1,color)	
			if len(self.next_marking_square_y)>phase:
				x,y = self.next_marking_square_y[phase*todown]
				x += toright*-1
				if not self.map.get_point(x,y, self.map.get_z(x,y))[1] == color:
					self.paint_ground(x,y,self.map.get_z(x,y)-1,color)	
			if max(len(self.next_marking_square_x), len(self.next_marking_square_y))<=phase:
				phase_slash = phase- max(len(self.next_marking_square_x), len(self.next_marking_square_y))
				if phase_slash<len(self.next_marking_slash)/2.0:
					x,y = self.next_marking_slash[phase_slash]
					x-=1
					if not self.map.get_point(x,y, self.map.get_z(x,y))[1] == color:
						self.paint_ground(x,y,self.map.get_z(x,y)-1,color)	
					x,y = self.next_marking_slash[phase_slash]
					x+=1
					if not self.map.get_point(x,y, self.map.get_z(x,y))[1] == color:
						self.paint_ground(x,y,self.map.get_z(x,y)-1,color)	
					x,y = self.next_marking_slash[phase_slash+len(self.next_marking_slash)/2]
					x-=1
					if not self.map.get_point(x,y, self.map.get_z(x,y))[1] == color:
						self.paint_ground(x,y,self.map.get_z(x,y)-1,color)	
					x,y = self.next_marking_slash[phase_slash+len(self.next_marking_slash)/2]
					x+=1
					if not self.map.get_point(x,y, self.map.get_z(x,y))[1] == color:
						self.paint_ground(x,y,self.map.get_z(x,y)-1,color)	
				else:
					finish=True
			if not finish:
				self.warning_call = callLater(BLOCK_SET_SPEED,self.area_destroy_warning,toright, todown,phase+1)

		def area_destroy_destroy(self, toright, todown, phase):
			self.destroy_call = None
			color = (255,0,0)				
			finish=False
			if len(self.next_marking_square_x)>phase:
				x,y = self.next_marking_square_x[phase*toright]
				if not self.map.get_point(x,y, self.map.get_z(x,y))[1] == color:
					self.paint_ground(x,y,self.map.get_z(x,y)-1,color)	
			if len(self.next_marking_square_y)>phase:
				x,y = self.next_marking_square_y[phase*todown]
				if not self.map.get_point(x,y, self.map.get_z(x,y))[1] == color:
					self.paint_ground(x,y,self.map.get_z(x,y)-1,color)	
			if max(len(self.next_marking_square_x), len(self.next_marking_square_y))<=phase:
				phase_slash = phase- max(len(self.next_marking_square_x), len(self.next_marking_square_y))
				if phase_slash<len(self.next_marking_slash)/2.0:
					x,y = self.next_marking_slash[phase_slash]
					if not self.map.get_point(x,y, self.map.get_z(x,y))[1] == color:
						self.paint_ground(x,y,self.map.get_z(x,y)-1,color)	
					x,y = self.next_marking_slash[phase_slash+len(self.next_marking_slash)/2]
					if not self.map.get_point(x,y, self.map.get_z(x,y))[1] == color:
						self.paint_ground(x,y,self.map.get_z(x,y)-1,color)	
				else:
					finish=True
			if not finish:
				self.destroy_call = callLater(BLOCK_SET_SPEED,self.area_destroy_destroy,toright, todown,phase+1)

		def get_cp_entities(self):
			entities=[]
			tentpos=[]
			for i in range(16):
				entity=Territory(i,self,0,0,0)
				entity.team=None
				entities.append(entity)
			return entities



		def update_entities(self):
			map = self.map
			for entity in self.entities:
				if self.on_update_entity(entity):
					entity.update()

	return PUBGProtocol, PUBGConnection
