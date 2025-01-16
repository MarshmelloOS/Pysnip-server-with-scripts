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
joining_speed=512
lowlimit=128
speed_lim=4096

NOLAG_SLOWLOAD = True

@alias('nl')
def nowloading(connection):
	return "%s player in loading now"%len(connection.protocol.loadinger)
add(nowloading)

def apply_script(protocol, connection, config):

	class SlowmaploadConnection(connection):
		nextspeed = lowlimit
		loadstarttime=0
		maploadcounter=0
		presendmap=0
		pakelim = 10
		

		def send_map(self, data = None):
			if data is not None:
				self.map_data = data
				map_start.size = self.protocol.mapdatasize*1.1
				self.send_contained(map_start)
			elif self.map_data is None:
				return				

			if not self.map_data.data_left():
		#		print self.address[0], "fin", self.maploadcounter
				self.map_data = None
				if not self.protocol.allentered:
					self.protocol.leady_enter.append(self)
					self.checkfin()
				else:
					self.map_enter()
				return
			if not self in self.protocol.loadinger:
				self.protocol.loadinger.append(self)
				self.nextspeed=joining_speed
			else: 
				timepake = seconds()-self.loadstarttime
				persec = self.protocol.mapdatasize / 45  #byte/sec
				self.nextspeed = int(persec*timepake) #30pk / sec  1pk/0.04sec
			if self.protocol.mapdatasize - self.maploadcounter > speed_lim *30:
				self.pakelim=10
			elif self.protocol.mapdatasize - self.maploadcounter > speed_lim *15:
				self.pakelim=5
			else:
				self.pakelim=1
			self.loadstarttime=seconds()
			pakecycle=1
			if self.maploadcounter<5:
				if seconds()-self.presendmap<0.3:
					return
				readspeed=1
				self.presendmap=seconds()
			else:
				if seconds() - self.protocol.change_time<90 and self.protocol.firstmember!=[]:
					self.nextspeed = self.speedadjust()
					if self.nextspeed>speed_lim:
						pakecycle = self.nextspeed // speed_lim
						pakecycle = min(pakecycle,self.pakelim)
						self.nextspeed = int(self.nextspeed /pakecycle)
					readspeed = min(self.nextspeed,speed_lim)
				else:
					if self.nextspeed>joining_speed:
						pakecycle = self.nextspeed // joining_speed
						pakecycle = min(pakecycle,10)
						self.nextspeed = int(self.nextspeed /pakecycle)
					readspeed = min(self.nextspeed,joining_speed)
					if len(self.protocol.loadinger)>0:
						if len(self.protocol.connections) > 6:
							readspeed/=len(self.protocol.loadinger)
					readspeed = max(lowlimit,readspeed)
			for _ in xrange(pakecycle):
				if not self.map_data.data_left():
					break
				map_data.data = self.map_data.read(readspeed)
		#		print self.address[0], len(map_data.data) , self.maploadcounter
				self.maploadcounter+=len(map_data.data) 
				self.send_contained(map_data)

		def speedadjust(self):
			if self.protocol.allentered or len(self.protocol.leady_enter)>0:
				return int(speed_lim*self.pakelim)
			topcount = self.maploadcounter
			bottomcount = self.maploadcounter
			for player in self.protocol.changeing_players:
				if player.maploadcounter>topcount:
					topcount = player.maploadcounter
				elif player.maploadcounter<bottomcount:
					bottomcount = player.maploadcounter
			if topcount==bottomcount:
				justspeed = speed_lim
			elif topcount-bottomcount<speed_lim*self.pakelim-lowlimit:
				justspeed = speed_lim*self.pakelim-(self.maploadcounter-bottomcount)
			else:
				delta=topcount-bottomcount*1.0
				lv = (topcount-self.maploadcounter)*1.0/delta

				justspeed=lv*(speed_lim*self.pakelim-lowlimit)+lowlimit
			justspeed=max(lowlimit,justspeed)
			return int(justspeed)

		def checkfin(self):
			if len(self.protocol.leady_enter)==1:
				callLater(6,self.protocol.all_map_enter_check)
			if self in self.protocol.changeing_players:
				self.protocol.changeing_players.remove(self)
			if self.protocol.changeing_players == []:
				self.protocol.all_map_enter_check()

		def map_enter(self):
			self.maploadcounter=0
			self.map_data = None
			for data in self.saved_loaders:
				packet = enet.Packet(str(data), enet.PACKET_FLAG_RELIABLE)
				self.peer.send(0, packet)
			self.saved_loaders = None
			self.on_join()
			if self in self.protocol.loadinger:
				self.protocol.loadinger.remove(self)
			if self in self.protocol.leady_enter:
				self.protocol.leady_enter.remove(self)
			if self in self.protocol.changeing_players:
				self.protocol.changeing_players.remove(self)
			if self in self.protocol.firstmember:
				self.protocol.firstmember.remove(self)		

		def on_disconnect(self):
			if self in self.protocol.loadinger:
				self.protocol.loadinger.remove(self)
			if self in self.protocol.leady_enter:
				self.protocol.leady_enter.remove(self)
			if self in self.protocol.changeing_players:
				self.protocol.changeing_players.remove(self)	
			if self in self.protocol.firstmember:
				self.protocol.firstmember.remove(self)		
			return connection.on_disconnect(self)

		def on_connect(self):
			if seconds() - self.protocol.change_time<90 and self.protocol.firstmember!=[]:
				return connection.on_connect(self)
			if len(self.protocol.connections) > 6:
				if len(self.protocol.loadinger)>3:
					self.disconnect(ERROR_FULL)
					return
			return connection.on_connect(self)

	class SlowmaploadProtocol(protocol):

		loadinger=[]
		mapdatasize=114514
		map_changed_time=0
		leady_enter=[]
		changeing_players=[]
		firstmember=[]
		change_time=0
		allentered=False

		def all_map_enter(self):
			self.allentered=True
			leady_enter=[]
			for player in self.leady_enter:
				leady_enter.append(player)
			for player in leady_enter:
				player.map_enter()
			self.leady_enter=[]

		def all_map_enter_check(self):
			if not self.allentered:
				self.all_map_enter()

		def cut_late_player(self):
			if len(self.changeing_players)>=10:
				topcount=0
				sumcount=0
				for player in self.changeing_players:
					sumcount += player.maploadcounter
					if player.maploadcounter>topcount:
						topcount = player.maploadcounter
				avecount = sumcount*1.0/len(self.changeing_players)
				for player in self.changeing_players:
					if player.maploadcounter<topcount/2 and player.maploadcounter<avecount*0.75:
						if len(self.changeing_players)>=6:
							self.changeing_players.remove(player)						
				callLater(5,self.cut_late_player)
			if self.changeing_players == []:
				self.all_map_enter_check()

		def on_map_change(self, map):
			generator = map.get_generator()
			compressor=zlib.compressobj(COMPRESSION_LEVEL)
			self.mapdatasize= len(compressor.compress(generator.get_data(1024*1024*2)))
			self.change_time=seconds()
			self.allentered=False
			for player in self.connections:
				player= self.connections[player]
				self.changeing_players.append(player) 
				self.firstmember.append(player) 
			callLater(15,self.cut_late_player)
			callLater(90,self.all_map_enter_check)
			return protocol.on_map_change(self, map)

	return SlowmaploadProtocol, SlowmaploadConnection