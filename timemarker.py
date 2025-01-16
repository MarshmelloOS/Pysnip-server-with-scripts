"""
time trace marker script
by yuyasato


modified from
marker.py (Maintainer: hompy)
"""

import csv
from StringIO import StringIO
from collections import deque, defaultdict
from functools import partial
from itertools import izip, islice, chain
from random import choice
from twisted.internet.reactor import callLater, seconds
from pyspades.world import cube_line
from pyspades.server import block_action, block_line, set_color, chat_message
from pyspades.common import make_color, to_coordinates
from pyspades.constants import *
from commands import add, admin, get_player, name, alias
from pyspades.world import Grenade
from pyspades.server import grenade_packet

MARK_TARGET = 0  # 0=allplayer, 1=blue only,   2=green only
WHO_CAN_SEE = 0  # 0=allplayer, 1=fiend only,  2=enemy only
EXPLODE_EFFECT = True  # explode sound and effect at the position on the timing of marker.

SCANNING = True
TIMEMARKER_FREQ = 10 #seconds
TIMEMARKER_LOOPING = True

S_PLAYER_ENABLED = '{player} can place markers again'
S_PLAYER_DISABLED = '{player} is disallowed from placing markers'
S_ENABLED = 'Markers have been enabled'
S_DISABLED = 'Markers have been disabled'

S_REACHED_LIMIT = 'Your team has too many markers of that kind!'

@admin
def clear(connection):
	if connection not in connection.protocol.players:
		raise ValueError()
	connection.destroy_markers()
	return S_CLEARED

@name('togglemarkers')
@admin
def toggle_markers(connection, player = None):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
		player.allow_markers = not player.allow_markers
		message = S_PLAYER_ENABLED if player.allow_markers else S_PLAYER_DISABLED
		message = message.format(player = player.name)
		protocol.send_chat(message, irc = True)
	else:
		protocol.allow_markers = not protocol.allow_markers
		message = S_ENABLED if protocol.allow_markers else S_DISABLED
		connection.protocol.send_chat(message, irc = True)

@admin
def markers(connection):
	if connection not in connection.protocol.players:
		raise ValueError()
	connection.send_lines(S_HELP)

add(clear)
add(toggle_markers)
add(markers)

@alias('tm')
@name('time_marker')
@admin
def time_marker(connection):
	global TIMEMARKER_LOOPING
	TIMEMARKER_LOOPING = not TIMEMARKER_LOOPING
	connection.protocol.marker_time_loop()
add(time_marker)


class BaseMarker():
	name = 'Marker'
	triggers = []
	whose=None
	background = None
	background_class = None
	duration = None
	color = None
	random_colors = None
	team_color = False
	lines = []
	points = []
	always_there = False
	maximum_instances = None
	expire_call = None
	z = 0
	
	def __init__(self, protocol, team, x, y, who=None):
		self.protocol = protocol
		self.team = team
		self.whose=who
		self.x = x
		self.y = y
		if self.random_colors:
			self.color = choice(self.random_colors)
		elif self.team_color:
			self.color = make_color(*team.color)
		self.blocks = set()
		base_lines, base_points = self.lines, self.points
		self.lines, self.points = [], []
		for line in base_lines:
			self.make_line(*line)
		for point in base_points:
			self.make_block(*point)
		# find markers we're colliding with
		has_timer = self.duration is not None
		collisions = []
		current_time = seconds()
		worst_time = current_time + self.duration if has_timer else None
		for marker in protocol.markers:
			intersect = marker.blocks & self.blocks
			if intersect:
				self.blocks -= intersect
				collisions.append(marker)
		self.build()
		team.marker_count[self.__class__] += 1
		protocol.markers.append(self)
		if self.background_class:
			self.background = self.background_class(protocol, team, x, y)
	
	def release(self):
		if self.expire_call and self.expire_call.active():
			self.expire_call.cancel()
		self.expire_call = None
		self.team.marker_count[self.__class__] -= 1
		self.protocol.markers.remove(self)
	
	def expire(self):
		self.destroy()
		self.release()
		if self.background:
			self.background.expire()
	"""
	@classmethod
	def is_triggered(cls, chat):
		return any(word in chat for word in cls.triggers)
	"""
	def make_block(self, x, y):
		x += self.x
		y += self.y
		if x < 0 or y < 0 or x >= 512 or y >= 512:
			return
		block = (x, y, self.z)
		self.blocks.add(block)
		self.points.append(block)
	
	def make_line(self, x1, y1, x2, y2):
		x1 = max(0, min(511, self.x + x1))
		y1 = max(0, min(511, self.y + y1))
		x2 = max(0, min(511, self.x + x2))
		y2 = max(0, min(511, self.y + y2))
		z = self.z
		line = (x1, y1, z, x2, y2, z)
		self.blocks.update(cube_line(*line))
		self.lines.append(line)
	
	def build(self, sender = None):
		sender = sender or self.protocol.send_contained
		self.send_color(sender)
		for line in self.lines:
			self.send_line(sender, *line)
		for point in self.points:
			self.send_block(sender, *point)
	
	def destroy(self, sender = None):
		# breaking a single block would make it come tumbling down, so we have
		# to destroy them all at once
		sender = sender or self.protocol.send_contained
		for block in self.blocks:
			self.send_block_remove(sender, *block)
	
	def send_color(self, sender):
		set_color.value = self.color
		set_color.player_id = 32
		if WHO_CAN_SEE==1:
			sender(set_color, team = self.team)			
		elif WHO_CAN_SEE==2:
			sender(set_color, team = self.team.other)
		else:
			sender(set_color)
	
	def send_block(self, sender, x, y, z, value = BUILD_BLOCK):
		block_action.value = value
		block_action.player_id = 32
		block_action.x = x
		block_action.y = y
		block_action.z = z
		if WHO_CAN_SEE==1:
			sender(block_action, team = self.team)			
		elif WHO_CAN_SEE==2:
			sender(block_action, team = self.team.other)
		else:
			sender(block_action)
	
	def send_line(self, sender, x1, y1, z1, x2, y2, z2):
		block_line.player_id = 32
		block_line.x1 = x1
		block_line.y1 = y1
		block_line.z1 = z1
		block_line.x2 = x2
		block_line.y2 = y2
		block_line.z2 = z2
		if WHO_CAN_SEE==1:
			sender(block_line, team = self.team)			
		elif WHO_CAN_SEE==2:
			sender(block_line, team = self.team.other)
		else:
			sender(block_line)
	
	def send_block_remove(self, sender, x, y, z):
		self.send_block(sender, x, y, z, DESTROY_BLOCK)

def parse_string_map(xs_and_dots):
	# greedily attempt to get the least amount of lines and blocks required
	# to build the shape. best (worst) function ever
	reader = csv.reader(StringIO(xs_and_dots), delimiter = ' ')
	rows = [s for s in (''.join(row) for row in reader) if s.strip()]
	lines, points = [], []
	if not rows:
		return lines, points
	
	width, height = len(rows[0]), len(rows)
	off_x, off_y = -width // 2, -height // 2
	for y, row in enumerate(rows):
		columns = [''.join(l[y:]).split('.', 1)[0] for l in izip(*rows)]
		it = enumerate(columns)
		for x, column in it:
			h = len(row[x:].split('.', 1)[0])
			v = len(column)
			if h == v == 0:
				continue
			if max(h, v) == 1:
				points.append((x + off_x, y + off_y))
			elif h >= v:
				lines.append((x + off_x, y + off_y, x + off_x + h - 1, y + off_y))
				row = '.' * (x + h) + row[(x + h):]
				next(islice(it, h, h), None) # forward the iterator
			else:
				lines.append((x + off_x, y + off_y, x + off_x, y + off_y + v - 1))
				rows[y:y + v] = (r[:x] + '.' + r[x + 1:] for r in rows[y:y + v])
	return lines, points

class EnemyBackground(BaseMarker):
	color = make_color(0, 0, 0)
	s = """
    . . X X X X X . .
    . X X X X X X X .
    X X X X X X X X X
    X X X X X X X X X
    X X X X X X X X X
    X X X X X X X X X
    X X X X X X X X X
    . X X X X X X X .
    . . X X X X X . .
    """

class Enemy(BaseMarker):
	name = 'Point'
	background_class = EnemyBackground
	duration = 40.0
	always_there = True
	color = make_color(255, 0, 0)
	s = """
    . . X X X . .
    . X X X X X .
    X X X X X X X
    X X X X X X X
    X X X X X X X
    . X X X X X .
    . . X X X . .
    """

other_markers = [Enemy]
background_markers = []

# turn bitmap into line and block instructions
for cls in chain( other_markers, background_markers):
	if cls.background_class:
		background_markers.append(cls.background_class)
	cls.lines, cls.points = parse_string_map(cls.s)

def apply_script(protocol, connection, config):
	class MarkerConnection(connection):
		allow_markers = True
		last_marker = None
		sneak_presses = None
		
		def send_markers(self):
			is_self = lambda player: player is self
			send_me = partial(self.protocol.send_contained, rule = is_self)
			for marker in self.protocol.markers:
				marker.build(send_me)
		
		def destroy_markers(self):
			is_self = lambda player: player is self
			send_me = partial(self.protocol.send_contained, rule = is_self)
			for marker in self.protocol.markers:
				marker.destroy(send_me)
		
		def make_marker(self, marker_class, location):
			marker_max = marker_class.maximum_instances
			if (marker_max is not None and
				self.team.marker_count[marker_class] >= marker_max):
				self.send_chat(S_REACHED_LIMIT)
				return
			new_marker = marker_class(self.protocol, self.team, location[0],location[1],self)
			self.last_marker = seconds()

		def on_login(self, name):
			self.send_markers()
			self.sneak_presses = deque(maxlen = 2)
			connection.on_login(self, name)
		
		def on_team_changed(self, old_team):
			if old_team and not old_team.spectator:
				new_team, self.team = self.team, old_team
				self.destroy_markers()
				self.team = new_team
			if self.team and not self.team.spectator:
				self.send_markers()
			connection.on_team_changed(self, old_team)
		
		def marker_time(self):
			if self:
				if not self.disconnected:
					for marker in self.protocol.markers:
						if marker.whose == self:
							marker.expire()
					x,y,z = self.world_object.position.get()
					if EXPLODE_EFFECT:
						grenade_packet.value = 0
						grenade_packet.player_id=self.player_id
						grenade_packet.position=x,y,z
						grenade_packet.velocity=(0,0,0)
						self.protocol.send_contained(grenade_packet)
					location = x,y
					callLater(0.05,self.make_marker,Enemy,location )		

		def on_reset(self):
			for marker in self.protocol.markers:
				if marker.whose == self:
					marker.expire()
			return connection.on_reset(self)
	
	class MarkerProtocol(protocol):
		allow_markers = True
		markers = None

		def marker_time_loop(self):
			if TIMEMARKER_LOOPING:
				if SCANNING:
					if MARK_TARGET==0 or MARK_TARGET==1:
						for player in self.blue_team.get_players():
							x,y,z = player.world_object.position.get()
							sctime = y*512.0+x 
							callLater(1/512.0/512.0*sctime,player.marker_time)
					if MARK_TARGET==0 or MARK_TARGET==2:
						for player in self.green_team.get_players():
							x,y,z = player.world_object.position.get()
							sctime = y*512.0+x 
							callLater(1/512.0/512.0*sctime,player.marker_time)				
				else:
					if MARK_TARGET==0 or MARK_TARGET==1:
						for player in self.blue_team.get_players():
							player.marker_time()
					if MARK_TARGET==0 or MARK_TARGET==2:
						for player in self.green_team.get_players():
							player.marker_time()
				callLater(TIMEMARKER_FREQ,self.marker_time_loop)
			else:
				for marker in self.markers:
					marker.expire()
		
		def on_map_change(self, map):
			for team in (self.blue_team, self.green_team):
				team.intel_marker = None
				team.marker_calls = []
				team.marker_count = defaultdict(int)
			self.markers = []
			protocol.on_map_change(self, map)
		
		def on_map_leave(self):
			for marker in self.markers[:]:
				marker.release()
			self.markers = None
			for team in (self.blue_team, self.green_team):
				team.intel_marker = None
				for call in team.marker_calls:
					if call.active():
						call.cancel()
				team.marker_calls = None
				team.marker_count = None
			protocol.on_map_leave(self)
	
	return MarkerProtocol, MarkerConnection