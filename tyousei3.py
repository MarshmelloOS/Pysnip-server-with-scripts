def apply_script(protocol,connection,config):
	class tyouseiConnection(connection):
		def on_team_join(self,team):
			if self.team == self.protocol.blue_team and self.protocol.blue_team.count() <= self.protocol.green_team.count():
				if team == self.protocol.green_team:
					self.send_chat("Team is full, moved to %s" % self.protocol.blue_team.name)
					return self.protocol.blue_team
	 		elif self.team == self.protocol.green_team and self.protocol.green_team.count() <= self.protocol.blue_team.count():
				if team == self.protocol.blue_team:
					self.send_chat("Team is full, moved to %s" % self.protocol.green_team.name)
					return self.protocol.green_team
			return connection.on_team_join(self,team)
	return protocol,tyouseiConnection