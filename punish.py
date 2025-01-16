"""
Punishment made by Bori
"""
DO_NOT_USE_SKILLS = "Don't crouch, sneak, jump or sprint, use your skills"
ME_EXPLAIN = "Fight like a real man and don't do anything forbidden"


def apply_script(protocol, connection, config):
        
			
	class punishConnection(connection):
		def on_animation_update(self, jump, crouch, sneak, sprint):
			if jump or crouch or sneak or sprint:
				if self.hp>=1:
					self.hit(5)
					self.send_chat(DO_NOT_USE_SKILLS)
			return connection.on_animation_update(self,jump, crouch, sneak, sprint)		
		
		def on_kill(self, killer, type, grenade):
			killer.send_chat("Punish him more")
			return connection.on_kill(self, killer, type, grenade)
		
		
		def on_refill(self):
			return False
		
		def on_spawn(self, pos):
			self.send_chat(ME_EXPLAIN)
		
	return protocol, punishConnection