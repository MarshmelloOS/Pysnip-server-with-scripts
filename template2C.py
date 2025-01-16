# -*- coding: utf-8 -*-
"""
スクリプト初心者支援用テンプレート
第二回
コマンド入力で動作する系スクリプトのテンプレート


佐藤裕也

"""
#ここからスクリプト


from pyspades.constants import *
from commands import alias,add
from commands import admin, add, name #これはadminとかaddとかnameとか、AoS特有のやつをデータフォルダからインポートしてる　adminとか使うなら入れよう

@alias('ti')			#エイリアス：コマンドが長いやつを省略する奴/medkit→/m /airstrike→/aなど　この場合/tiで発動
@name('otimmpo')		#コマンド名：/otimmpoで発動
def otimmpo(connection):
	connection.send_chat("otimmpo haeta wwwwwwwwwww")	#connectionさんのチャット欄に文章が表示されるよ（この場合connection=コマンド打った人）
	connection.tinko()	#connectionの名のもとに関数tinkoが発動されるよ
	return "otimmpo haeta"		#スクリプトが正常動作したらコンソール画面とconnection氏のチャット欄に文章が表示されるよ
add(otimmpo)			#よくわかんないけどとりあえず入れよう




def apply_script(protocol,connection,config):

	class TintinConnection(connection):
		def tinko(self):		#飛んできたよ　self=connectionになったよ
			print "tinpoppo"	#コンソールに文章が表示されるよ

	return protocol, TintinConnection

