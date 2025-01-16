# -*- coding: utf-8 -*-
"""
ランダム区画マップスクリプト
区画ごとにマップデータを保存して、マップ変更時にデータを呼び出しして区画をランダムに並び替える

使い方
dist/automati/64というフォルダを作ってください
AREASIZEを変える場合は64の部分のフォルダを別の数値（AREASIZEの数値）にしてください

・マップデータ保存方法
BATTLE_USEをFalseにすると建築モードで起動します。
/svで保存モードになります。
保存したい区画の左上（x,yが最小）のブロックをMMTの要領でたたくなどして選択してください。（Z座標は問わず）
AREASIZE*AREASIZE*64の区画がdist/automati/64/N.txt (N:整数)に保存されます。

・戦闘（通常モード）での使用方法
BATTLE_USEをTrueにすると通常モードで起動します。
60行目付近　choice([0,1,2,3]) が使用されるデータになります。使いたいデータを全部コンマ区切りで書いてください
マップローテでは元のマップデータに上書き（上書き保存という意味ではない）する形になるので、海を除く全マップ空間が何もないマップを使った方がいいです。
nullpo.vxlは何もないマップです。
あとは普通に起動するだけで平気なはずです。

※マップロードに時間がかかりすぎてプレイヤーが落ちますが仕様です。


added by yuyasato


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


BATTLE_USE = True   ########### Falseにすると建築・設定モードになる

AREASIZE=64     ######１区画の正方形の辺長：デフォルトで64


 
@alias('sv')
@name('savemode')
def savemode(connection,type):
	connection.savemode=True
	connection.savetype=type
	connection.send_chat("savemode on. type:%s"%connection.savetype)
	print "savemode on"

add(savemode)

def c01():
	return choice([0,1])

def apply_script(protocol, connection, config):

	class AutomatiProtocol(protocol):
		next_mapdata_mem=[]
		next_areatype=[]
		area_data=[[],[],[],[],[],[]]
		first_memory=True

		def area_data_memory(self):
			self.area_data=[[],[],[],[],[],[]]
			for type in [0,1,2,3,4,5]:  ######　読み込みに使うマップ名指定
				for name in [0]:  ######　読み込みに使うマップ名指定
					with open('./automati/%s/%s/%s.txt'%(AREASIZE,type,name), 'rb') as file:
						data = json.load(file)
					self.area_data[type].append(data)	
			self.first_memory=False	

		def c01():
			return choice([0,1])

		def set_areatype(self):
			self.next_areatype=[]

			for column in range(8):#(12345678)
				self.next_areatype.append([])

				for row in range(8):#(ABCDEFGH)
					if column==0:
						if row==0:
							temp=(c01(),c01(),c01(),c01())
							self.next_areatype[column].append(temp)
						else:
							left = self.next_areatype[column][-1]
							if left[1]!=1:
								temp = ( left[0],c01(),left[2],left[1] )
							else:
								temp = ( c01(),c01(),c01(),left[1] )
							self.next_areatype[column].append(temp)
					else:
						if row==0:
							up = self.next_areatype[column-1][row]
							rightup=self.next_areatype[column-1][row+1]
							if up[2]!=1:
								temp = ( up[2],up[1],c01(),up[3] )
							else:
								if rightup[2]==0 and rightup[3]==1:
									temp = ( up[2],1,c01(),c01() )
								else:
									temp = ( up[2],c01(),c01(),c01() )

							self.next_areatype[column].append(temp)
						else:
							up = self.next_areatype[column-1][row]
							left = self.next_areatype[column][-1]
							if row<7:
								rightup=self.next_areatype[column-1][row+1]

							if up[2]!=1:
								if left[1]!=1:
									temp = ( up[2],up[1],left[2],left[1]  )
								else:
									temp = ( up[2],up[1],c01(),left[1]  )
							else:
								if row<7:
									if rightup[2]==0 and rightup[3]==1:
										if left[1]!=1:
											temp = ( up[2],1,left[2],left[1]  )
										else:
											temp = ( up[2],1,c01(),left[1]  )
									else:
										if left[1]!=1:
											temp = ( up[2],c01(),left[2],left[1]  )
										else:
											temp = ( up[2],c01(),c01(),left[1]  )
								else:
									if left[1]!=1:
										temp = ( up[2],c01(),left[2],left[1]  )
									else:
										temp = ( up[2],c01(),c01(),left[1]  )
									
							self.next_areatype[column].append(temp)


		def decord_type(self):		#type = (012345, rotate 0123)
			self.decorded__next_type=[]
			num=0
			for clm in self.next_areatype:
				self.decorded__next_type.append([])
				for area in clm:
					if sum(area)==0:	#type 0
						type=(0,choice([0,1,2,3]))
					elif sum(area)==1:	#type 1
						if area[0]==1:
							type=(1,0)
						elif area[1]==1:
							type=(1,1)
						elif area[2]==1:
							type=(1,2)
						elif area[3]==1:
							type=(1,3)
					elif sum(area)==2:	#type 2 or 5
						if area[0]!=area[2]:	#type 2 
							if area[0]==1 and area[1]==1:
								type=(2,0)
							elif area[1]==1 and area[2]==1:
								type=(2,1)				
							elif area[2]==1 and area[3]==1:
								type=(2,2)
							elif area[3]==1 and area[0]==1:
								type=(2,3)	
						else:					#type 5 
							if area[0]==1:
								type=(5,choice([0,2]))
							elif area[1]==1:
								type=(5,choice([1,3]))	
					elif sum(area)==3:	#type 3
						if area[3]==0:
							type=(3,0)
						elif area[0]==0:
							type=(3,1)
						elif area[1]==0:
							type=(3,2)
						elif area[2]==0:
							type=(3,3)
					elif sum(area)==4:	#type 4
						type=(4,choice([0,1,2,3]))
					self.decorded__next_type[num].append(type)
				num+=1

		def set_map(self, map):	
			if BATTLE_USE:

				if self.first_memory:
					self.area_data_memory()			
				print "start", seconds()
				self.next_mapdata_mem=[]
				self.set_areatype()
				print self.next_areatype
				self.decord_type()
				print self.decorded__next_type

				for column in range(8):
					self.next_mapdata_mem.append([])

					for row in range(8):
						type=self.decorded__next_type[column][row][0]
						data=choice(self.area_data[type])
						self.next_mapdata_mem[column].append(data)


				print "setfinish", seconds()
			protocol.set_map(self, map)


		def on_map_change(self, map):
			if BATTLE_USE:
				print "start", seconds()
				for column in range(8):
					for row in range(8):
						x0,y0,z0 = row*AREASIZE, column*AREASIZE,0
						data=self.next_mapdata_mem[column][row]
						rot=self.decorded__next_type[column][row][1]

						if rot==0:
							counter_x=0
							counter_y=0
							counter_z=0
							
							for xx in data:
								counter_y=0
								for yy in xx:
									counter_z=0
									for zz in yy:
										if zz is not None:
											xxx=counter_x
											yyy=counter_y
											if xxx<AREASIZE and yyy<AREASIZE:
												color= (zz[0],zz[1],zz[2])
												self.map.set_point(xxx+x0,yyy+y0,counter_z+z0,color)
										counter_z+=1
									counter_y+=1
								counter_x+=1
						elif rot==1:
							counter_x=0
							counter_y=0
							counter_z=0
							
							for xx in data:
								counter_y=0
								for yy in xx:
									counter_z=0
									for zz in yy:
										if zz is not None:
											xxx=AREASIZE+1-1-counter_y
											yyy=counter_x
											if xxx<AREASIZE and yyy<AREASIZE:
												color= (zz[0],zz[1],zz[2])
												self.map.set_point(xxx+x0,yyy+y0,counter_z+z0,color)
										counter_z+=1
									counter_y+=1
								counter_x+=1
						elif rot==2:
							counter_x=0
							counter_y=0
							counter_z=0
							
							for xx in data:
								counter_y=0
								for yy in xx:
									counter_z=0
									for zz in yy:
										if zz is not None:
											xxx=AREASIZE+1-1-counter_x
											yyy=AREASIZE+1-1-counter_y
											if xxx<AREASIZE and yyy<AREASIZE:
												color= (zz[0],zz[1],zz[2])
												self.map.set_point(xxx+x0,yyy+y0,counter_z+z0,color)
										counter_z+=1
									counter_y+=1
								counter_x+=1
						elif rot==3:
							counter_x=0
							counter_y=0
							counter_z=0
							
							for xx in data:
								counter_y=0
								for yy in xx:
									counter_z=0
									for zz in yy:
										if zz is not None:
											xxx=counter_y
											yyy=AREASIZE+1-1-counter_x
											if xxx<AREASIZE and yyy<AREASIZE:
												color= (zz[0],zz[1],zz[2])
												self.map.set_point(xxx+x0,yyy+y0,counter_z+z0,color)
										counter_z+=1
									counter_y+=1
								counter_x+=1
				print "finish", seconds()
			protocol.on_map_change(self, map)

	class AutomatiConnection(connection):
		savemode=False
		savetype=None
		def on_block_destroy(self, x, y, z, value):
			if not BATTLE_USE:
				if self.savemode:
					self.savemode=False

					self.savememori=[]
					for xx in range(AREASIZE+1):
						self.savememori.append([])
						for yy in range(AREASIZE+1):
							self.savememori[xx].append([])
							for zz in range(64):
								color= self.protocol.map.get_color(x+xx, y+yy, zz)
								self.savememori[xx][yy].append(color)
			#		print self.savememori
					for numid in range(60000):
						name=str(numid)
						if not os.path.exists('./automati/%s/%s/%s.txt'%(AREASIZE,self.savetype,name)):
							with open('./automati/%s/%s/%s.txt'%(AREASIZE,self.savetype,name), 'w') as file:
								json.dump(self.savememori, file, indent = 4)
							break
					self.protocol.send_chat("area saved. name:%s.txt"%name)
			connection.on_block_destroy(self, x, y, z, value)


	return AutomatiProtocol, AutomatiConnection