'''
LineSpqr Script by Bori
'''

YOU_ARE_A_LINESSPQR_MASTER = "You are a LineSPQR master"

def apply_script(protocol, connection, config):
	class linesConnection(connection):
		def on_spawn(self, pos):
			if "|SPQR|" in self.name:
				self.send_chat(YOU_ARE_A_LINESSPQR_MASTER)
			return connection.on_spawn(self, pos)
	return protocol, linesConnection
