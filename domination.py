"""
domination  yuyasato
"""
from pyspades.constants import *
from commands import alias,admin, add, name, get_team, get_player,where_from
from pyspades.server import Territory, Flag
from twisted.internet.reactor import callLater, seconds
from pyspades import contained as loaders

territory_capture = loaders.TerritoryCapture()
progress_bar = loaders.ProgressBar()
move_object = loaders.MoveObject()


POINT_LIMIT = 100
POINT_INTERVAL = 10
TC_basenum=3

BUILDING_ENABLED = True

@admin	
@name('build')
def build_ok(connection, points):
	global BUILDING_ENABLED
	BUILDING_ENABLED = not BUILDING_ENABLED
	connection.protocol.building = BUILDING_ENABLED
	return "build %s" % BUILDING_ENABLED
add(build_ok)

@admin	
@name('pointinterval')
def pointinterval(connection, points):
	global POINT_INTERVAL
	POINT_INTERVAL = int(points)
	connection.protocol.send_chat("point interval changed. point / %s sec" % POINT_INTERVAL)
	return "point interval changed. point / %s sec" % POINT_INTERVAL
add(pointinterval)


@alias('lim')
@admin	
@name('limitpoint')
def limitpoint(connection, limit):
	global POINT_LIMIT
	POINT_LIMIT = int(limit)
	connection.protocol.send_chat("point limit changed to %s " % POINT_LIMIT)
	return "point limit changed %s " % POINT_LIMIT
add(limitpoint)

class Territory(Flag):
	progress = 0.0
	players = None
	start = None
	rate = 0
	rate_value = 0.0
	finish_call = None
	capturing_team = None
	
	def __init__(self, *arg, **kw):
		Flag.__init__(self, *arg, **kw)
		self.players = set()
	
	def add_player(self, player):
		if not self.protocol.game_stop:
			self.get_progress(True)
			self.players.add(player)
			self.update_rate()
		
	def remove_player(self, player):
		self.get_progress(True)
		self.players.discard(player)
		self.update_rate()
	
	def update_rate(self):
		rate = 0
		for player in self.players:
			if player.team.id:
				rate += 1
			else:
				rate -= 1
		progress = self.progress
		if ((progress == 1.0 and (rate > 0 or rate == 0)) or 
		   (progress == 0.0 and (rate < 0 or rate == 0))):
			return
		self.rate = rate
		self.rate_value = rate * TC_CAPTURE_RATE
		if self.finish_call is not None:
			self.finish_call.cancel()
			self.finish_call = None
		if rate != 0:
			self.start = seconds()
			rate_value = self.rate_value
			if rate_value < 0:
				self.capturing_team = self.protocol.blue_team
				end_time = progress / -rate_value
			else:
				self.capturing_team = self.protocol.green_team
				end_time = (1.0 - progress) / rate_value
			if self.capturing_team is not self.team:
				self.finish_call = callLater(end_time, self.finish)
		self.send_progress()
	
	def send_progress(self):
		progress_bar.object_index = self.id
		if self.team is None:
			capturing_team = self.capturing_team
			team = capturing_team.other
		else:
			capturing_team = self.team.other
			team = self.team
		progress_bar.capturing_team = capturing_team.id
		rate = self.rate
		progress = self.get_progress()
		if team.id:
			rate = -rate
			progress = 1 - progress
		progress_bar.progress = progress
		progress_bar.rate = rate
		self.protocol.send_contained(progress_bar)
	
	def finish(self):
		self.finish_call = None
		protocol = self.protocol
		if self.rate > 0:
			team = protocol.green_team
		else:
			team = protocol.blue_team
		team.score += 1
		if self.team is not None:
			self.team.score -= 1
		self.team = team
		protocol.on_cp_capture(self)
		territory_capture.object_index = self.id
		territory_capture.state = self.team.id
		territory_capture.winning = False
		protocol.send_contained(territory_capture)
		
	def get_progress(self, set = False):
		"""
		Return progress (between 0 and 1 - 0 is full blue control, 1 is full
		green control) and optionally set the current progress.
		"""
		rate = self.rate_value
		start = self.start
		if rate == 0.0 or start is None:
			return self.progress
		dt = seconds() - start
		progress = max(0, min(1, self.progress + rate * dt))
		if set:
			self.progress = progress
		return progress
	
	def get_spawn_location(self):
		x1 = max(0, self.x - SPAWN_RADIUS)
		y1 = max(0, self.y - SPAWN_RADIUS)
		x2 = min(512, self.x + SPAWN_RADIUS)
		y2 = min(512, self.y + SPAWN_RADIUS)
		return self.protocol.get_random_location(True, (x1, y1, x2, y2))

def apply_script(protocol, connection, config):
	game_stop=False

	class DominationConnection(connection):
		def on_refill(self):
			return False

		def on_join(self):
			callLater(0.1, self.protocol.TC_graphic_adjust)
			return connection.on_join(self)

			
	class DominationProtocol(protocol):
		game_mode = TC_MODE
		blue_point = 0
		green_point = 0
		half_time = False

		def __init__(self, *arg, **kw):
			protocol.__init__(self, *arg, **kw)
			callLater(POINT_INTERVAL, self.domine_clock)

		def TC_graphic_adjust(self):
			for entity in self.entities:
				move_object.object_type = entity.id
				if entity.team is None:
					move_object.state = 2
				else:
					move_object.state = entity.team.id
				move_object.x = entity.x
				move_object.y = entity.y
				move_object.z = entity.z

				self.send_contained(move_object)


		def domine_clock(self):
			if not self.game_stop:
				self.TC_graphic_adjust()
				self.blue_point += self.blue_team.score
				self.green_point += self.green_team.score
				self.send_chat("%s:%s(+%s) - %s:%s(+%s)   /%s point game"%(self.blue_team.name,self.blue_point,self.blue_team.score,self.green_team.name,self.green_point,self.green_team.score, POINT_LIMIT))
				if not self.half_time:
					if self.blue_point>POINT_LIMIT/2 or self.green_point>POINT_LIMIT/2:
						self.half_time = True
						self.send_chat("--- spawn reversed ---")


				if self.blue_point>=POINT_LIMIT and self.blue_point>self.green_point:
					self.entities[0].team=self.blue_team
					self.reset_game()
					self.on_game_end()
					self.entities[0].team=None
					self.point_reset()
					self.send_chat("--- %s team win! ---"%self.blue_team.name)

				elif self.green_point>=POINT_LIMIT and self.green_point>self.blue_point:
					self.entities[0].team=self.green_team
					self.reset_game()
					self.on_game_end()
					self.entities[0].team=None
					self.point_reset()
					self.send_chat("--- %s team win! ---"%self.green_team.name)

			callLater(POINT_INTERVAL, self.domine_clock)

		def point_reset(self):
			for entity in self.entities:
				if entity.finish_call is not None:
					entity.finish_call.cancel()
					entity.finish_call = None

				entity.start = None
				entity.capturing_team = None

				entity.players=set()
				entity.rate=0
				entity.team=None
				entity.progress=0.5
			self.entities = self.get_cp_entities()

			self.green_point = 0
			self.blue_point = 0
			self.blue_team.score = 0
			self.green_team.score = 0

		def get_cp_entities(self):
			terretories=[] 
			positions=[(0,0,63)] 

			extensions=self.map_info.extensions
			if extensions.has_key("territories"):
				positions=extensions['territories']
				l=len(positions)+1

				for i in range(l-1):
					pos=positions[i]
					if len(pos)>2: 
						x,y,z=pos
					else: 
						x,y=pos
						z=self.map.get_z(x,y)
					cp=Territory(i, self, x, y, z) 
					cp.progress=0.5
					cp.team=None
					terretories.append(cp)
			else:
				for i in range(TC_basenum):
					x = 256-self.mapsize_x/2+self.mapsize_x/(TC_basenum+1)*(i+1)
					y = 256+self.mapsize_y/2-self.mapsize_y/(TC_basenum+1)*(i+1)
					z=self.map.get_z(x,y)
					cp=Territory(i, self, x, y, z) 
					cp.progress=0.5
					cp.team=None
					terretories.append(cp)
			return terretories

		def start_call(self):
			self.building = BUILDING_ENABLED
			self.game_stop=False
			self.half_time = False
			self.point_reset()
			callLater(0.5, self.point_reset)

		def on_game_end(self):
			self.game_stop=True
			return protocol.on_game_end(self)
			

		def on_map_change(self, name):
			callLater(0.3, self.start_call)
			self.point_reset()
			protocol.on_map_change(self, name) 
	
	return DominationProtocol, DominationConnection
