"""
unbound by thepolm3
removes map boundaries
"""
from twisted.internet.task import LoopingCall

def apply_script(protocol,connection,config):
    class UnboundProtocol(protocol):
        pass
    class UnboundConnection(connection):
        save_vel=0.0
        loop=None
        def pos(self):
            position=self.world_object.position
            return position.x,position.y,position.z

        def goOverEdge(self):
            world_object=self.world_object
            if world_object:
                x,y,z=self.pos()
                if x>=511:
                    if self.world_object.velocity.x > 0:
                        self.world_object.set_position(0.5,y,z)
                if x<=1:
                    if self.world_object.velocity.x < 0:
                        self.world_object.set_position(511.5,y,z)
                if y>=511:
                    if self.world_object.velocity.y > 0:
                        self.world_object.set_position(x,0.5,z)
                if y<=1:
                    if self.world_object.velocity.y < 0:
                        self.world_object.set_position(x,511.5,z)

        def on_spawn(self,pos):
            if not self.loop:
                self.loop=LoopingCall(self.goOverEdge)
                self.loop.start(0.01)
            return connection.on_spawn(self,pos)

    return UnboundProtocol,UnboundConnection
