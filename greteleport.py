#greteleport by Kuma
#Version 1

from commands import add, admin, name, alias
from pyspades.server import position_data
from math import floor

GRENADE_TELEPORT_MESSAGE = "Grenade teleport has been turned {bool}"
GRENADE_OUT = "You can't throw the grenade out of the map"

@alias('gtp')
@admin
def grenadeteleport(connection):
  protocol = connection.protocol
  protocol.grenade_teleport = not protocol.grenade_teleport
  on_off = "ON" if protocol.grenade_teleport else "OFF"
  protocol.send_chat(GRENADE_TELEPORT_MESSAGE.format(bool = on_off))

@alias('zb')
@admin
def grenadezblock(connection, value = None):
  protocol = connection.protocol
  if not value is None:
    value = int(value)
    protocol.z_blocks = value    
    protocol.send_chat("Spawn Z block set to {}".format(value))
  else:
    protocol.z_blocks = 5
    protocol.send_chat("Spawn Z block set to default value")  

@alias('u')
@name('uns')
def unstick_player(connection):
  protocol = connection.protocol
  player = connection
  if player in protocol.players:
    player.set_location_safe(player.get_location())
  
add(grenadeteleport)
add(grenadezblock)
add(unstick_player)

def apply_script(protocol, connection, config):

  class gtpConnection(connection):
    def grenade_exploded(self, grenade):
      protocol = self.protocol
      if protocol.grenade_teleport:
        position = grenade.position
        x, y, z = position.x, position.y, position.z
        x, y, z = int(floor(x))-0.5, int(floor(y))-0.5, protocol.map.get_height(x, y) - protocol.z_blocks +0.5
        if position.x < 0 or position.y < 0 or position.x > 512 or position.y > 512 or position.z < 0 or position.z > 64:
          self.send_chat(GRENADE_OUT)
          return False        
        else:
          self.world_object.set_position(x, y, z)
          position_data.x = x
          position_data.y = y 
          position_data.z = z
          self.send_contained(position_data)
          connection.set_location_safe(self, self.get_location())
      else:
        return connection.grenade_exploded(self, grenade)
        
  class gtpProtocol(protocol):
    grenade_teleport = config.get('grenade_teleport', True)
    z_blocks = config.get('z_blocks', 5)
      
      
  return gtpProtocol, gtpConnection
