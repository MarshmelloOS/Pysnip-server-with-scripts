"""
thepolm3
makes the intel returnable by its own team
"""

from pyspades.collision import vector_collision
from twisted.internet.task import LoopingCall

#the default looks quite smooth
SPEED=200#th |  difference of the base and the intel moved in one "tick" (1/10 second)

def apply_script(protocol, connection, config):
    class TracksProtocol(protocol):

        def advance_intel(self,team):
            base,flag = team.base,team.flag
            a,b,c = base.x,base.y,base.z
            x,y,z = flag.x,flag.y,flag.z
            q,w = round(x+(a-x)/SPEED,4),round(y+(b-y)/SPEED,4)
            flag.set(q,w,self.map.get_z(q,w))
            flag.update()
            
    class TracksConnection(connection):
        cartcheck=None
        
        def on_spawn(self,pos):
            if self.cartcheck:
                self.cartcheck.stop()
            self.cartcheck=LoopingCall(self.check_cart)
            self.cartcheck.start(0.1)
            self.team.flag.update()
            return connection.on_spawn(self,pos)

        def check_cart(self):
            if self.world_object and self.team.flag:
                if vector_collision(self.world_object.position, self.team.flag):
                    self.protocol.advance_intel(self.team)
                self.team.flag.update()
        
    
    return TracksProtocol, TracksConnection
