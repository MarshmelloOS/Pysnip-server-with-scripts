# -*- coding: utf-8 -*-
"""
大型マップを任意サイズに切り取るスクリプト

MAPSIZE_X =	横幅
MAPSIZE_Y =	縦幅
OUT_AREA_DAMAGE = 場外ダメージ
MIN_LAND_RATIO = 切り取った領域の内の陸の比率の許容限度(%)
	小さくすると海ばっかりの部分が切り取られる可能性があるが、小さすぎると切り取り試行回数が増えて鯖落ちリスクがある



mapcutter 
20180224 yuyasato
"""


from itertools import product
from random import *
from math import floor
from pyspades.server import block_action
from pyspades.contained import BlockAction, SetColor
from commands import *
from commands import admin, add, name, get_team, get_player,alias
from pyspades.contained import *
from pyspades.server import *
from pyspades.common import *
from random import randint
from twisted.internet.reactor import callLater, seconds
from pyspades.vxl import VXLData


SEA_COLOR = (100,0,0)

OUT_AREA_DAMAGE = 200
MIN_LAND_RATIO = 75      #(%)
MAX_LAND_RATIO_EACH_TEAM  = 20      #(%)

MAPSIZE_X =	500
MAPSIZE_Y =	100

@alias('nm')
@name('nextmaps')
def nextmaps(connection):
	connection.protocol.nextmap()
add(nextmaps)


def apply_script(protocol,connection,config):
	class MapcutterProtocol(protocol):
		use_map = []
		usemap_xy=[0,0]
		mapd=None

		def on_map_change(self, map):

			for x in xrange(MAPSIZE_X):
				for y in xrange(MAPSIZE_Y):
					for z in xrange(64):
						color= self.use_map[x][y][z]
						if color is not None:
							map.set_point(x+256-MAPSIZE_X/2, y+256-MAPSIZE_Y/2, z, color)
			for x in xrange(MAPSIZE_X):
				for z in xrange(63):
					map.set_point(x+256-MAPSIZE_X/2, MAPSIZE_Y+256-MAPSIZE_Y/2, z, (255,200,200))
					map.set_point(x+256-MAPSIZE_X/2, 256-MAPSIZE_Y/2-1, z, (255,200,200))
					
			callLater(0.1, self.nextmap_calc)

			protocol.on_map_change(self, map)

		def set_map(self, map):	

			map = VXLData()
			for x in range(512):
				for y in range(512):
					map.set_point(x, y, 63, SEA_COLOR)

			protocol.set_map(self, map)

	#	def on_advance(self, map):

		def nextmap_calc(self, first=False):
			damedesu = True

			if self.planned_map is None:
				self.planned_map = self.map_rotator.next()

			while damedesu:
				map = self.planned_map

				try:
					map_info = self.get_map(map)
				except MapNotFound, e:
					return e

				mapd=map_info.data	#今ロードしたマップのデータを読んだ
				self.mapd=mapd
				self.use_map = []
				all = MAPSIZE_X*MAPSIZE_Y*1.0
				landratio=0
				landratio_b=100
				landratio_g=1
				counter=0
				damedesu = False
				while landratio<MIN_LAND_RATIO or not ( -1*MAX_LAND_RATIO_EACH_TEAM < landratio_b - landratio_g < MAX_LAND_RATIO_EACH_TEAM):
					cut_x=randint(0,511-MAPSIZE_X)
					cut_y=randint(0,511-MAPSIZE_Y)
					land = mapd.count_land(cut_x,cut_y, cut_x+MAPSIZE_X, cut_y+MAPSIZE_Y)
					landratio=land/all*100

					land_b = mapd.count_land(cut_x,cut_y, cut_x+MAPSIZE_X/2, cut_y+MAPSIZE_Y)
					landratio_b=land_b/(all/2)*100

					land_g = mapd.count_land(cut_x+MAPSIZE_X/2,cut_y, cut_x+MAPSIZE_X, cut_y+MAPSIZE_Y)
					landratio_g=land_g/(all/2)*100
					counter+=1
					if counter >=100:
						damedesu = True
						print "damedesu"
						self.planned_map = self.map_rotator.next()
						break
			self.usemap_xy =[cut_x,cut_y]

			if first:
				self.nextmap()
			else:
				callLater(0.1, self.nextmap)

		def nextmap(self):

			mapd=self.mapd
			cut_x,cut_y = self.usemap_xy[0],self.usemap_xy[1]
			for x in xrange(cut_x, cut_x+MAPSIZE_X):
				self.use_map.append([])
				for y in xrange(cut_y, cut_y+MAPSIZE_Y):
					self.use_map[x-cut_x].append([])
					sea_points = mapd.get_z(x,y)==64
					for z in xrange(64):
						color= mapd.get_color(x, y, z)
						self.use_map[x-cut_x][y-cut_y].append(color)

		def advance_rotation(self, message = None):
			self.startsec = seconds()

			self.set_time_limit(False)

			if self.planned_map is None:
				self.nextmap_calc(True)

			map = self.planned_map

			self.planned_map = None
			self.on_advance(map)

			if message is None:
				self.set_map_name(map)
			else:
				self.send_chat('%s Next map: %s.' % (message, map.full_name),irc = True)
				reactor.callLater(10, self.set_map_name, map)

		def on_world_update(self):
			for player in self.blue_team.get_players():
				if player.hp:
					x,y,z = player.world_object.position.get()
					if not(256-MAPSIZE_X/2<x<256+MAPSIZE_X/2 and 256-MAPSIZE_Y/2<y<256+MAPSIZE_Y/2):
						player.set_hp(player.hp - OUT_AREA_DAMAGE)
			for player in self.green_team.get_players():
				if player.hp:
					x,y,z = player.world_object.position.get()
					if not(256-MAPSIZE_X/2<x<256+MAPSIZE_X/2 and 256-MAPSIZE_Y/2<y<256+MAPSIZE_Y/2):
						player.set_hp(player.hp - OUT_AREA_DAMAGE)
			protocol.on_world_update(self)


	class MapcutterConnection(connection):

		def on_position_update(self):
			x,y,z = self.world_object.position.get()
			if not(256-MAPSIZE_X/2<x<256+MAPSIZE_X/2 and 256-MAPSIZE_Y/2<y<256+MAPSIZE_Y/2):
				self.set_hp(self.hp - OUT_AREA_DAMAGE)
			return connection.on_position_update(self)

		def invalid_build_position(self, x, y, z):
			if 256-MAPSIZE_X/2-1<x<256+MAPSIZE_X/2+1 and 256-MAPSIZE_Y/2-1<y<256+MAPSIZE_Y/2+1:
				return False
			return True

		def on_block_build_attempt(self, x, y, z):
			if self.invalid_build_position(x, y, z):
				return False
			return connection.on_block_build_attempt(self, x, y, z)

		def on_spawn_location(self, pos):
			pos2 = connection.on_spawn_location(self, pos)
			if pos==pos2 or pos2==None:
				y = uniform(256-MAPSIZE_Y/2+2,256+MAPSIZE_Y/2-2)
				if self.team == self.protocol.blue_team:	
					x = uniform(256-MAPSIZE_X/2+2,256-MAPSIZE_X/4-2)
				elif self.team == self.protocol.green_team:
					x = uniform(256+MAPSIZE_X/2-2,256+MAPSIZE_X/4-2)
				else:
					return pos2
				z = self.protocol.map.get_z(x,y) - 2.7
				return x,y,z
			else:
				return pos2

		def on_line_build_attempt(self, points):
			for point in points:
				if self.invalid_build_position(*point):
					return False
			return connection.on_line_build_attempt(self, points)

	return MapcutterProtocol,MapcutterConnection