# -*- coding: utf-8 -*-
"""
flight script by phocom modified by falcon,yuyasato
飛行スクリプト
緑チームのみ飛行可能
ジャンプで飛行開始
Wで加速、Sで減速、ctrlで爆弾投下,Vでロケット発射
一定以上速いと爆弾投下、ロケット発射不能
壁や床との激突や撃墜された場合爆発
一定以下の速度では着陸が可能
着陸すると爆弾とロケット補給
infiniclip.pyとかrapidとかも同時に鯖に入れるといいと思う
ある程度高度が上がると爆発して落ちるようになってるはずだけど、
あんまり高く上がるとclientが落ちるかもしれんので注意
"""


from twisted.internet import reactor
from pyspades.constants import *
from pyspades.common import Vertex3
from pyspades.world import Grenade
from pyspades.server import grenade_packet
import commands
from pyspades.constants import UPDATE_FREQUENCY
from easyaos import *
from math import cos,sin,atan2,degrees,radians
from pyspades.server import position_data
import random

TS=2 #bks
DROPGRE=1.0 #/s
CANNON=0.1 #/s
FLIGHT_UPDATE=0.01	#s
RUDDER=18  #deg/s
CANNON_AMMO_MAX=60 #bullets
CANNON_AMMO_RELOAD=1 #s/bullet
FLIGHT_ALTITUDE=-50 #bks

def airplane(connection):
 	if not connection.flying:
		x, y, z = connection.world_object.position.get()
		x2, y2, z2 = connection.world_object.orientation.get()
		course = degrees(atan2(y2,x2))
		connection.god=True
		connection.flying = True
		connection.flight(x, y, FLIGHT_ALTITUDE, course, 5.9)

commands.add(airplane)



def apply_script(protocol,connection,config):
	class FlightConnection(connection):
		flying = False
		cannonfire_count=0
		dropbomb_count=0
		cannon_ammo=CANNON_AMMO_MAX
		cannon_reload_count=0

		def flight(self, x, y, z, course, speed):
			if self.flying:
				if not (self.world_object.down and self.world_object.up):
					if self.world_object.down:	
						if speed <= 7:			   
						   speed += speed*FLIGHT_UPDATE
					elif self.world_object.up:	
						if speed > 3:				#speedは小さいほど機速は速い
						   speed -= speed*FLIGHT_UPDATE

				if not (self.world_object.left and self.world_object.right):
					if self.world_object.left:
						course-=FLIGHT_UPDATE*RUDDER
					elif self.world_object.right:		
						course+=FLIGHT_UPDATE*RUDDER
				course = (course+360)%360
		
				x2= cos(radians(course))
				y2= sin(radians(course))
				xs = x2 / speed
				ys = y2 / speed

				if self.world_object.crouch:
					self.dropbomb_count+=1
					if self.dropbomb_count>=DROPGRE/FLIGHT_UPDATE:
						self.dropbomb(x,y,z+3,x2*FLIGHT_UPDATE*UPDATE_FPS ,y2*FLIGHT_UPDATE*UPDATE_FPS)
						self.dropbomb_count=0
				else:
					if self.dropbomb_count<DROPGRE/FLIGHT_UPDATE:
						self.dropbomb_count+=1

				self.cannon_reload_count+=1*FLIGHT_UPDATE
				if self.cannon_reload_count>=CANNON_AMMO_RELOAD:
					if CANNON_AMMO_MAX > self.cannon_ammo:
						self.cannon_ammo+=1
					self.cannon_reload_count=0

				if self.world_object.sprint:
					self.cannonfire_count+=1
					if self.cannonfire_count>=CANNON/FLIGHT_UPDATE:
						if self.world_object.cast_ray(180) and self.cannon_ammo>0:
							xc,yc,zc = self.world_object.cast_ray(180)
							xo,yo,zo = self.world_object.orientation.get()
							xg,yg,zg = xc-xo*TS,yc-yo*TS,zc-zo*TS
							self.protocol.world.create_object(Grenade,0.0,Vertex3(xg,yg,zg),None,Vertex3(0,0,0),self.grenade_exploded)
							grenade_packet.value=0.0
							grenade_packet.player_id=self.player_id
							grenade_packet.position=(xg,yg,zg)
							grenade_packet.velocity=(0,0,0)
							self.protocol.send_contained(grenade_packet)
							self.cannonfire_count=0
							self.cannon_ammo-=1
				else:
					if self.cannonfire_count<CANNON/FLIGHT_UPDATE:
						self.cannonfire_count+=1



				x += xs
				y += ys
				z = FLIGHT_ALTITUDE
				x = (x + 511) % 511
				y = (y + 511) % 511

				position_data.x = x
				position_data.y = y
				position_data.z = z
				self.send_contained(position_data)
				reactor.callLater(FLIGHT_UPDATE, self.flight, x, y, z, course, speed)

		def dropbomb(self,x,y,z,x2,y2):
			pos = Vertex3(x, y, z)

			a = x2
			b = y2
			c = 0
			forward = Vertex3(a, b, c)


			grenade = self.protocol.world.create_object(Grenade, 0.0, pos, None, forward, None)
			collision = grenade.get_next_collision(UPDATE_FREQUENCY)

			if collision:
				t, xg, yg, zg = collision

			self.protocol.world.create_object(Grenade, t, pos, None, forward, None )
			grenade_packet.value = t
			grenade_packet.player_id = self.player_id
			grenade_packet.position = pos.get()
			grenade_packet.velocity = (a,b,c)
			self.protocol.send_contained(grenade_packet)
			reactor.callLater(t, self.high_explosive, xg, yg, zg)

		def high_explosive(self,x,y,z):
			count = 0
			self.protocol.world.create_object(Grenade,count,Vertex3(x,y,z),None,Vertex3(0,0,0.001),self.grenade_exploded)
			grenade_packet.value=count
			grenade_packet.player_id=self.player_id
			grenade_packet.position=(x,y,z)
			grenade_packet.velocity=(0,0,0.001)
			self.protocol.send_contained(grenade_packet)

			while count<15: 
				reactor.callLater(count/1000.0, self.makegre,x,y,z,count)				
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

		def on_spawn(self,pos):
			self.flying = False
		 	return connection.on_spawn(self,pos)
		
		def on_team_leave(self):
			self.flying=False
			return connection.on_team_leave(self)
		
		def on_fall(self, damage):
			if self.flying:
				return False
			return connection.on_fall(self, damage)

		def on_reset(self):
			self.flying = False
			return connection.on_reset(self)





	
	return protocol, FlightConnection