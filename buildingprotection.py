from pyspades.contained import BlockAction
from pyspades.server import block_action
from pyspades.common import Vertex3
from pyspades.constants import *

protectpoint = [[[0 for z in xrange(0, 62)] for y in xrange(0, 512)] for x in xrange(0, 512)]

def getMapProtection(map, x, y, z):
  if map.get_solid(x, y, z):
    return 1
  else:
    return 0

def initMapProtection(map):
  x = 0
  y = 0
  z = 0
  for z in xrange(3, 62, 5):
    for y in xrange(0, 512):
      for x in xrange(0, 512):
        protectpoint[x][y][z] = getMapProtection(map, x, y, z)

def checkMapProtection(x, y, z):
  if z%5 == 3 and protectpoint[x][y][z] == 1:
    return 1
  elif x%64 >= 31 and x%64 <= 32 and y%64 >= 31 and y%64 <= 32:
    return 1
  else:
    return 0

def apply_script(protocol, connection, config):
  class BuildingProtectionConnection(connection):
    def on_block_destroy(self, x, y, z, mode):
      if checkMapProtection(x, y, z):
        self.send_chat('You cant destroy Floors, Bridges and Pillars')
        return False
      elif mode == SPADE_DESTROY:
        for dz in xrange(z-1, z+2):
          if dz < 0:
            dz = 0
          if dz < 62:
            if self.protocol.map.get_solid(x, y, dz) and not checkMapProtection(x, y, dz):
                self.protocol.map.destroy_point(x, y, dz)
                block_action.x = x
                block_action.y = y
                block_action.z = dz
                block_action.value = DESTROY_BLOCK
                self.protocol.send_contained(block_action, save = True)
        return False
      elif mode == GRENADE_DESTROY:
        for dz in xrange(z-1, z+2):
          if dz < 0:
            dz = 0
          if dz < 62:
            for dy in xrange(y-1, y+2):
              if dy < 0:
                dy = 0
              if dy < 512:
                for dx in xrange(x-1, x+2):
                  if dx < 0:
                    dx = 0
                  if dx < 512:
                    if self.protocol.map.get_solid(dx, dy, dz) and not checkMapProtection(dx, dy, dz):
                      self.protocol.map.destroy_point(dx, dy, dz)
                      block_action.x = dx
                      block_action.y = dy
                      block_action.z = dz
                      block_action.value = DESTROY_BLOCK
                      self.protocol.send_contained(block_action, save = True)
        return False

  class BuildingProtectionProtocol(protocol):
    def on_map_change(self, map):
      initMapProtection(map)
      protocol.on_map_change(self, map)

  return BuildingProtectionProtocol, BuildingProtectionConnection