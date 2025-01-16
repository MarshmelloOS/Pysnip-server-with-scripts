# -*- coding: utf-8 -*-
"""
print to console the position log data
鯖ログに位置のログデータをプリントするスクリプト

記録方法は2つ
１．グレネード持ってる間は1秒おきに記録する（周囲1ブロックが確保された広い空間のみ）
２．銃持ってる状態ではV押した地点を記録する（狭い空間でも可能。V押すとその点でスポーンした場合のシュミレーションがされる。良ければCtrlで決定）

/prで現在のメモリーを出力して確認（メモリーは保持）
/pr y でメモリークリアして出力

/npで現在記録した点の数を確認可能

マップアドバンスで自動的にサーバーログlog.txtに出力されてメモリーリセットされる。


マップテキストで
spawn_locations_blue = [
	(361, 201, 55),
	 (431, 325, 55)
]

def get_spawn_location(connection):
	if connection.team is connection.protocol.blue_team:
		x, y, z = random.choice(spawn_locations_blue)

みたいな風にrandom.choiceを使う場合に、これの出力ログを
spawn_locations_blue = [
	(361, 201, 55),
	 (431, 325, 55)
]
の部分に突っ込めばそのまま使えるはず


"""

from commands import admin, add, name, get_team, get_player,alias
from twisted.internet.reactor import callLater
from math import floor
from pyspades.contained import *
from pyspades.server import *
from pyspades.common import *

POSDATALIST=[]

@alias('be')
@name('bell')
def bell(connection):
	print "\a"
	return "piro-n"
add(bell)

@alias('pr')
@name('printout')
def printout(connection, reset="n"):
	if POSDATALIST !=[]:
		leng = len(POSDATALIST)
	else:
		leng=0
	if reset == "y":
		global POSDATALIST
		POSDATALIST=[]
	return "printed  %s points"%leng
add(printout)

@alias('np')
@name('nowpoint')
def nowpoint(connection, reset="n"):
	if POSDATALIST !=[]:
		leng = len(POSDATALIST)
	else:
		leng=0
	return connection.protocol.send_chat("%s points were recorded now."%leng)
add(nowpoint)

def apply_script(protocol,connection,config):
	class RecordConnection(connection):
		Vpos_temp=None
		spawntesting=False
		temp_okorng=False
		orec=9
		def on_position_update(self):
			if self.tool==GRENADE_TOOL and not self.world_object.crouch:
				if -0.001<self.world_object.velocity.z<0.001:
					x,y,z=self.world_object.position.get()
					x = int(floor(x))
					y = int(floor(y))
					z = int(floor(z))
					point_crear=0
					point_jimen=0
					for xx in [-1,0,1]:
						for yy in [-1,0,1]:
							for zz in [-1,0,1,2]:
								point_crear += self.protocol.map.get_solid(x+xx,y+yy,z+zz)
								if point_crear>0:break
					if point_crear==0:
						for xx in [-1,0,1]:
							for yy in [-1,0,1]:
								point_jimen += not(self.protocol.map.get_solid(x+xx,y+yy,z+3) or self.protocol.map.get_solid(x+xx,y+yy,z+4))
								if point_jimen>0:break
					if point_crear+point_jimen==0:
						global POSDATALIST
						POSDATALIST.append((x,y,z))
						for xx in [-1,0,1]:
							for yy in [-1,0,1]:	
								if self.protocol.map.get_solid(x+xx,y+yy,z+3):
									self.put_jimen(x+xx,y+yy,z+3,(255,0,0))
								elif self.protocol.map.get_solid(x+xx,y+yy,z+4):
									self.put_jimen(x+xx,y+yy,z+4,(255,0,0))
						self.put_sora(x,y,0,(255,0,0))						

						self.orec+=1
						if self.orec>10:
							self.orec=0
							self.send_chat("position recording")
			return connection.on_position_update(self)


		def put_sora(self,x,y,z,color):
			for xx in [-1,0,1]:
				for yy in [-1,0,1]:			
					if self.protocol.map.get_solid(x+xx,y+yy,z):
						block_action = BlockAction()
						block_action.player_id = self.player_id
						block_action.value = DESTROY_BLOCK
						block_action.x = x+xx
						block_action.y = y+yy
						block_action.z = z
						self.protocol.send_contained(block_action)
						self.protocol.map.remove_point(x+xx,y+yy,z)
			for xx in [-1,0,1]:
				for yy in [-1,0,1]:	
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

		def put_jimen(self,x,y,z,color):
			if self.protocol.map.get_solid(x,y,z):
				block_action = BlockAction()
				block_action.player_id = self.player_id
				block_action.value = DESTROY_BLOCK
				block_action.x = x
				block_action.y = y
				block_action.z = z
				self.protocol.send_contained(block_action)
				self.protocol.map.remove_point(x, y, z)
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

		def spawntest(self):
			if self.spawntesting and self.tool!=WEAPON_TOOL:
				self.spawn()
				callLater(2,self.spawntest)
			else:
				self.spawntesting=False

		def on_animation_update(self, jump, crouch, sneak, sprint):
			if self.tool==BLOCK_TOOL:
				 if sneak:
					self.spawntesting=True
					self.spawn()
					callLater(3,self.spawntest)
			if self.tool==GRENADE_TOOL:
				if sneak and not self.world_object.sneak:
					x,y,z=self.world_object.position.get()
					x = int(floor(x))
					y = int(floor(y))
					z = int(floor(z))
					point_crear=0
					point_jimen=0
					for xx in [-1,0,1]:
						for yy in [-1,0,1]:
							for zz in [-1,0,1,2]:
								point_crear += self.protocol.map.get_solid(x+xx,y+yy,z+zz)
								if point_crear>0:break
					if point_crear==0:
						for xx in [-1,0,1]:
							for yy in [-1,0,1]:
								point_jimen += not(self.protocol.map.get_solid(x+xx,y+yy,z+3) or self.protocol.map.get_solid(x+xx,y+yy,z+4))
								if point_jimen>0:break
					if point_crear+point_jimen==0:
						global POSDATALIST
						POSDATALIST.append((x,y,z))
						for xx in [-1,0,1]:
							for yy in [-1,0,1]:	
								if self.protocol.map.get_solid(x+xx,y+yy,z+3):
									self.put_jimen(x+xx,y+yy,z+3,(255,0,0))
								elif self.protocol.map.get_solid(x+xx,y+yy,z+4):
									self.put_jimen(x+xx,y+yy,z+4,(255,0,0))
						self.put_sora(x,y,0,(255,0,0))						

						self.orec+=1
						if self.orec>10:
							self.orec=0
							self.send_chat("position recording")
			if self.tool==WEAPON_TOOL:
				if sneak and not self.world_object.sneak:
					x,y,z=self.world_object.position.get()
					x = int(floor(x))
					y = int(floor(y))
					z = int(floor(z))
					point_crear=0
					for zz in [0,1,2]:
						point_crear += self.protocol.map.get_solid(x,y,z+zz)
						if point_crear>0:break
					if point_crear==0:
						self.Vpos_temp=x,y,z
						self.temp_okorng=True
						x += 0.5
						y += 0.5
						z += 0.4
						pos=x,y,z
						self.spawn(pos)	
						self.send_chat("OK? if OK,  Ctrl with migikuri")
				if crouch and self.temp_okorng:
					print 321
					global POSDATALIST
					x,y,z=self.Vpos_temp
					POSDATALIST.append((x,y,z))
					if self.protocol.map.get_solid(x,y,z+3):
						self.put_jimen(x,y,z+3,(0,0,255))
					elif self.protocol.map.get_solid(x,y,z+4):
						self.put_jimen(x,y,z+4,(0,0,255))
					self.put_sora(x,y,0,(0,0,255))	
					self.Vpos_temp=None
					self.temp_okorng = False
					self.send_chat("position recorded")					

			return connection.on_animation_update(self, jump, crouch, sneak, sprint)

	class RecordProtocol(protocol):
		premapname=None
		def on_map_change(self, map):
			global POSDATALIST
			print self.premapname
			print POSDATALIST

			POSDATALIST=[]	
			self.premapname=self.map_info.name
			return protocol.on_map_change(self, map)
	
	return RecordProtocol, RecordConnection