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
import math


COOLDOWN=0.5


def apply_script(protocol,connection,config):
    class FlightConnection(connection):
        flying = False
        fw = False
        bw = False
        le = False
        ri = False
	rocket=False
	aircraft = False 

        Shift = False
        V = False
        Ctrl = False
        
        def flight_reset(self):
            self.flying = False
            self.fw = False
            self.bw= False
	    self.le = False	   
            self.Shift = False
            self.V= False
            self.Ctrl = False

        def flight(self, x, y, z, x2, y2, z2, speed, rest_bomb, gre_fired, rest_rocket, roc_fired,lookaway,left,llll,right,rrrr):
            if self.flying:

                    if self.bw:	
                        if speed <= 15:			   
			   speed += speed*0.01
			   pspeed=1300//speed
			   if speed >5.9:
			 	  self.send_chat("speed %s   You can landing now. "% pspeed )
			   elif speed >=5:
				   if rest_bomb>0 or rest_rocket>0:
					  self.send_chat("speed %s   You can use anti ground weapon.  "% pspeed )
				   else:
			 		  self.send_chat("speed %s "% pspeed )
			   else:
		 		  self.send_chat("speed %s "% pspeed )
                    elif self.fw:	
                        if speed > 2:				#speedは小さいほど機速は速い
			   speed -= speed*0.01
			   pspeed=1300//speed
			   if speed >5.9:
			 	  self.send_chat("speed %s   You can landing now. "% pspeed )
			   elif speed >= 5:
				   if rest_bomb>0 or rest_rocket>0:
					  self.send_chat("speed %s   You can use anti ground weapon.  "% pspeed )
				   else:
				 	  self.send_chat("speed %s "% pspeed )
			   else:
		 		  self.send_chat("speed %s "% pspeed )
		    if self.Shift:
			  self.send_chat("Altitude %s "% z )			

                    xo, yo, zo = self.world_object.orientation.get()
		    if self.V:
			if self.tool == GRENADE_TOOL:
				if roc_fired==0:
					  if speed >= 5:
						    if rest_rocket>0:
							if z>2:
							    if not self.rocket:
							     self.send_chat("WAIT cooling down now")		
							    else:
							     self.rocket=False
							     vx,vy,vz=xo,yo,zo
							     self.rockelan(self,(x+vx*3,y+vy*3,z+vz*3),(vx*0.8,vy*0.8,vz*0.8))
							     rest_rocket-=1
						  	     self.send_chat("The rest Rocket is  %s "% rest_rocket  )
							     reactor.callLater(COOLDOWN,self.rocket_charge)
							else:
							     self.send_chat("The Altitude is too high to shoot Rocket.")							
						    else:
							     self.send_chat("You have used all Rocket. You can supply Rocket by landing.")
					  else:
						    self.send_chat("The speed is too fast to shoot rocket." )
					  roc_fired=1
		    elif not self.V:	
			roc_fired=0	
		
		    if self.Ctrl:
			if self.tool == GRENADE_TOOL:
				if gre_fired==0:
					  if speed >= 5:
						if rest_bomb>0:
				                    player_pos=self.world_object.position
						    x3=x2/speed*4
						    y3=y2/speed*4
						    z3=z2/speed*4
				  		    grenade = self.protocol.world.create_object(Grenade,0.0,player_pos,None,Vertex3(x3,y3,z3),None)
				             	    collision = grenade.get_next_collision(UPDATE_FREQUENCY)
				                    if collision:
				                   	impact, x4, y4, z4 = collision
				            	    self.protocol.world.create_object(Grenade, impact,player_pos,None,Vertex3(x3,y3,z3), self.grenade_exploded)
				  		    grenade_packet.value = impact
				  	  	    grenade_packet.player_id=self.player_id
				  		    grenade_packet.position=player_pos.get()
				  		    grenade_packet.velocity=(x3,y3,z3)
				 		    self.protocol.send_contained(grenade_packet)

						    rest_bomb-=1
						    self.send_chat("The rest Bomb is  %s "% rest_bomb  )
						else:
						    self.send_chat("You have used all Bomb. You can supply bomb by landing." )	
					  else:
						    self.send_chat("The speed is too fast to drop bomb." )
					  gre_fired=1
		    elif not self.Ctrl:
			gre_fired=0


		    cos = (x2*xo + y2*yo + z2*zo)/( math.sqrt( x2**2 + y2**2 + z2**2 )*math.sqrt( xo**2+yo**2+zo**2 ) )
		    if cos > 1:
				cos = 1
		    if cos<-1 :
				cos = -1
	   	    ang = math.degrees(math.acos(cos))

		    if self.ri:
			if rrrr!=1 and ang < 40:
				if left:
					left=0
					self.send_chat("normal flight mode")
				else:
					right = 1
					self.send_chat("right turning mode")	
				rrrr=1
		    if not self.ri:
			rrrr=0	
	
		    if self.le:
			if llll!=1 and ang<40:
				if right:
					right=0
					self.send_chat("normal flight mode")
				else:
					left = 1
					self.send_chat("left turning mode")
				llll=1
		    if not self.le:
			llll=0	


		    if left:
			Eang = math.degrees(math.atan(y2/x2))
			oang = Eang - 0.1
			if x2<0:
				oang = oang + 180
			x2 = math.cos(math.radians(oang))
			y2 = math.sin(math.radians(oang))
			z2 = 0

		    if right:
			Eang = math.degrees(math.atan(y2/x2))
			oang = Eang + 0.1
			if x2<0:
				oang = oang + 180
			x2 = math.cos(math.radians(oang))
			y2 = math.sin(math.radians(oang))
			z2 = 0
		    if self.Shift:
			lookaway=1
			self.send_chat("auto pirot mode")
		    elif ang < 30:
		        if lookaway==1:
				self.send_chat("normal flight mode")
			lookaway=0


		    if not right and not left and lookaway==0:
              	      x2, y2, z2 =  xo, yo, zo




                    x += x2 /  speed
                    y += y2 /  speed
                    z += z2 /  speed
                    x = (x + 511) % 511
                    y = (y + 511) % 511

                    if self.protocol.map.get_solid(x, y, z+2) or self.protocol.map.get_solid(x, y, z+1):
		     if speed >= 5.9 and not self.protocol.map.get_solid(x, y, z):
                        self.flight_reset()
		     else:
			player_pos=self.world_object.position
  		        self.protocol.world.create_object(Grenade,0.0,player_pos,None,Vertex3(0,0,0),self.grenade_exploded)
  		        grenade_packet.value=0.0
  	  		grenade_packet.player_id=self.player_id
  			grenade_packet.position=player_pos.get()
  			grenade_packet.velocity=(0,0,0)
 		        self.protocol.send_contained(grenade_packet)

                    if self.protocol.map.get_solid(x, y, z):
		     if speed >= 5.9 and self.protocol.map.get_solid(x, y, z+2) or self.protocol.map.get_solid(x, y, z+1):
                        self.flight_reset()
		     else:
			player_pos=self.world_object.position
  		        self.protocol.world.create_object(Grenade,0.0,player_pos,None,Vertex3(0,0,0),self.grenade_exploded)
  		        grenade_packet.value=0.0
  	  		grenade_packet.player_id=self.player_id
  			grenade_packet.position=player_pos.get()
  			grenade_packet.velocity=(0,0,0)
 		        self.protocol.send_contained(grenade_packet)

                    if z < -40:
                        self.send_chat("!!CAUTION!!  Flight Altitude is too high")

                    if z < -70:
                        self.send_chat("!! W A R N I N G !!")

		    if z < -80:
		      for cl in [0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]:			
			player_pos=self.world_object.position
  		        grenade_packet.value=cl
  	  		grenade_packet.player_id=self.player_id
  			grenade_packet.position=player_pos.get()
  			grenade_packet.velocity=(0,0,0)
 		        self.protocol.send_contained(grenade_packet)
                      self.flight_reset()
                      self.send_chat("The aircraft was crashed.")

                    self.set_location((x, y, z))
                    reactor.callLater(0.01, self.flight, x, y, z, x2, y2, z2, speed,rest_bomb,gre_fired,rest_rocket,roc_fired,lookaway,left,llll,right,rrrr)

        def on_spawn(self,pos):
         	self.flight_reset
		self.aircraft=False
            	return connection.on_spawn(self,pos)

	@commands.alias('f')
	def aircraft(connection):
		self = connection
		if not self.aircraft:
			self.aircraft=True
            		self.send_chat("You riding Aircraft now. JUMP TO TAKE OFF!!")
		elif self.aircraft:
			self.aircraft=False
	            	self.send_chat("You got off Aircraft.")
	commands.add(aircraft)

	def rockelan(self,connection,(x,y,z),(vx,vy,vz)):
	 easyremove(connection,(x,y,z))
	 x+=vx*1.5
	 y+=vy*1.5
	 z+=vz*1.5

	 VTfuse = 0
	 for player in connection.protocol.players.values():
		if not (player.god or player.team == connection.team):
			 xa,ya,za = player.get_location()
			 xr,yr,zr=xa-x,ya-y,za-z
			 radius= math.sqrt(xr**2 + yr**2 + zr**2)
			 if radius<2:
				VTfuse=1
				break

	 if connection.protocol.map.get_solid(x,y,z) or x<2 or x>509 or y<2 or y>509 or z<2 or z>63 or VTfuse==1:
		if connection.protocol.map.get_solid(x,y,z) or z>63 or VTfuse==1:
		  easygre(connection,(x,y,z),(0,0,0),0)
		  easygre(connection,(x+2,y,z),(0,0,0),0)
		  easygre(connection,(x-2,y,z),(0,0,0),0)
		  easygre(connection,(x,y+2,z),(0,0,0),0)
		  easygre(connection,(x,y-2,z),(0,0,0),0)
		  easygre(connection,(x,y,z+2),(0,0,0),0)
		  easygre(connection,(x,y,z-2),(0,0,0),0)
	 	else:
			grenade_packet.value=0.0
  	  		grenade_packet.player_id=connection.player_id
  			grenade_packet.position=(x,y,z)
  			grenade_packet.velocity=(0,0,0)
 		        self.protocol.send_contained(grenade_packet)
	 else:
	  reactor.callLater(0.03,self.rockelan,connection,(x,y,z),(vx,vy,vz))
	  easyblock(connection,(x,y,z),connection.color)



	def rocket_charge(self):
	   self.rocket=True
        
        def on_animation_update(self,jump,crouch,sneak,sprint):
	    if not self.flying:

	     	if jump and self.aircraft:
	                self.flying=True
		  	self.rocket=True
	                self.send_chat("you have 100 Bombs  and 100 Rockets	")
	                self.send_chat("  W : up speed  //  S : down speed  //  Ctrl : drop bomb  //  V : shot rocket")
	                x, y, z = self.world_object.position.get()
                    	x2, y2, z2 = self.world_object.orientation.get()
	                self.flight(x, y, z, x2, y2, z2, 5.9, 100, 0, 100, 0, 0 ,0,0,0,0)

            if self.flying:

                if not self.Shift and sprint:
                    self.Shift = True
                elif self.Shift and not sprint:
                    self.Shift = False

                if not self.V and sneak:
                    self.V = True
                elif self.V and not sneak:
                    self.V = False

                if not self.Ctrl and crouch:
                    self.Ctrl = True
                elif self.Ctrl and not crouch:
                    self.Ctrl = False



            return connection.on_animation_update(self,jump,crouch,sneak,sprint)




        def on_walk_update(self, fw, bw, le, ri):
            if fw:
                self.fw = True
            else:
                self.fw = False
            if bw:
                self.bw = True
            else:
                self.bw = False
            if le:
                self.le = True
            else:
                self.le = False
            if ri:
                self.ri = True
            else:
                self.ri = False
            return connection.on_walk_update(self, fw, bw, le, ri)


        
        def on_kill(self,killer,type,grenade):
	   if self.flying:
            self.flying=False
	    player_pos=self.world_object.position
	    for cl in [0.00, 0.01, 0.02]:			
  		        grenade_packet.value=cl
  	  		grenade_packet.player_id=self.player_id
  			grenade_packet.position=player_pos.get()
  			grenade_packet.velocity=(0,0,0)
 		        self.protocol.send_contained(grenade_packet)
            self.flight_reset()
           return connection.on_kill(self,killer,type,grenade)
        
        def on_team_leave(self):
            self.flying=False
            return connection.on_team_leave(self)
    
        def on_fall(self, damage):
            if self.flying:
                self.flight_reset
                return False
            else:
                return connection.on_fall(self, damage)

        def on_disconnect(self):
            self.flying = False
            return connection.on_disconnect(self)





    
    return protocol, FlightConnection