#-*-coding:utf-8-*-
"""
���Ƃ����C���e���������I�ɍŏ��̈ʒu�܂Ŗ߂�X�N���v�g


ALWAYS_RETURN��True�ɂ���ƃC���e���𗎂Ƃ������Ƀ��^�[��
False�ɂ���Ɛ��̒��ɗ��Ƃ������������^�[��

RETURN_DELAY�̓C���e���𗎂Ƃ��Ă��烊�^�[������܂ł̗P�\����
0�ɂ���Ƒ����Ƀ��^�[��

RETURN_DELAY_IN_WATER�͐��ɗ��Ƃ������̗̂P�\����

SPAWN_ON_TOP�͒n�`�̈�ԍ����Ƃ���ɃX�|�[�����邩�ǂ����B
True�ɂ���ƒ��_�ɃX�|�[���B
False���ƌ��̍����ɃX�|�[�����邪�A
�n�`���ς���Ă����ꍇ�C���e�����n���ɖ��܂��Ă��܂��ꍇ������B
"""


from pyspades.constants import *
from pyspades.common import Vertex3, coordinates
from pyspades import world
from commands import add, admin, name, alias, join_arguments
from twisted.internet.reactor import callLater, seconds


ALWAYS_RETURN = True
RETURN_DELAY = 60
RETURN_DELAY_IN_WATER = 5
SPAWN_ON_TOP = False

INTEL_POSITION_GREEN = [0, 0, 0]
INTEL_POSITION_BLUE = [0, 0, 0]

MESSAGE_RETURNING = "Intel is going to return in {delay_time} seconds"
COUNT = "{time}"


def countTime(connection, left, flag):
    if flag.player == None:
        if left > 0:
            if left > 30 and left%10 == 0:
                connection.protocol.send_chat(COUNT.format(time = left), global_message = False)
                callLater(10, countTime, connection, left-10, flag)
            elif left <= 30 and left > 5 and left%5 == 0:
                connection.protocol.send_chat(COUNT.format(time = left), global_message = False)
                callLater(5, countTime, connection, left-5, flag)
            elif left <= 5:
                connection.protocol.send_chat(COUNT.format(time = left), global_message = False)
                callLater(1, countTime, connection, left-1, flag)
            else:
                callLater(1, countTime, connection, left-1, flag)
        else:
            connection.protocol.returnIntel(flag)


def apply_script(protocol, connection, config):
    class IntelAutoReturnProtocol(protocol):
        def on_flag_spawn(self, x, y, z, flag, entity_id):
            if entity_id == GREEN_FLAG:
                INTEL_POSITION_GREEN[0] = x
                INTEL_POSITION_GREEN[1] = y
                INTEL_POSITION_GREEN[2] = z
            elif entity_id == BLUE_FLAG:
                INTEL_POSITION_BLUE[0] = x
                INTEL_POSITION_BLUE[1] = y
                INTEL_POSITION_BLUE[2] = z
            return protocol.on_flag_spawn(self, x, y, z, flag, entity_id)
            

        def returnIntel(self, flag):
            if flag.player == None:
                if flag.team == self.green_team:
                    x, y, z = INTEL_POSITION_GREEN
                elif flag.team == self.blue_team:
                    x, y, z = INTEL_POSITION_BLUE
                else:
                    return
                if SPAWN_ON_TOP:
                    z = self.map.get_z(x, y, 0)
                pos = (x, y, z)
                flag.set(*pos)
                flag.update()
                self.send_chat("Intel returned")
                print("intel returned")
                return
    
    class IntelAutoReturnConnection(connection):
        def on_flag_drop(self):
            x, y, z = self.get_location()
            z = self.protocol.map.get_z(x, y, z)
            if ALWAYS_RETURN or z >= 63:
                flag = self.team.other.flag
                if z >= 63:
                    delay = RETURN_DELAY_IN_WATER
                else:
                    delay = RETURN_DELAY
                if delay > 0:
                    self.protocol.send_chat(MESSAGE_RETURNING.format(delay_time = delay), global_message = False)
                callLater(1, countTime, self, delay - 1, flag)
    
    
    return IntelAutoReturnProtocol, IntelAutoReturnConnection