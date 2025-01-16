from twisted.internet.task import LoopingCall
from math import cos, sin, atan2, degrees, radians
from pyspades.constants import *
from pyspades.common import Vertex3

def apply_script(protocol, connection, config):
    class UnboundProtocol(protocol):
        pass

    class UnboundConnection(connection):
        def pos(self):
            position = self.world_object.position
            return position.x, position.y, position.z

        def teleport_to_opposite_side(self):
            world_object = self.world_object
            if world_object:
                x, y, z = self.pos()
                if x >= 512:
                    world_object.set_position(0, y, z)
                elif x < 0:
                    world_object.set_position(511, y, z)
                elif y >= 512:
                    world_object.set_position(x, 0, z)
                elif y < 0:
                    world_object.set_position(x, 511, z)

        def on_spawn(self, pos):
            if not hasattr(self, 'loop'):
                self.loop = LoopingCall(self.teleport_to_opposite_side)
                self.loop.start(0.01)
            return connection.on_spawn(self, pos)

        # Paste the rest of the flight script below
        def flight(self, x, y, z, course, speed):
            # Paste the rest of the flight script here

        def dropbomb(self, x, y, z, x2, y2):
            # Paste the rest of the dropbomb script here

        def high_explosive(self, x, y, z):
            # Paste the rest of the high_explosive script here

        def makegre(self, x, y, z, count):
            # Paste the rest of the makegre script here

        def on_team_leave(self):
            self.flying = False
            return connection.on_team_leave(self)

        def on_fall(self, damage):
            if self.flying:
                return False
            return connection.on_fall(self, damage)

        def on_reset(self):
            self.flying = False
            return connection.on_reset(self)

    return UnboundProtocol, UnboundConnection
