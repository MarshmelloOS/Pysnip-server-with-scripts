"""
autoheal script by yuyasato 20170430, update 20171202

"""

from commands import admin, add, name, get_team, alias
from pyspades.constants import *
from twisted.internet.reactor import callLater


HEAL_INTERVAL  = 0.05    ## /sec
HEAL_AMOUNT    = 1    ## heal HP per HEAL_INTERVAL
HEAL_LIMIT = 100  ## heal limit of one spawn  ( 0 = no limit )

HEAL_ONLY_CROUCHING = True	# heal only crouching
HEAL_ONLY_BLOCKHOLD = False	# heal only holding block
HEAL_ONLY_STATIC = True		# heal only No moving
STATIC_DELAY=3  # /sec		# needed time of static state to heal
NO_STATIC_ON_HIT = True		# static state is reseted on_hit

AUTOHEAL_BLUE  = True
AUTOHEAL_GREEN = True

@alias('autoheal')
@name('autohealtoggle')
@admin
def autohealtoggle(connection):
	if connection.protocol.autoheal_running:
		connection.protocol.autoheal_running=False
		return "Autoheal disabled"
	else:
		callLater(HEAL_INTERVAL*3,connection.protocol.autoheal_start)	
		return "Wait %s seconds. Autoheal enabled."%HEAL_INTERVAL*3
add(autohealtoggle)

@alias('autoheal_int')
@name('autoheal_interval')
@admin
def autoheal_interval(connection,value):
	global HEAL_INTERVAL
	HEAL_INTERVAL=float(value)
	return "autoheal set %sHP/%ssec"%(HEAL_AMOUNT, HEAL_INTERVAL)
add(autoheal_interval)

@alias('autoheal_amo')
@name('autoheal_amount')
@admin
def autoheal_amount(connection,value):
	global HEAL_AMOUNT
	HEAL_AMOUNT=int(value)
	return "autoheal set %sHP/%ssec"%(HEAL_AMOUNT, HEAL_INTERVAL)
add(autoheal_amount)

@alias('autoheal_lim')
@name('autoheal_limit')
@admin
def autoheal_limit(connection,value):
	global HEAL_LIMIT
	HEAL_LIMIT=int(value)
	return "autoheal limit set %s"%(HEAL_LIMIT)
add(autoheal_limit)

@alias('med')
@name('medkit_check')
def medkit_check(connection):
	return "You have %s medkits"%(connection.heal_limit)
add(medkit_check)

@alias('m')
@name('medkit_announce')
def medkit_announce(connection):
	if not (HEAL_ONLY_CROUCHING or HEAL_ONLY_BLOCKHOLD or HEAL_ONLY_STATIC):
		msg = "there is no medkit system."
	else:
		msg = "to using medkit, you should"
		if HEAL_ONLY_CROUCHING:
			msg+=" crouch"
		if HEAL_ONLY_BLOCKHOLD:
			if HEAL_ONLY_CROUCHING:
				msg+=" and"
			msg+=" hold block"
		if HEAL_ONLY_STATIC:
			if HEAL_ONLY_CROUCHING or HEAL_ONLY_BLOCKHOLD:
				msg+=" and"
			msg+=" no move for %s sec"%STATIC_DELAY
		msg+="."
	return msg
add(medkit_announce)

def apply_script(protocol, connection, config):

	class AutohealConnection(connection):
		autoheal_static = 0
		heal_limit = HEAL_LIMIT

		def moving_check(self):
				vz = (self.world_object.velocity.z)**2
				vw = self.world_object.up
				vs = self.world_object.down
				va = self.world_object.left
				vd = self.world_object.right
				vel = vz+va+vs+vd+vw
				if vel>0.001:
					self.autoheal_static=0
				return vel<0.001
					

		def on_hit(self, hit_amount, hit_player, type, grenade):
			if NO_STATIC_ON_HIT:
				self.autoheal_static=0
			return connection.on_hit(self, hit_amount, hit_player, type, grenade)

		def on_shoot_set(self, fire):
			self.autoheal_static=0
			return connection.on_shoot_set(self, fire)

		def on_animation_update(self, jump, crouch, sneak, sprint):
			self.autoheal_static=0
			return connection.on_animation_update(self, jump, crouch, sneak, sprint)

		def on_tool_changed(self, tool):
			self.autoheal_static=0
			return connection.on_tool_changed(self, tool)

		def on_secondary_fire_set(self, secondary):
			self.autoheal_static=0
			return connection.on_secondary_fire_set(self, secondary)

		def on_spawn(self, pos):
			self.autoheal_static=0
			self.heal_limit = HEAL_LIMIT
			return connection.on_spawn(self, pos)

	def on_grenade(self, time_left):
			self.autoheal_static=0
			return connection.on_grenade(self, time_left)

	def on_block_build_attempt(self, x, y, z):
			self.autoheal_static=0
			return connection.on_block_build_attempt(self, x, y, z)

	def on_line_build_attempt(self, points):
			self.autoheal_static=0
			return connection.on_line_build_attempt(self, points)

	class AutohealProtocol(protocol):
		autoheal_running = False

		def __init__(self, *arg, **kw):
			self.autoheal_running=False
			callLater(HEAL_INTERVAL*3,self.autoheal_start)
			callLater(3,self.autoheal_start)

			return protocol.__init__(self, *arg, **kw)

		def autoheal_start(self):
			if not self.autoheal_running:
				self.autoheal_running=True
				self.autoheal()
				self.static_check()

		def static_check(self):
			if self.autoheal_running:
				for player in self.blue_team.get_players():
					if player and player.world_object:
						player.autoheal_static += player.moving_check()
				for player in self.green_team.get_players():
					if player and player.world_object:
						player.autoheal_static += player.moving_check()
				callLater(1.0,self.static_check)

		
		def autoheal(self):
			if AUTOHEAL_BLUE:
				for player in self.blue_team.get_players():
					if player.heal_limit >0 or HEAL_LIMIT==0:
						if player.world_object.crouch or not HEAL_ONLY_CROUCHING:
							if player.tool ==BLOCK_TOOL or not HEAL_ONLY_BLOCKHOLD:
								player.moving_check()
								if player.autoheal_static>=STATIC_DELAY or not HEAL_ONLY_STATIC:
										if 100>player.hp>0:
											hp_temp = player.hp+HEAL_AMOUNT
											if hp_temp>100:
												hp_temp=100
											player.heal_limit -= hp_temp - player.hp
											if player.heal_limit<=0:
												player.send_chat("You don't have any medkits!")
											player.set_hp(hp_temp, type = FALL_KILL)
			if AUTOHEAL_GREEN:
				for player in self.green_team.get_players():
					if player.heal_limit >0 or HEAL_LIMIT==0:
						if player.world_object.crouch or not HEAL_ONLY_CROUCHING:
							if player.tool ==BLOCK_TOOL or not HEAL_ONLY_BLOCKHOLD:
								player.moving_check()
								if player.autoheal_static>=STATIC_DELAY or not HEAL_ONLY_STATIC:
										if 100>player.hp>0:
											hp_temp = player.hp+HEAL_AMOUNT
											if hp_temp>100:
												hp_temp=100
											player.heal_limit -= hp_temp - player.hp
											if player.heal_limit<=0:
												player.send_chat("You don't have any medkits!")
											player.set_hp(hp_temp, type = FALL_KILL)
			if self.autoheal_running:
				callLater(HEAL_INTERVAL,self.autoheal)

	return AutohealProtocol, AutohealConnection
