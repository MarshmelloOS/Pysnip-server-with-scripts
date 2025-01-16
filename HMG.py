"""
HMG script by yuyasato 20190119

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


MACHINEGUN_SPEED  = 0.12    ## /sec

@alias('mg_int')
@name('machinegun_interval')
@admin
def machinegun_interval(connection,value):
	global MACHINEGUN_SPEED
	MACHINEGUN_SPEED=float(value)
	return "MACHINEGUN_SPEED set %s sec"%(MACHINEGUN_SPEED)
add(machinegun_interval)

@alias('hmg')
@name('be_hmger')
def be_hmger(connection):
	connection.HMGER = not connection.HMGER
	if connection.HMGER:
		connection.set_weapon(0, False, False)
		connection.kill(type = CLASS_CHANGE_KILL)
		return "you are now machinegunnner"
	else:
		connection.kill(type = CLASS_CHANGE_KILL)
		return "you are no longer use machinegun"		
add(be_hmger)

def apply_script(protocol, connection, config):

	class HMGConnection(connection):
		HMGstatic = 0
		HMGER=False
		rapid_loop = None
		hmgready = False

		def moving_check(self):
				vz = (self.world_object.velocity.z)**2
				vw = self.world_object.up
				vs = self.world_object.down
				va = self.world_object.left
				vd = self.world_object.right
				vel = vz+va+vs+vd+vw+ (not self.world_object.crouch)
				if vel>0.001:
					self.static_end()
				return vel<0.001

		def on_animation_update(self, jump, crouch, sneak, sprint):
			if self.HMGER:
				self.static_end()
			return connection.on_animation_update(self, jump, crouch, sneak, sprint)

		def on_tool_changed(self, tool):
			if self.HMGER:
				self.static_end()
			return connection.on_tool_changed(self, tool)

		def on_spawn(self, pos):
			if self.HMGER:
				self.static_end()
			return connection.on_spawn(self, pos)

		def on_grenade(self, time_left):
			if self.HMGER:
				self.static_end()
			return connection.on_grenade(self, time_left)

		def resend_tool(self):
			set_tool.player_id = self.player_id
			set_tool.value = self.tool
			if self.weapon_object.shoot:
				self.protocol.send_contained(set_tool)
			else:
				self.send_contained(set_tool)
			if self.HMGER:
					weapon_reload.player_id = self.player_id
					stock = 666
					self.weapon_object.reset()
					weapon_reload.clip_ammo = self.weapon_object.current_ammo = 2
					weapon_reload.reserve_ammo = self.weapon_object.current_stock = stock	
					self.weapon_object.set_shoot(True)
					self.send_contained(weapon_reload)

		def static_end(self):
			if self.HMGER:
				self.rapid_hack_detect = True
				self.HMGstatic = 0
				self.hmg_ready=False
				weapon_reload.player_id = self.player_id
				stock = 666
				self.weapon_object.reset()
				weapon_reload.clip_ammo = self.weapon_object.current_ammo = 0
				weapon_reload.reserve_ammo = self.weapon_object.current_stock = stock	
				self.weapon_object.set_shoot(False)
				self.send_contained(weapon_reload)	

		def hmg_ok(self):
			if self.HMGER:
				if not self.hmg_ready:
					self.rapid_hack_detect = False
					self.send_chat("HMG available")
					if self.weapon_object.current_ammo<2:
						weapon_reload.player_id = self.player_id
						stock = 666
						self.weapon_object.reset()
						weapon_reload.clip_ammo = self.weapon_object.current_ammo = 2
						weapon_reload.reserve_ammo = self.weapon_object.current_stock =  stock	
						self.weapon_object.set_shoot(True)
						self.send_contained(weapon_reload)	
				self.hmg_ready=True

		def on_position_update(self):
			if self.HMGER:
				if self and self.world_object:
					vz = (self.world_object.velocity.z)**2
					vw = self.world_object.up
					vs = self.world_object.down
					va = self.world_object.left
					vd = self.world_object.right
					vel = vz+va+vs+vd+vw
					if vel>0.001:
						self.static_end()
			return connection.on_position_update(self)

		def rapid_looping(self):
			self.rapid_loop = None
			if self and self.world_object and self.tool==2:				
				if self.hmg_ready:
					self.resend_tool()
					self.rapid_loop = callLater(MACHINEGUN_SPEED, self.rapid_looping)
				else:
					self.static_end()

		def on_shoot_set(self, fire):
			if self.HMGER:
				if self.tool==2:				
					if fire:
						if self.hmg_ready:
							if self.rapid_loop is not None:
								self.rapid_loop.cancel()
							self.rapid_loop = None
							self.rapid_loop = callLater(MACHINEGUN_SPEED, self.rapid_looping)
						else:
							self.static_end()
					else:
						if self.rapid_loop is not None:
							self.rapid_loop.cancel()
						self.rapid_loop = None
						if self.hmg_ready:
							weapon_reload.player_id = self.player_id
							stock = 666
							self.weapon_object.reset()
							weapon_reload.clip_ammo = self.weapon_object.current_ammo = 2
							weapon_reload.reserve_ammo = self.weapon_object.current_stock = stock	
							self.weapon_object.set_shoot(True)
							self.send_contained(weapon_reload)
			return connection.on_shoot_set(self, fire)



	class HMGProtocol(protocol):
		HMGTMR_running = False

		def __init__(self, *arg, **kw):
			self.HMGTMR_running=False
			callLater(3,self.HMGTMRstart)

			return protocol.__init__(self, *arg, **kw)

		def HMGTMRstart(self):
			if not self.HMGTMR_running:
				self.HMGTMR_running=True
				self.HMGTMR()

		def static_check(self):
			if self.HMGTMR_running:
				for player in self.players.values():
					if player and player.world_object:
						if player.HMGER:
							player.HMGstatic += player.moving_check()
							if player.HMGstatic>=5:	
								player.hmg_ok()							
							elif player.HMGstatic>0:
								player.send_chat("HMG preparetion .... %d sec."%(5.0 - player.HMGstatic))	
		def HMGTMR(self):
			if self.HMGTMR_running:
				self.static_check()
				callLater(1.0,self.HMGTMR)

	return HMGProtocol, HMGConnection
