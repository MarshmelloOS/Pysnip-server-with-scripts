from pyspades.server import block_action
from pyspades.collision import distance_3d_vector
from commands import add, admin
from map import Map
from pyspades.constants import *
import commands

@admin
def box(connection):
        if connection.boxing > 0:
            connection.boxing = 0
            return 'Building generator cancelled'
        else:
            connection.boxing = 1
            return 'Place first corner block'
add(box)

def apply_script(protocol, connection, config):
    class boxMakerConnection(connection):
        boxing = 0
        box_x = 0
        box_y = 0
        box_z = 0

        def build_box(self, first_x, first_y, first_z, second_x, second_y, second_z, boxcolor):
            for build_x in xrange(min(first_x , second_x) , max(first_x , second_x)+1):
                for build_y in xrange(min(first_y , second_y) , max(first_y , second_y)+1):
                    self.box_place_block(build_x, build_y, first_z, boxcolor)
                    self.box_place_block(build_x, build_y, second_z, boxcolor)
                for build_z in xrange(min(first_z , second_z) , max(first_z , second_z)+1):
                    self.box_place_block(build_x, first_y, build_z, boxcolor)
                    self.box_place_block(build_x, second_y, build_z, boxcolor)
            for build_z in xrange(min(first_z , second_z) , max(first_z , second_z)+1):
                for build_y in xrange(min(first_y , second_y) , max(first_y , second_y)+1):
                    self.box_place_block(first_x, build_y, build_z, boxcolor) 
                    self.box_place_block(second_x, build_y, build_z, boxcolor)                    
        
        def box_place_block(self,x,y,z,boxcolor):
            if self.god_build:
                if self.protocol.god_blocks is None:
                    self.protocol.god_blocks = set()
                self.protocol.god_blocks.add((x, y, z))
            block_action.x = x
            block_action.y = y
            block_action.z = z
            block_action.player_id = self.player_id
            block_action.value = BUILD_BLOCK
            self.protocol.send_contained(block_action, save = True)
            self.protocol.map.set_point(block_action.x, block_action.y, block_action.z, boxcolor)


        def on_block_build(self, x, y, z):
            if self.boxing == 2:
                if abs(self.box_x - x) > 32 or abs(self.box_y - y) > 32:
                    self.send_chat('Building is too large! Building cancelled.')
                    self.boxing = 0
                else:
                    self.build_box(self.box_x, self.box_y, self.box_z, x, y, z, self.color+(255,))
                    self.boxing = 0
            if self.boxing == 1:
                self.box_x = x
                self.box_y = y
                self.box_z = z
                self.send_chat('Now place opposite corner block')
                self.boxing = 2
            return connection.on_block_build(self, x, y, z)

                
    return protocol, boxMakerConnection
