"""
50 over block put bug fix script 

no test was done. if some bad effect occur it is sorry.

by yuyasato20190324
"""

def apply_script(protocol, connection, config):

	class OverblockfixConnection(connection):

		def on_line_build_attempt(self, points):
			if self.blocks+5 < len(points):
				return False
			return connection.on_line_build_attempt(self, points)

	return protocol, OverblockfixConnection