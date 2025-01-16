# -*- coding: utf-8 -*-
"""
ホーミングミサイルスクリプト
右クリで狙ってVで発射
"""

from easyaos import *
import commands
from pyspades.server import set_tool, weapon_reload, create_player, set_hp
from twisted.internet.reactor import callLater
from pyspades.server import position_data
from twisted.internet import reactor
from pyspades.constants import *
from pyspades.common import Vertex3
from pyspades.world import Grenade
from pyspades.server import grenade_packet
from collections import deque
import commands
import random
from math import sqrt
from commands import add,admin,alias,name

FC_DIST=999 #照射距離
missile_acc=3		#ミサイルの加速度旋回能（小さいほど高旋回））

def apply_script(protocol,connection,config):
	class TVMissileConnection(connection):

		blk = [deque([]),deque([]),deque([]),deque([]),deque([]),deque([]),deque([]),deque([]),deque([]),deque([])]

		missile=0

		"""
		def scope(self):
			if self.world_object:
				if self.tool == WEAPON_TOOL and self.world_object.secondary_fire:
					self.freeze_animation = True
					xo,yo,zo=self.world_object.orientation.get()
					xp,yp,zp=self.world_object.position.get()
					if self.AT_bullet is None:
						magn=self.d
						if magn<=1:
							position_data.x = xp
							position_data.y = yp
							position_data.z = zp
							self.send_contained(position_data)
						else:
							xb,yb,zb = xp,yp,zp
							sol = None
							isol=magn
							for i in range(int(magn*3)):
								xb+=xo/3.0
								yb+=yo/3.0
								zb+=zo/3.0
								if self.protocol.map.get_solid(xb, yb, zb) or xb>511 or xb<0 or yb>511 or yb<0 or zb>63 or zb<-40:
									sol = (xb, yb, zb)
									isol=i
									break
							bk = self.world_object.cast_ray(magn)
							bki = self.world_object.cast_ray(i)

							if bk == None and sol==None:
								xo*=magn
								yo*=magn
								zo*=magn

								x,y,z=xp+xo,yp+yo,zp+zo	
							else:
								xo*=2
								yo*=2
								zo*=2

								if bki==None:
									x,y,z=sol[0]-xo, sol[1]-yo, sol[2]-zo
								else:
									x,y,z=bki[0]-xo, bki[1]-yo, bki[2]-zo
							position_data.x = x
							position_data.y = y
							position_data.z = z
							self.send_contained(position_data)
					else:

						xg,yg,zg = self.AT_bullet.position.get()
						xo,yo,zo = self.AT_bullet.velocity.get()
						position_data.x = xg-xo*5
						position_data.y = yg-yo*5
						position_data.z = zg+1
						self.send_contained(position_data)
					callLater(0.001, self.scope)
				else:
					xp,yp,zp=self.snipe_pos
					position_data.x = xp
					position_data.y = yp
					position_data.z = zp
					self.send_contained(position_data)	
					self.freeze_animation = False
					self.snipe_end_time=seconds()
					

		"""
		def on_secondary_fire_set(self, secondary):
			"""
			if self.tool == WEAPON_TOOL and self.weapon == 0 and secondary and self.sniper:
				self.freeze_animation = True
				self.world_object.up=self.world_object.down=self.world_object.left=self.world_object.right=False
				if self.snipe_pos == None or seconds() - self.snipe_end_time>0.5:
					self.snipe_pos=self.world_object.position.get()
				else:
					a,b,c=self.snipe_pos
					x,y,z=self.world_object.position.get()
					kyori = (a-x)**2+(b-y)**2
					kyori = kyori**0.5
					if kyori<5:
						self.snipe_pos=self.world_object.position.get()
					else:
						self.world_object.set_position(a,b,c)
				callLater(0.001, self.scope)
			"""
			return connection.on_secondary_fire_set(self, secondary)

		def high_explosive(self,x,y,z):
			count = 0
			self.protocol.world.create_object(Grenade,count,Vertex3(x,y,z),None,Vertex3(0,0,0.001),self.grenade_exploded)
			grenade_packet.value=count
			grenade_packet.player_id=self.player_id
			grenade_packet.position=(x,y,z)
			grenade_packet.velocity=(0,0,0.001)
			self.protocol.send_contained(grenade_packet)

			while count<15: 
				callLater(count/1000.0, self.makegre,x,y,z,count)				
				count+=1

		def makegre(self,x,y,z,count):
				sigma=1.5
				(xg,yg,zg)=(random.gauss(0, sigma),random.gauss(0, sigma),random.gauss(0, sigma))
				xp, yp, zp = x+xg, y+yg, z+zg
				self.protocol.world.create_object(Grenade,0,Vertex3(xp,yp,zp),None,Vertex3(0,0,0),self.grenade_exploded)
				if count<5:
					grenade_packet.value=0
					grenade_packet.player_id=self.player_id
					grenade_packet.position=(xp,yp,zp)
					grenade_packet.velocity=(0,0,0)
					self.protocol.send_contained(grenade_packet)

			

		def missileflight(self,num, x, y, z,vx,vy,vz,time):
			#起爆判定
			exp=False
			if self.protocol.map.get_solid(x, y, z) or self.protocol.map.get_solid(x+vx, y+vy, z+vz) or time > 2000:
				if self.blk[num] != deque([]):
					easyremove(self,self.blk[num].popleft())
				self.high_explosive(x,y,z)
				self.missile-=1
				exp=True	

			"""					
			if not (player.god or player.team == connection.team):	#味方とgodは除く
				xa,ya,za = player.world_object.position.get()		#プレイヤーの位置捕捉	
				xr,yr,zr=xa-x,ya-y,za-z
				radius= sqrt(xr**2 + yr**2 + zr**2)		#ミサイルとプレイヤーの距離

				if radius<=VTradius:				#近接信管が作動する距離か判定
					exp=True
			"""


			if not exp:
				#グラフィック
				if z>0 and 0<x<511 and 0<y<511:
					if time>5 and self.blk[num] != deque([]):
						easyremove(self,self.blk[num].popleft())
					self.blk[num].append((x,y,z))
					easyblock(self, (x,y,z), (250,250,251))


				if time%3<1:
					grenade_packet.value=0
					grenade_packet.player_id=self.player_id
					grenade_packet.position=(x,y,z)
					grenade_packet.velocity=(0,0,0)
					self.protocol.send_contained(grenade_packet)
				#誘導段階
				
				if self.tool == WEAPON_TOOL and self.world_object.secondary_fire:# and self.world_object.sneak:
					location = self.world_object.cast_ray(FC_DIST)
					if location:
						xtgt, ytgt, ztgt = location
						xr,yr,zr=xtgt-x,ytgt-y,ztgt-z
						radius= sqrt(xr**2 + yr**2 + zr**2)		#ミサイルとtgtの距離
						vradius= sqrt(xr**2 + yr**2)		#ミサイルとtgtの距離
						if vradius>num*10+15:
							zr=0
						if radius>FC_DIST*1.3:
							xtgt, ytgt, ztgt=self.world_object.position.get()
							xr,yr,zr=xtgt-x,ytgt-y,0
							radius= sqrt(xr**2 + yr**2)		#ミサイルと誘導手の平面距離
						vxi=xr/radius
						vyi=yr/radius
						vzi=zr/radius
					else:
						vxi, vyi, vzi = vx,vy,vz
				else:
					vxi, vyi, vzi = vx,vy,vz
				vxa=vxi/missile_acc
				vya=vyi/missile_acc					#理想進路を定数で割って疑似加速度成分を算出
				vza=vzi/missile_acc					
				vsx=vx+vxa
				vsy=vy+vya
				vsz=vz+vza
				vs= sqrt(vsx**2 + vsy**2 + vsz**2)
				vx=vsx/vs
				vy=vsy/vs						#現在進行方向と疑似加速成分度を平均化して速度を定常化
				vz=vsz/vs			
				x=x+vx*1.5
				y=y+vy*1.5
				z=z+vz*1.5
				if x>511:
					x-511
				if x<0:
					x+511
				if y>511:
					y-511
				if y<0:
					y+511
				callLater(0.03, self.missileflight,num, x, y, z,vx,vy,vz,time+1)

		def on_animation_update(self,jump,crouch,sneak,sprint):
			if sneak and self.world_object.secondary_fire and self.tool == WEAPON_TOOL:
				if self.missile == 0:
					for i in range(10):
						self.missile+=1
						x,y,z=random.randrange(1,510),random.randrange(1,510),0
						vx,vy,vz=1,0,0
						self.missileflight(i,x,y,z,vx,vy,vz,-5)
			return connection.on_animation_update(self,jump,crouch,sneak,sprint)

	return protocol, TVMissileConnection