# push W in front of wall, you can climb the wall.
# if you want use specific color block as ladder, you should delete comment out # (in line 31, 67, 79, 115 )
# and color RGB write in the list LADDER_COLOR in line 13
# but color block ladder was not being tested sorry 

# 20170709 yuyasato  

from twisted.internet.reactor import callLater
from pyspades.server import position_data
from twisted.internet import reactor
from pyspades.constants import *

LADDER_COLOR = [(0,0,0),(1,1,1)]

def apply_script(protocol,connection,config):
	class LadderConnection(connection):
		laddering = 0

		def on_walk_update(self, up, down, left, right):
			if not self.laddering:
				if up:
					aimblock = self.world_object.cast_ray(2)
					if aimblock:

						xb,yb,zb = aimblock[0], aimblock[1], aimblock[2] 
						xb,yb,zb=xb+0.5,yb+0.5,zb+0.5
						xp, yp, zp = self.world_object.position.get()
						dist = ((xb-xp)**2+ (yb-yp)**2)**(1/2.0)
						if dist<1.5:
							abcolor = self.protocol.map.get_point(xb,yb,zb)[1]
							if abcolor:# in LADDER_COLOR:
								if   -0.9<xp-xb<0.9 and yp-yb >0.9:   #N
									self.laddering = 1 
									yb+=0.6
								elif xp-xb>0.9 and  -0.9 <yp-yb <0.9: #W
									self.laddering = 2
									xb+=0.6
								elif -0.9<xp-xb<0.9 and yp-yb <-0.9:  #S
									self.laddering = 3
									yb-=0.6
								elif xp-xb<-0.9 and -0.9 <yp-yb <0.9: #E
									self.laddering = 4	
									xb-=0.6
								self.ride_ladder(xb,yb,zp)
			return connection.on_walk_update(self, up, down, left, right)

		def ride_ladder(self,x,y,z):
			if self.world_object:
				if self.laddering:
					if 	self.world_object.up:
						if not self.protocol.map.get_solid(x,y,z-0.2):
							z-=0.005*(self.world_object.sprint+1)
					if self.world_object.down:
						z+=0.005*(self.world_object.sprint+1)
						if self.protocol.map.get_solid(x,y,z+2):
							self.laddering = 0
					xm,ym = x,y
					if   self.laddering == 1:
						ym-=1
					elif self.laddering == 2:
						xm-=1
					elif self.laddering == 3:
						ym+=1
					elif self.laddering == 4:
						xm+=1
					chestcolor = self.protocol.map.get_point(xm,ym,z+1.5)[1]
					if chestcolor is None:# or not chestcolor in LADDER_COLOR: #ladder isnt in front of chest
						if   self.laddering == 1:
							y+=1
						elif self.laddering == 2:
							x+=1
						elif self.laddering == 3:
							y-=1
						elif self.laddering == 4:
							x-=1	
						self.laddering = 0

						headcolor = self.protocol.map.get_point(xm,ym,z+0.5)[1]
						if headcolor is None:# or not headcolor in LADDER_COLOR: #ladder isnt in front of head	
							if not self.protocol.map.get_solid(xm,ym,z-1):
								x,y,z = xm,ym,z-1					
					self.world_object.set_position(x, y, z)						
					position_data.x = x
					position_data.y = y
					position_data.z = z
					self.send_contained(position_data)
					reactor.callLater(0.001, self.ride_ladder, x, y, z)
			else:
				self.laddering = 0

		def on_animation_update(self, jump, crouch, sneak, sprint):
			if jump:
				if self.laddering:
					x, y, z = self.world_object.position.get()
					if   self.laddering == 1:
						y+=1
					elif self.laddering == 2:
						x+=1
					elif self.laddering == 3:
						y-=1
					elif self.laddering == 4:
						x-=1
					self.world_object.set_position(x, y, z)	
					position_data.x = x
					position_data.y = y
					position_data.z = z
					self.send_contained(position_data)
					self.laddering = 0
			if crouch and not self.world_object.crouch:
				if not self.laddering:
					xp, yp, zp = self.world_object.position.get()

					z1color = self.protocol.map.get_point(xp, yp, zp+3)[1]
					z2color = self.protocol.map.get_point(xp, yp, zp+4)[1]
					if (z1color is not None and z1color) and (z2color is not None and z2color):#(z1color is not None and z1color in LADDER_COLOR) and (z2color is not None and z2color in LADDER_COLOR):
						xo, yo, zo = self.world_object.orientation.get()
						r = (xo**2+ yo**2)**(1/2.0)
						xo=xo/r
						yo=yo/r
						xp=int(xp)+0.5
						yp=int(yp)+0.5
						zp=int(zp)+0.5
						if    -0.8<xo<0.8 and yo<-0.8:  #N
							self.laddering = 1 
							yp+=0.6
						elif  xo<-0.8 and -0.8<yo<0.8: #W
							self.laddering = 2
							xp+=0.6
						elif  -0.8<xo<0.8 and 0.8<yo: #S
							self.laddering = 3
							yp-=0.6
						elif  xo>0.8 and -0.8<yo<0.8:  #E
							self.laddering = 4
							xp-=0.6
						if self.laddering:
							if not(
								self.protocol.map.get_solid(xp, yp, zp) or
								self.protocol.map.get_solid(xp, yp, zp+1) or
								self.protocol.map.get_solid(xp, yp, zp+2) or
								self.protocol.map.get_solid(xp, yp, zp+3) or
								self.protocol.map.get_solid(xp, yp, zp+4) or
								self.protocol.map.get_solid(xp, yp, zp+5) ):
									self.ride_ladder(xp, yp, zp+2)				
							else:
								self.laddering = 0
			return connection.on_animation_update(self, jump, crouch, sneak, sprint)		
	
		def on_team_leave(self):
			self.laddering = 0
			return connection.on_team_leave(self)
	
		def on_fall(self, damage):
			if self.laddering:
				return False
			else:
				return connection.on_fall(self, damage)

		def on_reset(self):
			self.laddering = 0
			return connection.on_reset(self)

		def on_disconnect(self):
			self.laddering = 0
			return connection.on_disconnect(self)
	
	return protocol, LadderConnection