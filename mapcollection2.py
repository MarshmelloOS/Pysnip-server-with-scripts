# -*- coding: utf-8 -*-
"""
map colection 

by yuyasato


"""

from commands import add, admin
from pyspades.contained import BlockAction, SetColor
from pyspades.constants import *
from commands import add, admin, name, alias, join_arguments
from math import *
from random import randint, uniform, choice,triangular
from pyspades.contained import *
from pyspades.server import *
from pyspades.common import *
from pyspades.server import block_action
from pyspades.contained import BlockAction, SetColor
from commands import *
import os.path
import json
from twisted.internet.reactor import callLater, seconds
from pyspades.contained import *
from pyspades.server import *
from pyspades.common import *

KAKUNIN_MODE = True
@alias('sv')
@name('savemode')
def savemode(connection,type = "nanimokaitenai"):
	if type == "nanimokaitenai":
		type = connection.savetype
	if connection.savemode!=0:
		connection.savemode=0
		return "cancel sita"
	if type == "none":
		return "type sentaku siro !!!!!!"
	connection.savemode=1
	connection.savetype=type
	return "type:%s   kukaku hidari ue wo tataku."%connection.savetype

add(savemode)

@alias('be')
@name('bell')
def bell(connection):
	print "\a"
	return "piro-n"
add(bell)


@alias('hy')
@name('hyoji')
def hyoji(connection, type):
	global TYPE
	TYPE = type
	return type
add(hyoji)

TYPE="test"#　表示するフォルダ　

AREASIZE=64

def apply_script(protocol, connection, config):
	class MapcollectionProtocol(protocol):

		def on_map_change(self, map):
			if KAKUNIN_MODE:
				type=TYPE
				for column in range(512//AREASIZE):
					for row in range(512//AREASIZE):
						x0,y0,z0 = row*AREASIZE, column*AREASIZE,0
						name = column*(512//AREASIZE) + row
						if os.path.exists('./mapcollection/%s/%s.txt'%(type,name)):
							with open('./mapcollection/%s/%s.txt'%(type,name), 'rb') as file:
								data = json.load(file)
						else:
							break

						counter_x=0
						counter_y=0
						counter_z=0
						
						for xx in data:
							counter_y=0
							for yy in xx:
								counter_z=0
								for zz in yy:
									if zz is not None:
										color = zz
										color= (color[0],color[1],color[2])
										self.map.set_point(counter_x+x0,counter_y+y0,counter_z+z0,color)
									counter_z+=1
								counter_y+=1
							counter_x+=1
			protocol.on_map_change(self, map)


	class MapcollectionConnection(connection):
		savemode=0
		savetype="none"
		savepoint_x, savepoint_y = 0,0
		def on_block_destroy(self, x, y, z, value):
			if self.savemode ==2:
				self.savemode=0

				self.savememori=[]
				x0,y0 =self.savepoint_x, self.savepoint_y
				if x0<x and y0<y:
					for xx in range(x-x0+1):
						self.savememori.append([])
						for yy in range(y-y0+1):
							self.savememori[xx].append([])
							for zz in range(64):
								color= self.protocol.map.get_color(x0+xx, y0+yy, zz)
								self.savememori[xx][yy].append(color)
					for numid in range(60000):
						name=str(numid)
						if not os.path.exists('./mapcollection/%s/%s.txt'%(self.savetype,name)):
							with open('./mapcollection/%s/%s.txt'%(self.savetype,name), 'w') as file:
								json.dump(self.savememori, file, indent = 4)
							break
					print "type: %s, name:%s.txt"%(self.savetype,name)
					print self.protocol.map_info.name , (x0,y0),(x,y)
					mean_x, mean_y = (x0+x)/2,  (y0+y)/2
					dtsize_x, dtsize_y = x-x0,y-y0
					strdata = "%s.txt : %s , %s,  size: %s x %s , pos:(%s,%s)-(%s,%s)"%(name, self.protocol.map_info.name,  to_coordinates(mean_x,mean_y), dtsize_x, dtsize_y, x0,y0,x,y)
					f = open('./mapcollection/%s/data.txt'%(self.savetype), 'a') 
					f.write(strdata+'\n') 
					f.close()
					self.put_sora(mean_x, mean_y,0,(255,0,0))

					self.protocol.send_chat(" 2 : saved. type: %s, name:%s.txt"%(self.savetype,name))
				else:
					self.protocol.send_chat("error!! junban ga okasii")
					print "error", (x0,y0),(x,y)
			
				return False
			elif self.savemode ==1:
				self.savepoint_x, self.savepoint_y = x,y
				self.savemode=2
				self.send_chat(" 1 : hidariue kettei sita. tugi migisita.")
				return False
			return False

		def put_sora(self,x,y,z,color):
			color = (255,0,0)
			for xx in [-2,-1,0,1,2]:
				for yy in [-2,-1,0,1,2]:			
					if self.protocol.map.get_solid(x+xx,y+yy,z):
						block_action = BlockAction()
						block_action.player_id = self.player_id
						block_action.value = DESTROY_BLOCK
						block_action.x = x+xx
						block_action.y = y+yy
						block_action.z = z
						self.protocol.send_contained(block_action)
						self.protocol.map.remove_point(x+xx,y+yy,z)
			for xx in [-2,-1,0,1,2]:
				for yy in [-2,-1,0,1,2]:	
					block_action = BlockAction()
					set_color = SetColor()
					set_color.value = make_color(*color)
					set_color.player_id = 32
					self.protocol.send_contained(set_color)
					block_action.player_id = 32
					block_action.value=BUILD_BLOCK
					block_action.x = x+xx
					block_action.y = y+yy
					block_action.z = z
					self.protocol.send_contained(block_action)
					self.protocol.map.set_point(x+xx,y+yy,z, color)
			color = (0,255,0)
			for xx in [-3,-2,-1,0,1,2,3]:
				for yy in [-3,-2,-1,0,1,2,3]:	
					block_action = BlockAction()
					set_color = SetColor()
					set_color.value = make_color(*color)
					set_color.player_id = 32
					self.protocol.send_contained(set_color)
					block_action.player_id = 32
					block_action.value=BUILD_BLOCK
					block_action.x = x+xx
					block_action.y = y+yy
					block_action.z = z
					self.protocol.send_contained(block_action)
					self.protocol.map.set_point(x+xx,y+yy,z, color)



	return MapcollectionProtocol, MapcollectionConnection