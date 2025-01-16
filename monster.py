# -*- coding: utf-8 -*-

"""
モンスターと戦うゲームモード

"""

from pyspades.constants import *
from easyaos import *
from pyspades.server import create_player, intel_capture
from math import sqrt, acos, atan2,pi, cos, sin, fabs
from commands import add, admin, name, alias, join_arguments

SUMMONER_LOCATION = (511, 511)	#ダミープレイヤーの座標

BOSS_HP = 10000			#ボスの体力
BOSS_SPEED = 2			#ボスのスピード
BOSS_ROTATE = pi/12		#ボスの回転能

HENCHMEN_HP = 100		#雑魚の体力
HENCHMEN_SPEED = 4		#雑魚のスピード
HENCHMEN_ROTATE = pi/4	#雑魚の回転能	

SHOOT_RAY_LENGTH = 128	#銃の射程距離
SPADE_RAY_LENGTH = 20	#スペードの射程距離

"""
各武器の基礎ダメージ
"""
RIFLE_DAMAGE = 10
SMG_DAMAGE = 3
SHOTGUN_DAMAGE = 10000
SPADE_DAMAGE = 50
GRENADE_DAMAGE = 5000


"""
モンスターに必要なconnection情報を持たせるためのダミープレイヤー
infからのいただきもの
"""
class DummyPlayer():
	protocol = None
	team = None
	player_id = None
	monster = None
	
	#初期化
	def __init__(self, prot):
		self.protocol = prot
		self.team = self.protocol.green_team
		self.acquire_player_id()
		print("dummy player was created")
	
	#IDのダブりチェックをして、ダミープレイヤーを生成し直す
	def acquire_player_id(self):
		max_players = min(32, self.protocol.max_players)
		if len(self.protocol.connections) >= max_players:
			try:
				self.player_id = next(self.team.get_players()).player_id
			except StopIteration:
				self.player_id = None
			return self.player_id is not None
		self.player_id = self.protocol.player_ids.pop()
		self.protocol.player_ids.put_back(self.player_id)
		x, y = SUMMONER_LOCATION
		create_player.x = x
		create_player.y = y
		create_player.z = self.protocol.map.get_z(x, y)
		create_player.weapon = RIFLE_WEAPON
		create_player.player_id = self.player_id
		create_player.name = "monster"
		create_player.team = self.team.id
		self.protocol.send_contained(create_player, save = True)
		return True
		
	#モンスターを生成する
	def summon(self):
		self.monster = Monster(self, (512, 255, 10), (-1, 0, 0), 0)
		self.monster.move()		#このmoveはモンスターのHPが0になるまで自動的にループする。
		self.monster.checkHP()
		
		self.protocol.monsters.append(self.monster)
		print("dummy summoned a monster")
	
	#得点する
	def score(self):
		if self.player_id in self.protocol.players:
			self.acquire_player_id()
		winning = (self.protocol.max_score not in (0, None) and 
			self.team.score + 1 >= self.protocol.max_score)
		self.team.score += 1
		intel_capture.player_id = self.player_id
		intel_capture.winning = winning
		self.protocol.send_contained(intel_capture, save = True)
		if winning:
			print("winning")
			for monster in self.protocol.monsters:
				monster.HP = 0
			self.team.other.initialize()
			for player in self.protocol.players.values():
				player.hp = None
				if player.team is not None:
					player.spawn()
			self.protocol.on_game_end()
			print("game end")


#モンスターの抽象クラス
class Monster:
	connection = None	#ダミープレイヤーの情報
	position = None		#現在の座標
	forward = None		#向き
	target = None
	type = 0			#ボスは0、雑魚は１
	mode = 0			#戦闘モード
	HP	= 0				#体力
	speed = 0			#速度
	rotate = 0			#回転能
	body = None			#体を構成するブロック座標の配列
	bodyDef = None		#bodyの定義用配列
	
	#初期化
	def __init__(self, connection, pos, fwd, type):
		self.connection = connection
		self.position = pos
		self.forward = fwd
		self.target = self.connection.protocol.targetLocation
		self.type = type
				
		#ボスモンスター
		if self.type == 0:
			self.HP = BOSS_HP
			self.speed = BOSS_SPEED
			self.rotate = BOSS_ROTATE
			self.bodyDef = [
				#前面
				(3, -1, 0, 192, 0, 0),
				(3, 1, 0, 192, 0, 0),
				(3, -2, 0, 255, 255, 255),
				(3, -1, 1, 255, 255, 255),
				(3, 1, 1, 255, 255, 255),
				(3, 2, 0, 255, 255, 255),
				(3, -1, -1, 0, 0, 0),
				(3, -1, 0, 192, 0, 0),
				(3, 0, -2, 0, 0, 0),
				(3, 0, -1, 0, 0, 0),
				(3, 0, 0, 0, 0, 0),
				(3, 0, 1, 0, 0, 0),
				(3, 0, 2, 0, 0, 0),
				(3, 1, -1, 0, 0, 0),
				(3, 1, 0, 192, 0, 0),
				
				#上面
				(2, 0, -3, 0, 0, 0),
				(1, -1, -3, 0, 0, 0),
				(1, 0, -3, 0, 0, 0),
				(1, 1, -3, 0, 0, 0),
				(0, -2, -3, 0, 0, 0),
				(0, -1, -3, 0, 0, 0),
				(0, 0, -3, 0, 0, 0),
				(0, 1, -3, 0, 0, 0),
				(0, 2, -3, 0, 0, 0),
				(-1, -1, -3, 0, 0, 0),
				(-1, 0, -3, 0, 0, 0),
				(-1, 1, -3, 0, 0, 0),
				(-2, 0, -3, 0, 0, 0),
				
				#下面
				(2, 0, 3, 0, 0, 0),
				(1, -1, 3, 0, 0, 0),
				(1, 0, 3, 0, 0, 0),
				(1, 1, 3, 0, 0, 0),
				(0, -2, 3, 0, 0, 0),
				(0, -1, 3, 0, 0, 0),
				(0, 0, 3, 0, 0, 0),
				(0, 1, 3, 0, 0, 0),
				(0, 2, 3, 0, 0, 0),
				(-1, -1, 3, 0, 0, 0),
				(-1, 0, 3, 0, 0, 0),
				(-1, 1, 3, 0, 0, 0),
				(-2, 0, 3, 0, 0, 0),
				
				#右面
				(2, 3, 0, 0, 0, 0),
				(1, 3, -1, 0, 0, 0),
				(1, 3, 0, 0, 0, 0),
				(1, 3, 1, 0, 0, 0),
				(0, 3, -2, 0, 0, 0),
				(0, 3, -1, 0, 0, 0),
				(0, 3, 1, 0, 0, 0),
				(0, 3, 2, 0, 0, 0),
				(-1, 3, -1, 0, 0, 0),
				(-1, 3, 0, 0, 0, 0),
				(-1, 3, 1, 0, 0, 0),
				(-2, 3, 0, 0, 0, 0),
				
				#左面
				(2, -3, 0, 0, 0, 0),
				(1, -3, -1, 0, 0, 0),
				(1, -3, 0, 0, 0, 0),
				(1, -3, 1, 0, 0, 0),
				(0, -3, -2, 0, 0, 0),
				(0, -3, -1, 0, 0, 0),
				(0, -3, 1, 0, 0, 0),
				(0, -3, 2, 0, 0, 0),
				(-1, -3, -1, 0, 0, 0),
				(-1, -3, 0, 0, 0, 0),
				(-1, -3, 1, 0, 0, 0),
				(-2, -3, 0, 0, 0, 0),
				
				#背面
				(-3, -2, 0, 0, 0, 0),
				(-3, -1, -1, 0, 0, 0),
				(-3, -1, 0, 0, 0, 0),
				(-3, -1, 1, 0, 0, 0),
				(-3, 0, -2, 0, 0, 0),
				(-3, 0, -1, 0, 0, 0),
				(-3, 0, 0, 0, 0, 0),
				(-3, 0, 1, 0, 0, 0),
				(-3, 0, 2, 0, 0, 0),
				(-3, 1, -1, 0, 0, 0),
				(-3, 1, 0, 0, 0, 0),
				(-3, 1, 1, 0, 0, 0),
				(-3, 2, 0, 0, 0, 0),
				
				#腕
				(4, -6, 0, 0, 0, 0),
				(4, -5, -1, 0, 0, 0),
				(4, -5, 1, 0, 0, 0),
				(4, -4, 0, 0, 0, 0),
				(4, 4, 0, 0, 0, 0),
				(4, 5, -1, 0, 0, 0),
				(4, 5, 1, 0, 0, 0),
				(4, 6, 0, 0, 0, 0),
				(3, -5, 0, 0, 0, 0),
				(3, 5, 0, 0, 0, 0),
				(2, -5, 0, 0, 0, 0),
				(2, 5, 0, 0, 0, 0),
				(1, -5, 0, 0, 0, 0),
				(1, 5, 0, 0, 0, 0),
				(0, -5, 0, 0, 0, 0),
				(0, -4, 0, 0, 0, 0),
				(0, 4, 0, 0, 0, 0),
				(0, 5, 0, 0, 0, 0),
				
				(2, -2, -1, 0, 0, 0),
				(2, -2, 1, 0, 0, 0),
				(2, -1, -2, 0, 0, 0),
				(2, -1, 2, 0, 0, 0),
				(2, 1, -2, 0, 0, 0),
				(2, 1, 2, 0, 0, 0),
				(2, 2, -1, 0, 0, 0),
				(2, 2, 1, 0, 0, 0),
				
				(1, -2, -2, 0, 0, 0),
				(1, -2, 2, 0, 0, 0),
				(1, 2, -2, 0, 0, 0),
				 (1, 2, 2, 0, 0, 0),
				
				(-1, -2, -2, 0, 0, 0),
				(-1, -2, 2, 0, 0, 0),
				(-1, 2, -2, 0, 0, 0),
				(-1, 2, 2, 0, 0, 0),
				
				(-2, -2, -1, 0, 0, 0),
				(-2, -2, 1, 0, 0, 0),
				(-2, -1, -2, 0, 0, 0),
				(-2, -1, 2, 0, 0, 0),
				(-2, 1, -2, 0, 0, 0),
				(-2, 1, 2, 0, 0, 0),
				(-2, 2, -1, 0, 0, 0),
				(-2, 2, 1, 0, 0, 0),
				
				(-2, 0, 0, 0, 0, 0),
				(-1, 0, 0, 0, 0, 0),
				(0, 0, 0, 0, 0, 0),
				(0, 0, -2, 0, 0, 0),
				(0, 0, -1, 0, 0, 0),
				(0, 0, 1, 0, 0, 0),
				(0, 0, 2, 0, 0, 0),
				(0, -3, 0, 0, 0, 0),
				(0, -2, 0, 0, 0, 0),
				(0, -1, 0, 0, 0, 0),
				(0, 1, 0, 0, 0, 0),
				(0, 2, 0, 0, 0, 0),
				(0, 3, 0, 0, 0, 0),
				(1, 0, 0, 0, 0, 0),
				(2, 0, 0, 0, 0, 0)
			]
	
	#移動するたびに新しい座標で体を構成するブロックの座標を再定義する
	#現在位置の座標と体の向きからブロックを置く場所を算出
	def defineBody(self):
		x, y, z = self.position
		vx, vy, vz = self.forward
		dir = atan2(vy, vx)
		elv = acos(vz)
		self.body = []
		for location in self.bodyDef:
			dx, dy, dz, r, g, b = location
			bx = x + dx*cos(dir) - dy*sin(dir)
			by = y + dx*sin(dir) + dy*cos(dir)
			bz = z + dz
			point = ((bx, by, bz), (r, g, b))
			self.body.append(point)
	
	#移動した先に新しい体を組み立てる
	def makeBody(self):
		for point in self.body:
			location, color = point
			x, y, z = location
			if 0<=x<512 and 0<=y<512 and 0<=z<62:
				if not self.connection.protocol.map.get_solid(x, y, z):
					easyblock(self.connection, location, color)
	
	#移動する前に今いる座標の体を消す
	def removeBody(self):
		for point in self.body:
			x, y, z = point[0]
			if 0<=x<512 and 0<=y<512 and 0<=z<62:
				if self.connection.protocol.map.get_solid(x, y, z):
					easyremove(self.connection, point[0])
	
	#攻撃の当たり判定用。送られた座標がbodyに含まれれば真を返す
	def isBody(self, (x, y, z)):
		if self.HP > 0:
			for point in self.body:
				bx, by, bz = point[0]
				if (x-1)<bx<(x+1) and (y-1)<by<(y+1) and (z-1)<bz<(z+1):
					return True
		return False
	
	#ダメージ処理
	def hit(self, damage):
		self.HP -= damage
		if self.HP < 0:
			self.HP = 0
	
	#HP表示
	def checkHP(self):
		if self.HP > 0:
			msg = " monster remain" + str(self.HP) + "/" + str(BOSS_HP) + "HP"
			gage = '['
			for i in range(0, 10000, 200):
				if i <= self.HP:
					gage += '#'
				else:
					gage += ' '
			gage += ']'
			self.connection.protocol.send_chat(gage, global_message = True)
			self.connection.protocol.send_chat(msg, global_message = True)
			print(self.HP)
			reactor.callLater(60, self.checkHP)
	
	#索敵して移動
	def move(self):
		x, y, z = self.position
		vx, vy, vz = self.forward
		tx, ty, tz = self.target
		targetName = "Base"
		capture = False
		
		dx = tx - x
		dy = ty - y
		dz = tz - z - 5
		distance = sqrt(dx**2 + dy**2 + dz**2)
		
		if distance < 10:
			self.connection.score()
		
		playerNum = 0
		for player in self.connection.protocol.blue_team.get_players():
			px, py, pz = player.get_location()
			dx2 = px - x
			dy2 = py - y
			dz2 = pz - z - 5
			radius = sqrt(dx2**2 + dy2**2 + dz2**2)
		
			if radius < 32:
				player.hit(5)
			
			if radius < distance and radius < 64:
				distance = radius
				dx = dx2
				dy = dy2
				dz = dz2
				targetName = player.name
				
			playerNum += 1
			
		if playerNum >= 1:
			
			tgtDir = atan2(dy/distance, dx/distance)
			tgtElv = acos(dz/distance)
			dir = atan2(vy, vx)
			elv = acos(vz)
			
			dirGap = tgtDir - dir
			if dirGap > pi/24:
				if dirGap <= pi:
					dir += self.rotate
				else:
					dir -= self.rotate
			elif dirGap < -1*pi/24:
				if dirGap >= -1 * pi:
					dir -= self.rotate
				else:
					dir += self.rotate
			
			if dir > pi:
				dir -= 2*pi
			elif dir < -1 * pi:
				dir += 2*pi
			
			if tgtElv > elv:
				elv += self.rotate
			elif tgtElv < elv:
				elv -= self.rotate
			
			vx = cos(dir)
			vy = sin(dir)
			vz = cos(elv)
			self.forward = (vx, vy, vz)
			
			x += vx * self.speed
			y += vy * self.speed
			z += vz * self.speed
			self.position = (x, y, z)
			
			self.defineBody()
			self.makeBody()
			reactor.callLater(0.4, self.removeBody)
			
		if self.HP > 0:
			reactor.callLater(0.5, self.move)


def apply_script(protocol, connection, config):
	class MonsterProtocol(protocol):
		
		targetLocation = None
		monsters = []			#将来的にモンスターが手下を数体召喚するようにしたいので配列に格納
		summoner = None
		mapChanged = False
		
		#マップアドヴァンスした時だけフラグを建てる
		#（これをしないとラウンド終了時までモンスターを召喚してしまって、ラウンドごとにモンスターが増えるようになる）
		def on_map_change(self, map):
			self.summoner = None
			self.summoner = DummyPlayer(self)
			self.mapChanged = True
		
		#青テントがスポーンしたら、モンスターを召喚して、ターゲットの座標としてテントの座標を入力する
		def on_base_spawn(self, x, y, z, base, entity_id):
			if entity_id == BLUE_BASE:
				self.monsters = []
				if self.mapChanged:
					self.mapChanged = False
					self.targetLocation = (x, y, z)
					self.summoner.summon()
		
	class MonsterConnection(connection):
		
		fire = False		#連射判定
		cool_down = False	#クリック連打対処
		
		#クールダウン終了
		def open_fire(self):
			self.cool_down = False
		
		#モンスターに攻撃が当たった時の処理
		def damage_monster(self, monster, type):
			damage = 0
			cool_down_time = 0
			next_fire = 0
			if type == RIFLE_WEAPON:
				damage = RIFLE_DAMAGE
				cool_down_time = 0.4
				next_fire = 0.5
			elif type == SMG_WEAPON:
				damage = SMG_DAMAGE
				next_fire = 0.11
			elif type == SHOTGUN_WEAPON:
				x, y, z = self.get_location()
				tx, ty, tz = monster.position
				distance = (x-tx)**2 + (y-ty)**2 + (z-tz)**2
				damage = 1 + int(SHOTGUN_DAMAGE/distance)
				cool_down_time = 0.9
				next_fire = 1.0
			elif type == SPADE_TOOL:
				damage = SPADE_DAMAGE
				next_fire = 0.2
			monster.hit(damage)
			self.send_chat("you gave " + str(damage) +" damage to the monster!")
			if monster.HP > 0:
				if cool_down_time > 0:
					self.cool_down = True
					reactor.callLater(cool_down_time, self.open_fire)
				reactor.callLater(next_fire, self.keep_on_fire)
			else:
				self.send_chat("you defeated the monster!")
				if monster.type == 0:
					for monster in self.protocol.monsters:
						monster.HP = 0
					self.protocol.monsters = []
					for i in xrange(0, 10):
						self.take_flag()
						self.capture_flag()
		
		#強制青join
		def on_team_join(self, team):
			if team == self.protocol.green_team:
				self.team = self.protocol.blue_team
				return False
		
		#銃とスペードの攻撃判定
		def on_shoot_set(self, fire):
			self.fire = fire
			if fire and not self.cool_down:
				self.keep_on_fire()
			return connection.on_shoot_set(self, fire)
		
		#連射している間繰り返しダメージ判定を行う
		def keep_on_fire(self):
			if self.fire:
				if self.tool == WEAPON_TOOL:
					location = self.world_object.cast_ray(SHOOT_RAY_LENGTH)
					if location:
						for monster in self.protocol.monsters:
							if monster.isBody(location):
								self.damage_monster(monster, self.weapon)
								
				elif self.tool == SPADE_TOOL:
					location = self.world_object.cast_ray(SPADE_RAY_LENGTH)
					if location:
						for monster in self.protocol.monsters:
							if monster.isBody(location):
								self.damage_monster(monster, SPADE_TOOL)
		
		#グレネードによるダメージの判定
		def on_block_destroy(self, x, y, z, mode):
			if mode == GRENADE_DESTROY:
				for monster in self.protocol.monsters:
					mx, my, mz = monster.position
					distance = max(1, sqrt((mx-x)**2 + (my-y)**2 + (mz-z)**2))
					if distance <= 46:
						damage = int(GRENADE_DAMAGE / (distance**3))
						monster.hit(damage)
						if monster.HP == 0:
							if monster.type == 0:
								for j in range(0, 10):
									self.take_flag()
									self.capture_flag()
									for monster in self.protocol.monsters:
										monster.HP = 0
							else:
								del monster
							self.send_chat("you defeated the monster!")
						else:
							self.send_chat("you gave" + str(damage) + "damage to the monster!")
			return connection.on_block_destroy(self, x, y, z, mode)
		
	return MonsterProtocol, MonsterConnection
