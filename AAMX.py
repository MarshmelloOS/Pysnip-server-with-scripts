from easyaos import *
from math import sqrt, acos, degrees

COOLDOWN=0.5
VTradius=3
sensor_radius= 130
sensor_ang=10
boost_time=15
missile_acc=2

def missile(connection,(x,y,z),(vx,vy,vz),time,team_num):
 easyremove(connection,(x,y,z))
 radiusmin,xrmin,yrmin,zrmin, = 255,255,255,255
 VTfuse = 0
 for player in connection.protocol.players.values():
	if team_num == 0:	
		if not (player.god or player.team == connection.protocol.blue_team):
			 xa,ya,za = player.get_location()
			 xr,yr,zr=xa-x,ya-y,za-z
			 radius= sqrt(xr**2 + yr**2 + zr**2)

			 vxi=xr/radius
			 vyi=yr/radius
			 vzi=zr/radius

			 cos = (vx*vxi + vy*vyi + vz*vzi)/( sqrt( vx**2 + vy**2 + vz**2 )*sqrt( vxi**2+vyi**2+vzi**2 ) )
			 if cos > 1:
				cos = 1
			 if cos<-1 :
				cos = -1
			 ang = degrees(acos(cos))

		         if radius<=VTradius:
		            VTfuse=1
			 if radius<=radiusmin and ang<sensor_ang :
				radiusmin = radius
				xrmin=xr
				yrmin=yr
				zrmin=zr
	if team_num == 1:	
		if not (player.god or player.team == connection.protocol.green_team):
			 xa,ya,za = player.get_location()
			 xr,yr,zr=xa-x,ya-y,za-z
			 radius= sqrt(xr**2 + yr**2 + zr**2)

			 vxi=xr/radius
			 vyi=yr/radius
			 vzi=zr/radius

			 cos = (vx*vxi + vy*vyi + vz*vzi)/( sqrt( vx**2 + vy**2 + vz**2 )*sqrt( vxi**2+vyi**2+vzi**2 ) )
			 if cos > 1:
				cos = 1
			 if cos<-1 :
				cos = -1
			 ang = degrees(acos(cos))

		         if radius<=VTradius:
		            VTfuse=1
			 if radius<=radiusmin and ang<sensor_ang :
				radiusmin = radius
				xrmin=xr
				yrmin=yr
				zrmin=zr
 vxi=xrmin/radiusmin
 vyi=yrmin/radiusmin
 vzi=zrmin/radiusmin

 if radiusmin<sensor_radius and time>boost_time:
	 vxa=vxi/missile_acc
	 vya=vyi/missile_acc
	 vza=vzi/missile_acc
	 vsx=vx+vxa
	 vsy=vy+vya
	 vsz=vz+vza
 	 vs= sqrt(vsx**2 + vsy**2 + vsz**2)
	 vx=vsx/vs
	 vy=vsy/vs
	 vz=vsz/vs
 
 x+=vx*1.8
 y+=vy*1.8
 z+=vz*1.8
 time+=1

 if connection.protocol.map.get_solid(x,y,z) or x<2 or x>509 or y<2 or y>509 or z<2 or z>63 or VTfuse==1 or time>300:
  easygre(connection,(x,y,z),(0,0,0),0)
  easygre(connection,(x+2,y,z),(0,0,0),0)
  easygre(connection,(x-2,y,z),(0,0,0),0)
  easygre(connection,(x,y+2,z),(0,0,0),0)
  easygre(connection,(x,y-2,z),(0,0,0),0)
  easygre(connection,(x,y,z+2),(0,0,0),0)
  easygre(connection,(x,y,z-2),(0,0,0),0)
 else:
  reactor.callLater(0.03,missile,connection,(x,y,z),(vx,vy,vz),time,team_num)
  easyblock(connection,(x,y,z),connection.color)

def apply_script(protocol,connection,config):
 class MissileConnection(connection):
  missile=False
  def missile_charge(self):
   self.missile=True
   self.send_chat("You are able to shoot Missile now!!")
  def on_spawn(self,pos):
   self.missile=True
   return connection.on_spawn(self,pos)
  def on_animation_update(self,jump,crouch,sneak,sprint):
   if crouch and self.world_object.secondary_fire and self.tool == WEAPON_TOOL:
     x,y,z=self.world_object.position.get()
     vx,vy,vz=self.world_object.orientation.get()
     missile(self,(x+3*vx,y+3*vy,z+3*vz),(vx*0.8,vy*0.8,vz*0.8),0,0)
   return connection.on_animation_update(self,jump,crouch,sneak,sprint)
 return protocol,MissileConnection