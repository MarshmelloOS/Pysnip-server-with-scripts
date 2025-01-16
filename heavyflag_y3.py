"""
HeavyFlag, a OneCTF adaptation
by Shrub, originally by Yourself

References: onectf.py, koth.py
"""

from pyspades.constants import *
from commands import add, admin
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.internet.reactor import seconds,callLater
import math, random
from commands import alias,admin, add, name 

from pyspades import contained as loaders

intel_drop = loaders.IntelDrop()
intel_pickup = loaders.IntelPickup()
intel_capture = loaders.IntelCapture()

FLAG_SPAWN_POS = (256, 256)
HIDE_POS = (0, 0, 63)

POINT_TIME=10  #sec
INTEL_TRACE_FREQ = 10  #sec

FLYINTEL_ALTITUDE = -500  #bk

SPAWN_RADIUS = 60

SPAWN_SIGMA=SPAWN_RADIUS/3


@alias('ptt')			
@name('pointtime')		
def pointtime(connection, value):
	global POINT_TIME
	POINT_TIME = int(value)
	return	POINT_TIME+"s/point"
add(pointtime)

@alias('itt')		
@name('tracetime')		
def tracetime(connection, value):
	global INTEL_TRACE_FREQ
	INTEL_TRACE_FREQ = int(value)
	return	INTEL_TRACE_FREQ+"sec/pos"
add(tracetime)

@alias('spr')	
@name('spawnrad')		
def spawnrad(connection, value):
	global SPAWN_RADIUS
	SPAWN_RADIUS = float(value)
	return	SPAWN_RADIUS+":bk range"
add(spawnrad)

def apply_script(protocol, connection, config):

	class HeavyFlagProtocol(protocol):
		game_mode = CTF_MODE
		intel_freq_count = 0

		def __init__(self, *arg, **kw):
			protocol.__init__(self, *arg, **kw)
			callLater(5, self.onesec_loop)

		def on_base_spawn(self, x, y, z, base, entity_id):
			return HIDE_POS

		def onesec_loop(self):
			blue_flagger = self.green_team.flag.player
			green_flagger = self.blue_team.flag.player
			if not ((blue_flagger is None) and (green_flagger is None)):
				if blue_flagger is not None:
					flag_team = self.blue_team
					flagger = blue_flagger
				elif green_flagger is not None:
					flag_team = self.green_team
					flagger = green_flagger
				flagger.intel_holding_count+=1
				self.intel_freq_count+=1
				if self.intel_freq_count>=INTEL_TRACE_FREQ:
					self.intel_freq_count=0
					flag_team.flag.set(flagger.world_object.position.x,flagger.world_object.position.y, FLYINTEL_ALTITUDE)
					flag_team.flag.update()
				if flagger.intel_holding_count>=POINT_TIME:
					flagger.intel_holding_count=0
					flagger.capture_flag()
					flagger.take_flag()
			callLater(1.0, self.onesec_loop)

		def onectf_reset_flag(self, flag):
			z = self.map.get_z(*self.one_ctf_spawn_pos)
			pos = (self.one_ctf_spawn_pos[0], self.one_ctf_spawn_pos[1], z)
			if flag is not None:
				flag.player = None
				flag.set(*pos)
				flag.update()
			return pos

		def onectf_reset_flags(self):
			self.onectf_reset_flag(self.blue_team.flag)
			self.onectf_reset_flag(self.green_team.flag)
		
		def on_game_end(self):
			self.onectf_reset_flags()
			return protocol.on_game_end(self)

		def on_map_change(self, map):
			self.one_ctf_spawn_pos = FLAG_SPAWN_POS
			"""
			extensions = self.map_info.extensions
			if extensions.has_key('one_ctf'):
				self.one_ctf = extensions['one_ctf']
			if not self.one_ctf and extensions.has_key('reverse_one_ctf'):
				self.reverse_one_ctf = extensions['reverse_one_ctf']
			if extensions.has_key('one_ctf_spawn_pos'):
				self.one_ctf_spawn_pos = extensions['one_ctf_spawn_pos']
			"""
			return protocol.on_map_change(self, map)

		def on_flag_spawn(self, x, y, z, flag, entity_id):
			pos = self.onectf_reset_flag(flag.team.other.flag)
			protocol.on_flag_spawn(self, pos[0], pos[1], pos[2], flag, entity_id)
			return pos

	class HeavyFlagConnection(connection):
		intel_holding_count=0

		def on_flag_take(self):
			self.intel_holding_count=0
			flag = self.team.flag
			if flag.player is None:
				flag.set(self.world_object.position.x,self.world_object.position.y, FLYINTEL_ALTITUDE)
				flag.update()
			else:
				return False
			return connection.on_flag_take(self)

		def on_spawn_location(self, pos):
			teki_flagger = self.team.flag.player
			mikata_flagger = self.team.other.flag.player
			tm=1
			if teki_flagger is None and mikata_flagger is None :
				xm = self.team.flag.x
				ym = self.team.flag.y
				tm=3
			elif mikata_flagger is not None:
				xm = mikata_flagger.world_object.position.x
				ym = mikata_flagger.world_object.position.y
			elif teki_flagger is not None:
				xm = teki_flagger.world_object.position.x
				ym = teki_flagger.world_object.position.y
				tm=3
			x=y=0
			while True:
				theta = random.uniform(0,360)
				g = random.gauss(0, SPAWN_SIGMA)
				x=xm+(SPAWN_RADIUS*tm*math.cos(math.radians(theta)))+g
				y=ym+(SPAWN_RADIUS*tm*math.sin(math.radians(theta)))+g
				if 1<x<510 and 1<y<510:
					break
			pos = (x,y,self.protocol.map.get_z(x, y)-2.7)
			return pos	

		def on_flag_drop(self):
			self.intel_holding_count=0
			flag = self.team.flag
			position = self.world_object.position
			x, y, z = int(position.x), int(position.y), max(0, int(position.z))
			z = self.protocol.map.get_z(x, y, z)
			flag.set(x, y, z)
			flag.update()
			return connection.on_flag_drop(self)

	return HeavyFlagProtocol, HeavyFlagConnection