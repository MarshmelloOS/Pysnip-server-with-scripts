from pyspades.constants import *
from pyspades.world import Grenade
from pyspades.server import grenade_packet
from pyspades.common import Vertex3
from pyspades.constants import UPDATE_FREQUENCY
import random
import commands
from commands import alias,admin, add, name, get_team, get_player,where_from
from twisted.internet import reactor
from twisted.internet.reactor import callLater
from math import sqrt,sin,asin, cos, acos, pi, tan,atan,degrees,radians,hypot,atan2,floor

SPEED = 4.7
RELOAD_TIME = 3

@admin
@name('s')
def s(connection, points):
	global SPEED
	SPEED = float(points)
	return "SPEED %s " % SPEED
add(s)

@admin
@name('r')
def r(connection, points):
	global RELOAD_TIME
	RELOAD_TIME = float(points)
	return "RELOAD_TIME %s " % RELOAD_TIME
add(r)


@commands.alias('ar')
def be_artillery(connection):
	flag = True
	if connection.team == -1:
		return False
	x, y, z = connection.world_object.position.get()
#	if connection.team == connection.protocol.blue_team and x<192:
#		flag=True
#	if connection.team == connection.protocol.green_team and x>320:	
#		flag=True

	if flag:
		connection.artillery = not connection.artillery
		connection.fix_pos(x,y,z+1.5)
		if connection.artillery:
			return 'you are now artillery'
		else:
			return 'you are no longer artillery'
	else:
		return "you can't be artillery here"	
commands.add(be_artillery)

@commands.alias('fix')
def fix_ori(connection):
	if connection.artillery:
		connection.fix_ori = not connection.fix_ori
		connection.angle_gun = connection.world_object.orientation.get()
		connection.ev, connection.az = 0, 0
		if connection.fix_ori:
			return 'gun orientation fixed this angle'
		else:
			return 'now orientation depends on your aim'
	return "only artillery can use this command. press /ar"
commands.add(fix_ori)


def apply_script(protocol,connection,config):
	class ArtilleryConnection(connection):
		artillery = False
		angle_gun = 1, 1, 1
		fix_ori = False
		fw,bw,le,ri=False,False,False,False
		shift=False
		reloading=False
		shell = 0

		def add_score(self, score):
			self.shell +=score*3
			return connection.add_score(self, score)

		def on_hit(self, hit_amount, hit_player, type, grenade):
			if self.artillery and self==hit_player:
				return False						
			return connection.on_hit(self, hit_amount, hit_player, type, grenade)

		def fix_pos(self, x, y, z):
			if self.artillery:
				self.set_location((x, y, z))
				reactor.callLater(0.01, self.fix_pos, x, y, z)

		def on_kill(self,killer,type,grenade):
			self.artillery = False
			return connection.on_kill(self,killer,type,grenade)

		def on_team_leave(self):
			self.artillery = False
			return connection.on_team_leave(self)

		def on_spawn(self,pos):
			self.artillery = False
			return connection.on_spawn(self,pos)
		
		def on_reset(self):
			self.artillery = False
			connection.on_reset(self)


		def on_walk_update(self, fw, bw, le, ri):
			if self.fix_ori and self.artillery:
				if not fw:
					self.fw = False
				else:
					if not self.fw:
						x, y, z = self.angle_gun
						theta=degrees(atan2(y,x))
						phi=degrees(asin(z))
						r=hypot(x, y)
						if phi>-88.9:
							if self.shift:
								new_phi=phi-1.0
							else:
								new_phi=phi-0.1
						else:
							new_phi=phi
						z=sin(radians(new_phi))
						x*=cos(radians(new_phi))/r
						y*=cos(radians(new_phi))/r
						self.angle_gun = x, y, z 
						if self.shift:
							self.send_chat("elevation +1.0 deg. now azimuth%1f, elevation%+1f "% ((theta+450)%360, -1.0*new_phi))
						else:
							self.send_chat("elevation +0.1 deg. now azimuth%1f, elevation%+1f "% ((theta+450)%360, -1.0*new_phi))
					self.fw = True

				if not bw:
					self.bw = False
				else:
					if not self.bw:
						x, y, z = self.angle_gun
						theta=degrees(atan2(y,x))
						phi=degrees(asin(z))
						r=hypot(x, y)
						if phi<88.9:
							if self.shift:
								new_phi=phi+1.0
							else:
								new_phi=phi+0.1
						else:
							new_phi=phi
						z=sin(radians(new_phi))
						x*=cos(radians(new_phi))/r
						y*=cos(radians(new_phi))/r
						self.angle_gun = x, y, z 
						if self.shift:
							self.send_chat("elevation -1.0 deg. now azimuth%1f, elevation%+1f "% ((theta+450)%360, -1.0*new_phi))
						else:
							self.send_chat("elevation -0.1 deg. now azimuth%1f, elevation%+1f "% ((theta+450)%360, -1.0*new_phi))
					self.bw = True

				if not le:
					self.le = False
				else:
					if not self.le:
						x, y, z = self.angle_gun
						theta=degrees(atan2(y,x))
						phi=degrees(asin(z))
						r=hypot(x, y)
						if self.shift:
							new_theta=theta-1.0
						else:
							new_theta=theta-0.1
						x = cos(radians(new_theta))*r
						y = sin(radians(new_theta))*r
						self.angle_gun = x, y, z 
						if self.shift:
							self.send_chat("azimuth -1.0 deg. now azimuth%1f, elevation%+1f "% ((new_theta+450)%360, -1.0*phi))
						else:
							self.send_chat("azimuth -0.1 deg. now azimuth%1f, elevation%+1f "% ((new_theta+450)%360, -1.0*phi))
					self.le = True

				if not ri:
					self.ri = False
				else:
					if not self.ri:
						x, y, z = self.angle_gun
						theta=degrees(atan2(y,x))
						phi=degrees(asin(z))
						r=hypot(x, y)
						if self.shift:
							new_theta=theta+1.0
						else:
							new_theta=theta+0.1
						x = cos(radians(new_theta))*r
						y = sin(radians(new_theta))*r
						self.angle_gun = x, y, z 
						if self.shift:
							self.send_chat("azimuth +1.0 deg. now azimuth%1f, elevation%+1f "% ((new_theta+450)%360, -1.0*phi))
						else:
							self.send_chat("azimuth +0.1 deg. now azimuth%1f, elevation%+1f "% ((new_theta+450)%360, -1.0*phi))
					self.ri = True

			return connection.on_walk_update(self, fw, bw, le, ri)

		def heavy_gun_reload(self):
			self.reloading=False
			if self.shell>0:
				self.send_chat("reloading completion")

		def on_animation_update(self,jump,crouch,sneak,sprint):
			if sneak and self.world_object.secondary_fire and self.artillery:
				if self.shell>0:
					if not self.reloading:
						self.shell-=1
						self.send_chat("There is %s shells rest."% self.shell)
						self.heavy_gun_fire()
						self.reloading=True
						reactor.callLater(RELOAD_TIME, self.heavy_gun_reload)	
					else:
						self.send_chat("reloading now!!")
				else:
					self.send_chat("There is no shells anymore!")	
							
			if sprint:
				self.shift=True
			else:
				self.shift=False
			return connection.on_animation_update(self,jump,crouch,sneak,sprint)

		def heavy_gun_fire(self):
			x, y, z = self.world_object.position.get()
			pos = Vertex3(x, y, z)
			if self.fix_ori:
				a,b,c=self.angle_gun
			else:
				a,b,c = self.world_object.orientation.get()

			"""
			sigma=3
			phi=degrees(asin(c))
			r=hypot(a, b)
			new_phi=phi+random.gauss(0, sigma)
			c=sin(radians(new_phi))
			a*=cos(radians(new_phi))/r
			b*=cos(radians(new_phi))/r

			theta=degrees(atan2(b,a))
			r=hypot(a, b)
			new_theta=theta+random.gauss(0, sigma)
			a = cos(radians(new_theta))*r
			b = sin(radians(new_theta))*r
			"""


			exp_pos = Vertex3(x-a, y-b, z-c)
			a = a * SPEED
			b = b * SPEED
			c = c * SPEED
			forward = Vertex3(a, b, c)

	  	 	grenade_packet.value=0.0
	  		grenade_packet.player_id=self.player_id
	  		grenade_packet.position=exp_pos.get()
	  		grenade_packet.velocity=(0,0,0)
 			self.protocol.send_contained(grenade_packet)

		#	grenade = self.protocol.world.create_object(Grenade, 0.0, pos, None, forward, None)

			t=0
			while t<1000:
				xg=x+a*t
				yg=y+b*t
				zg=0.0315*(t**2)/2.0 + c*t + z
				t+=0.001
				if self.protocol.map.get_solid(xg,yg,zg) or (not 0<xg<511) or (not 0<yg<511) or (zg>63) :
					t=t/32.1
					break

			"""
			collision = grenade.get_next_collision(UPDATE_FREQUENCY)
			if collision:
				impact, x, y, z = collision
				print "ans", t-impact, xg-x,yg-y,zg-z
			"""

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
			self.explode=True

			while count<15: 
				reactor.callLater(count/100.0, self.makegre,x,y,z)				
				count+=1

			while count<0.15:						
				(xg,yg,zg)=(random.uniform(-0.5,0.5),random.uniform(-0.5,0.5),random.uniform(-0.5,0.5))
				dt=random.uniform(0,0.25)
				self.protocol.world.create_object(Grenade,count+dt,Vertex3(x,y,z),None,Vertex3(xg,yg,zg),self.grenade_exploded)
				grenade_packet.value=count+dt
				grenade_packet.player_id=self.player_id
				grenade_packet.position=(x,y,z)
				grenade_packet.velocity=(xg,yg,zg)
				self.protocol.send_contained(grenade_packet)
				count+=0.01

		def makegre(self,x,y,z):
				sigma=1.5
				(xg,yg,zg)=(random.gauss(0, sigma),random.gauss(0, sigma),random.gauss(0, sigma))
				xp, yp, zp = x+xg, y+yg, z+zg
				self.protocol.world.create_object(Grenade,0,Vertex3(xp,yp,zp),None,Vertex3(0,0,0),self.grenade_exploded)
				if random.uniform(-0.2,1.2)<0:
					grenade_packet.value=0
					grenade_packet.player_id=self.player_id
					grenade_packet.position=(xp,yp,zp)
					grenade_packet.velocity=(0,0,0)
					self.protocol.send_contained(grenade_packet)

		def on_fall(self, damage):
			if self.artillery:
				return False
			else:
				return connection.on_fall(self, damage)


	return protocol,ArtilleryConnection