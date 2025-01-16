# -*- coding: utf-8 -*-
"""
テントとインテルが動くよ

佐藤裕也

"""
#ここからスクリプト

from pyspades import contained as loaders
from twisted.internet import reactor
from commands import alias,admin, add, name 
import random
import math


b_base_move  = 1		#青テント動かすか　1 or 0
g_base_move  = 1		#緑テント動かすか　1 or 0
rb=200					#テント周回半径[block]
rotatespeed=0.01#0.0006		#テント回転速度0.04で歩くぐらいの速さ

SPEED = 'rotate speed {r}'
RB = 'RB {r}'

@alias('rs')			#回転速度変更コマンド
@name('rotatespeeds')		
def rotatespeeds(connection, value):
	global rotatespeed
	rotatespeed = float(value)
	return	SPEED.format(r = value)
add(rotatespeeds)	

@alias('rb')			#回転半径変更コマンド
@name('rotatebases')		
def rotatebases(connection, value):
	global rb
	rb = float(value)
	return	RB.format(r = value)
add(rotatebases)	


move_object = loaders.MoveObject()

def apply_script(protocol,connection,config):

	class TentmoveConnection(connection):
		moving = 0
		stoploop = 0
		ori=150			#初期位置　（マップ右を0degとして反時計回り）

		def on_spawn(self, pos):
			if not self.moving:
				self.stoploop=0
				reactor.callLater(0.1,self.tentmove)
			return connection.on_spawn(self, pos)

		def tentmove(self):
			self.moving=1
			if b_base_move: 
	#blue base move

				move_object.object_type = 2
				b_base = self.protocol.blue_team.base
				x = rb*math.sin(math.radians(TentmoveConnection.ori)) + 256
				y = rb*math.cos(math.radians(TentmoveConnection.ori)) + 256
				z=self.protocol.map.get_z(x,y)
				location = [x,y,z]
				b_base.set(*location)
				move_object.x = x
				move_object.y = y
				move_object.z = z
				self.send_contained(move_object)

			if g_base_move: 
	#green base move
				move_object.object_type = 3
				g_base = self.protocol.green_team.base

				x = rb*math.sin(math.radians(TentmoveConnection.ori+180)) + 256
				y = rb*math.cos(math.radians(TentmoveConnection.ori+180)) + 256
				z=self.protocol.map.get_z(x,y)

				move_object.x = x
				move_object.y = y
				move_object.z = z
				location = [x,y,z]
				g_base.set(*location)
				self.send_contained(move_object)

			if not self.stoploop:
				reactor.callLater(0.1,self.tentmove)
			else:
				self.moving=0

		def on_spawn_location(self,pos):
			if self.team == self.protocol.blue_team:
				xi,yi=self.protocol.blue_team.base.x, self.protocol.blue_team.base.y
			elif self.team == self.protocol.green_team:
				xi,yi=self.protocol.green_team.base.x, self.protocol.green_team.base.y	
			
			count = 0
			while count <5:
				theta = random.uniform(0,360)						#インテル中心のスポーン角度
				r = random.uniform(60,90)							#インテル中心のスポーン距離
				x = r*math.sin(math.radians(theta)) + xi
				y = r*math.cos(math.radians(theta)) + yi
				count+=1
				if 1<x<510 and 1<y<510:
					break

			if x<1:
				x=1
			if y<1:
				y=1
			if x>510:
				x=510
			if y>510:
				y=510

			z=self.protocol.map.get_z(x,y)-2

			return (x,y,z)



		def on_reset(self):
			self.stoploop=1
			return connection.on_reset(self)

	class TentmoveProtocol(protocol,TentmoveConnection):
        
		def on_map_change(self, map):
			protocol.on_map_change(self, map)
        
		def on_map_leave(self):
			protocol.on_map_leave(self)
        
		def on_world_update(self):
			TentmoveConnection.ori+=rotatespeed
			protocol.on_world_update(self)

	return  TentmoveProtocol, TentmoveConnection

