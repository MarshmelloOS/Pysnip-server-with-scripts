"""
slow map load to make lagless server
by yuyasato 20170316
"""

from pyspades.constants import *
from pyspades import contained as loaders
from twisted.internet.reactor import callLater,seconds
from commands import alias,admin, add, name, get_team, get_player,where_from
map_data = loaders.MapChunk()
map_start = loaders.MapStart()
import enet
import os
import zlib

COMPRESSION_LEVEL = 9
joining_speed=100000

@alias('slow')
def loadslow(connection):
	global joining_speed
	if joining_speed==128:
		joining_speed=100000
		return "load high speed set"
	else:
		joining_speed=128
		return "load slow speed set"
add(loadslow)

def apply_script(protocol, connection, config):
	class SlowmaploadConnection(connection):
		nextspeed = 128
		loadstarttime=0
		maploadcounter=0

		def send_map(self, data = None):
			if data is not None:
				self.map_data = data
				map_start.size = self.protocol.mapdatasize
				self.send_contained(map_start)
			elif self.map_data is None:
				return				
			if not self.map_data.data_left():
				print
				print self.protocol.map_info.name, "datasize", self.maploadcounter
				print 
				self.map_data = None
				self.map_enter()
				return
			readspeed = joining_speed

			for _ in xrange(10):
				if not self.map_data.data_left():
					break
				map_data.data = self.map_data.read(readspeed)
				self.maploadcounter+=len(map_data.data) 
				self.send_contained(map_data)

		def map_enter(self):
			self.maploadcounter=0
			self.map_data = None
			for data in self.saved_loaders:
				packet = enet.Packet(str(data), enet.PACKET_FLAG_RELIABLE)
				self.peer.send(0, packet)
			self.saved_loaders = None
			self.on_join()


	class SlowmaploadProtocol(protocol):
		mapdatasize=114514

		def on_map_change(self, map):
			generator = map.get_generator()
			compressor=zlib.compressobj(COMPRESSION_LEVEL)
			self.mapdatasize= len(compressor.compress(generator.get_data(1024*1024*2)))
			return protocol.on_map_change(self, map)

	return SlowmaploadProtocol, SlowmaploadConnection