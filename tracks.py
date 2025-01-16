"""
thepolm3
tracks, based on "payload" from tf2
idea by ninja pig
"""

from pyspades.collision import vector_collision
from twisted.internet.task import LoopingCall
#the default looks quite smooth
STEPS=1000
SPEED=10#moves per second
HIDE_POS=(0,0,63)
def apply_script(protocol, connection, config):
    
    class TracksProtocol(protocol):
        game_mode=xstep=ystep=xg=yg=winning_allowed=0

        def advance_cart(self,player):
            team=player.team
            cart=self.green_team.flag
            x,y=float(cart.x),float(cart.y)
            if team==self.green_team:
                x+=float(self.xstep)
                y+=float(self.ystep)
            else:
                x-=float(self.xstep)
                y-=float(self.ystep)
            cart.set(x,y,self.map.get_z(x,y))
            cart.update()
            if vector_collision(team.other.base, cart):
                self.winning_allowed=1
                player.take_flag()
                player.capture_flag()
                self.winning_allowed=0
                self.reset_cart()
                for player in self.players.values():
                    player.spawn()

        def reset_cart(self):
            cart=self.green_team.flag
            x,y=self.xstep*(STEPS/2)+self.xg,self.ystep*(STEPS/2)+self.yg
            cart.set(x,y,self.map.get_z(x,y))
            cart.update()

        def initial_setup(self):
            g=self.green_team.base #temp
            b=self.blue_team.base
            xg,yg=float(g.x),float(g.y)
            xb,yb=float(b.x),float(b.y)
            self.xstep=(xb-xg)/STEPS
            self.ystep=(yb-yg)/STEPS
            self.xg,self.yg=xg,yg
            #flagsetting time!
            self.reset_cart()

        def on_connect(self,connection):
            if not self.xstep:
                self.initial_setup()
            return protocol.on_connect(self,connection)

        def on_advance(self,map):
            for player in self.players.values():
                player.cartcheck = None
            return protocol.on_advance(self,map)

        def on_flag_spawn(self,x,y,z,flag,entity_id):
            return(0,0,0)

    class TracksConnection(connection):
        cartcheck=None
        
        def on_spawn(self,pos):
            if self.cartcheck:
                self.cartcheck.stop()
            self.cartcheck=LoopingCall(self.check_cart)
            self.cartcheck.start(1/SPEED)
            return connection.on_spawn(self,pos)

        def check_cart(self):
            if self.protocol.green_team and self.protocol.green_team.flag and self.world_object:
                if vector_collision(self.world_object.position, self.protocol.green_team.flag):
                    self.protocol.advance_cart(self)
        
        def on_flag_take(self):
            if self.protocol.winning_allowed:
                return connection.on_flag_take(self)
            return False
            

        def on_flag_capture(self):
            if self.protocol.winning_allowed:
                return connection.on_flag_capture(self)
            return False
    
    return TracksProtocol, TracksConnection
