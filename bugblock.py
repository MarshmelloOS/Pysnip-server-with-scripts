"""
bug block protect 

the bug occur when line build start at broken block

by yuyasato20190217
"""

from pyspades.constants import *
from twisted.internet.reactor import callLater
from pyspades.contained import BlockAction

def apply_script(protocol, connection, config):

	class BugblockConnection(connection):
		bugblock = []

		def on_line_build_attempt(self, points):
			if not self.protocol.map.has_neighbors(*points[0]):	
				self.bugblock = points
				motomoto=[]
				for point in self.bugblock:
					if self.protocol.map.get_solid(*point):
						motomoto.append(point)
				for point in motomoto:
					self.bugblock.remove(point)
				block_action = BlockAction()
				block_action.x = points[1][0]
				block_action.y = points[1][1]
				block_action.z = points[1][2]
				block_action.player_id = self.player_id
				block_action.value = BUILD_BLOCK
				self.protocol.send_contained(block_action, save = True)
				self.protocol.map.set_point(points[1][0],points[1][1],points[1][2], self.color)
				callLater(0.001, self.bugblock_break)
			return connection.on_line_build_attempt(self, points)

		def bugblock_break(self):
			for point in self.bugblock:
				block_action = BlockAction()
				block_action.x = point[0]
				block_action.y = point[1]
				block_action.z = point[2]
				block_action.value = DESTROY_BLOCK
				block_action.player_id = self.player_id
				self.on_block_removed(*point)
				self.protocol.map.remove_point(*point)
				self.protocol.send_contained(block_action, save = True)
			self.protocol.update_entities()			

	return protocol, BugblockConnection