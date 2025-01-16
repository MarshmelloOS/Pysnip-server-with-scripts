# -*- coding: utf-8 -*-
"""
大型マップを任意サイズに切り取るスクリプト

MAPSIZE_X =	横幅
MAPSIZE_Y =	縦幅
OUT_AREA_DAMAGE = 場外ダメージ
MAX_SEA_RATIO = 切り取った領域の内の海の比率の許容限度(%)
	大きくすると海ばっかりの部分が切り取られる可能性があるが、小さすぎると切り取り試行回数が増えて鯖落ちリスクがある

マップローテーション先頭には海以外何もない空マップを入れてください（nullpo.vxl等）


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
MAX_SEA_RATIO = 40      #(%)

MAPSIZE_X =	256
MAPSIZE_Y =	128


def apply_script(protocol,connection,config):
	class MapcutterProtocol(protocol):
		use_map = []

		def on_map_change(self, map):
			for x in xrange(MAPSIZE_X):
				for y in xrange(MAPSIZE_Y):
					for z in xrange(64):
						color= self.use_map[x][y][z]
						if color is not None:
							map.set_point(x+256-MAPSIZE_X/2, y+256-MAPSIZE_Y/2, z, color)
			protocol.on_map_change(self, map)

#		def set_map(self, map):	
#			protocol.set_map(self, map)

	#	def on_advance(self, map):


		def advance_rotation(self, message = None):
			self.set_time_limit(False)

			if self.planned_map is None:
				self.planned_map = self.map_rotator.next()
			while self.planned_map == self.maps[0]:
				self.planned_map = self.map_rotator.next()

			map = self.planned_map

			try:
				map_info = self.get_map(map)
			except MapNotFound, e:
				return e

			mapd=map_info.data	#今ロードしたマップのデータを読んだ
			realmapname=map_info.rot_info.name
			print "rn", realmapname
			self.use_map = []
			all = MAPSIZE_X*MAPSIZE_Y*1.0
			searatio=0
			while searatio<MAX_SEA_RATIO:
				cut_x=randint(0,511-MAPSIZE_X)
				cut_y=randint(0,511-MAPSIZE_Y)
				land = mapd.count_land(cut_x,cut_y, cut_x+MAPSIZE_X, cut_y+MAPSIZE_Y)
				searatio=land/all*100
				print searatio
			for x in xrange(cut_x, cut_x+MAPSIZE_X):
				self.use_map.append([])
				for y in xrange(cut_y, cut_y+MAPSIZE_Y):
					self.use_map[x-cut_x].append([])
					sea_points = mapd.get_z(x,y)==64
					for z in xrange(64):
						color= mapd.get_color(x, y, z)
						self.use_map[x-cut_x][y-cut_y].append(color)

			#マップを空マップに変更
			map = VXLData()
			for x in range(512):
				for y in range(512):
					map.set_point(x, y, 63, SEA_COLOR)
			open('./maps/mapcutter.vxl', 'wb').write(map.generate())

			mapl = self.get_map_rotation()
			maplf = self.get_map_rotation()
			mapl.insert(0, "mapcutter")
			self.set_map_rotation(mapl, False)
			map = self.maps[0]
			map_info = self.get_map(map)

			self.set_map_rotation(maplf, False)


			self.planned_map = None
			self.on_advance(map)
			if message is None:
				self.set_map_name(map)
			else:
				self.send_chat('%s Next map: %s.' % (message, realmapname),irc = True)
				reactor.callLater(10, self.set_map_name, map)



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

		def on_line_build_attempt(self, points):
			for point in points:
				if self.invalid_build_position(*point):
					return False
			return connection.on_line_build_attempt(self, points)

	return MapcutterProtocol,MapcutterConnection