#-*-coding:utf-8-*-

"""
建築向け色作成スクリプト

コマンド
	/colorhandle
		色作成モードのON/OFF
	
	/createcolor [red:0~255] [green:0~255] [blue:0~255]
		RGBで指定した色を作成する
		この時、DEUCE君が手に持っているブロックの色は変わらないが、置いたブロックは指定した色で塗られる。
		指定したRGBコードのまま色ムラの影響を受けない色でブロックを置けるのが利点


色作成モードでできる行動
	色サンプル作成
		ブロックを持って空中に向かって右クリック
		作成中の色のブロックを置くことができる。
		作成した色を使いたい場合は[E]キーで色抽出をしてください。
		※このサンプルブロックにも色ムラがあるので同じRGBで作成しても毎回同じではない
	
	色を足す
		[Shift]キー（長押しで連続変更）
		今指定している色（赤、緑、青）の光を追加する
	
	色を減らす
		[Ctrl]キー（長押しで連続変更）
		今指定している色（赤、緑、青）の光を減らす
	
	指定色を変更する
		[V]キー
		[Shift][Ctrl]で増減する色を変更する
		┌→赤→緑→青┐
		└――――――┘



バージョン情報
	ver1.0.0（2019.07.07）
		新規作成
	
	ver2.0.0（2019.11.26）
		サーバとクライアントで色を別管理している影響で
		画面上の見た目のブロックカラーとサーバが記録してる色が違うという問題があり
		色情報の持たせ方を変えた
		
		それに伴って色の繁栄方法を2通りに分ける
		１、Shift｜Ctrlで微調整する
			→Eキー抽出で手元のブロックカラーに反映する。クライアントの仕様で色ムラの影響を受ける。
		２、RGBコード指定で色を作る
			→ブロックを置くときに指定した色で塗り替える。手元のブロックと違う色のブロックを置く形になる。

"""

from pyspades.constants import *
from easyaos import *
from commands import add, name, alias, admin
from pyspades.server import block_action, orientation_data, grenade_packet, weapon_reload, set_tool, create_player
from pyspades import world, contained
from twisted.internet.reactor import callLater, seconds

MODES = ("red", "green", "blue")


"""
色編集モードのON/OFF
"""
@alias('clh')
@name('colorhandle')
def colorhandle(player):
	player.color_handling = not player.color_handling
	if player.color_handling:
		player.send_chat('selected color is ' + MODES[player.mode])
		player.send_chat('Block color handling mode ON')
	else:
		player.send_chat('Block color handling mode OFF')
add(colorhandle)

"""
RGB指定で色を生成
"""
@alias('crc')
@name('createcolor')
def createcolor(*arguments):
	player = arguments[0]
	
	if len(arguments) != 4:
		player.send_chat('Ex /createcolor 128 223, 255')
		player.send_chat('Enter red, green and blue')
		return
	
	red = int(arguments[1])
	green = int(arguments[2])
	blue = int(arguments[3])
	player.color = (red, green, blue)
	player.sample_color = player.color
	player.put_and_draw = True
	update_sample_color(player)
	player.send_chat('Put&Draw is enabled')
add(createcolor)

"""
プレイヤーが色編集モード中か判定
"""
def is_color_making(player):
	if player.tool == BLOCK_TOOL and player.color_handling:
		return True
	else:
		return False

"""
ブロックを持って右クリックで色のサンプルブロックを配置する
"""
def set_sample(player):
	if not player.moving_sample:
		return
	
	x, y, z = player.world_object.position.get()
	vx, vy, vz = player.world_object.orientation.get()
	dx = x + 3 * vx
	dy = y + 3 * vy
	dz = z + 3 * vz
	if dz < 0 or dz >= 62:
		return
	if dx < 0 or dx >= 512:
		return
	if dy < 0 or dy >= 512:
		return
	
	if not player.protocol.map.get_solid(dx, dy, dz):
		if player.sample_pos is not None:
			easyremove(player, player.sample_pos)
		player.sample_pos = (dx, dy, dz)
		easyblock(player, player.sample_pos, player.sample_color)

"""
ブロックの色を変更する
"""
def change_color(player):
	red, green, blue = player.sample_color
	colorList = [red, green, blue]
	color = colorList[player.mode]
	
	if player.color_change_brighten:
		color += 1
	if player.color_change_darken:
		color -= 1
	color %= 256
	
	colorList[player.mode] = color
	red, green, blue = colorList
	player.send_chat('(R:%d, G:%d, B:%d)'%(int(red), int(green), int(blue)))
	player.sample_color = (red, green, blue)
	update_sample_color(player)

"""
ShiftキーかCtrlキー長押しで色を高速で変更する
"""
def change_color_frequently(player):
	if is_color_making:
		if player.current_tap_num - player.before_tap_num == 0:
			return
		if player.current_tap_num - player.before_tap_num > 1:
			player.before_tap_num += 1
			return
		if player.current_tap_num - player.before_tap_num == 1:
			if player.color_change_brighten or player.color_change_darken:
				
				change_color(player)
				callLater(0.1, change_color_frequently, player)
			else:
				player.current_tap_num = 0
				player.before_tap_num = 0
	else:
		player.current_tap_num = 0
		player.before_tap_num = 0
	

"""
サンプルブロックの色を更新する
"""
def update_sample_color(player):
	if player.sample_pos is None:
		return
	x, y, z = player.sample_pos
	if player.protocol.map.get_solid(x, y, z):
		easyremove(player, player.sample_pos)
		easyblock(player, player.sample_pos, player.sample_color)

def apply_script(protocol, connection, config):
	
	class ColorHandleConnection(connection):
		color_handling = False
		put_and_draw = False
		
		# 0:red, 1:green, 2:blue
		mode = 0
		
		moving_sample = False
		sample_pos = None
		sample_color = (128, 128, 128)
		
		current_tap_num = 0
		before_tap_num = 0
		color_change_brighten = False
		color_change_darken = False
		
		def on_block_build_attempt(self, x, y, z):
			if self.put_and_draw:
				easyblock(self, (x,y,z), self.sample_color)
				return False
			return connection.on_block_build(self, x, y, z)
		
		def on_line_build_attempt(self, points):
			if self.put_and_draw:
				for point in points:
					easyblock(self, point, self.sample_color)
				return False
			return connection.on_line_build_attempt(self, points)
		
		def on_animation_update(self, jump, crouch, sneak, sprint):
			if is_color_making(self):
				self.color_change_brighten = sprint
				self.color_change_darken = crouch
				
				if sprint or crouch:
					change_color(self)
					self.current_tap_num += 1
					callLater(0.5, change_color_frequently, self)
					callLater(2.05, change_color_frequently, self)
					callLater(3.625, change_color_frequently, self)
					callLater(3.675, change_color_frequently, self)
				
				if sneak:
					self.mode = (self.mode + 1) % 3
					self.current_tap_num = 0
					self.before_tap_num = 0
					self.send_chat('selected color is ' + MODES[self.mode])
					self.send_chat('color selection has been changed')
					
					
			return connection.on_animation_update(self, jump, crouch, sneak, sprint)
		
		def on_secondary_fire_set(self, secondary):
			if secondary and is_color_making(self):
				self.moving_sample = True
				set_sample(self)
			else:
				self.moving_sample = False
			return connection.on_secondary_fire_set(self, secondary)
		
		def on_color_set(self, color):
			if self.put_and_draw:
				self.send_chat('Put&Draw is unenabled')
				self.put_and_draw = False
			self.sample_color = color
			update_sample_color(self)
			return connection.on_color_set(self, color)
	
	return protocol, ColorHandleConnection
