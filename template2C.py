# -*- coding: utf-8 -*-
"""
�X�N���v�g���S�Ҏx���p�e���v���[�g
����
�R�}���h���͂œ��삷��n�X�N���v�g�̃e���v���[�g


�����T��

"""
#��������X�N���v�g


from pyspades.constants import *
from commands import alias,add
from commands import admin, add, name #�����admin�Ƃ�add�Ƃ�name�Ƃ��AAoS���L�̂���f�[�^�t�H���_����C���|�[�g���Ă�@admin�Ƃ��g���Ȃ����悤

@alias('ti')			#�G�C���A�X�F�R�}���h����������ȗ�����z/medkit��/m /airstrike��/a�Ȃǁ@���̏ꍇ/ti�Ŕ���
@name('otimmpo')		#�R�}���h���F/otimmpo�Ŕ���
def otimmpo(connection):
	connection.send_chat("otimmpo haeta wwwwwwwwwww")	#connection����̃`���b�g���ɕ��͂��\��������i���̏ꍇconnection=�R�}���h�ł����l�j
	connection.tinko()	#connection�̖��̂��ƂɊ֐�tinko������������
	return "otimmpo haeta"		#�X�N���v�g�����퓮�삵����R���\�[����ʂ�connection���̃`���b�g���ɕ��͂��\��������
add(otimmpo)			#�悭�킩��Ȃ����ǂƂ肠��������悤




def apply_script(protocol,connection,config):

	class TintinConnection(connection):
		def tinko(self):		#���ł�����@self=connection�ɂȂ�����
			print "tinpoppo"	#�R���\�[���ɕ��͂��\��������

	return protocol, TintinConnection

