"""
OSExclusive.py
Kicks a player when they join a team if they're using a client
other than OpenSpades. They can still spectate.

Based on detectclient.py by noway421 (Good work man :D)
Modified by Kippykip
"""

from pyspades.constants import *
from pyspades.loaders import Loader
from pyspades.bytes import ByteReader, ByteWriter
from twisted.internet.reactor import callLater
from commands import name, add, get_player, join_arguments, InvalidPlayer
from collections import namedtuple
import itertools
from twisted.internet.reactor import seconds
from scheduler import Scheduler

id_iter = itertools.count(31)  # http://github.com/yvt/openspades/commit/aa62a0

S_VANILLAKICK = 'This server is OpenSpades exclusive!'                                                  # Reason for kick
V_EXPLAINFORKICK = True                                                                                    # Tell them why they're being kicked?
S_VANILLAMSG1 = 'You need the OpenSpades client to join this server! You will be kicked in 5 seconds!'  # 1nd explaining message
S_VANILLAMSG2 = 'You can get it at: https://github.com/yvt/openspades/releases/tag/v0.0.12'             # 2nd explaining message


class HandShakeInit(Loader):
    id = id_iter.next()

    def read(self, reader):
        pass

    def write(self, writer):
        writer.writeByte(self.id, True)
        writer.writeInt(42, True)


class HandShakeReturn(Loader):
    id = id_iter.next()

    challenge_passed = -1

    def read(self, reader):
        tmp = reader.readInt(True)
        if tmp == 42:
            self.challenge_passed = 1
        else:
            self.challenge_passed = 0

    def write(self, writer):
        writer.writeByte(self.id, True)


class VersionGet(Loader):
    id = id_iter.next()

    def read(self, reader):
        pass

    def write(self, writer):
        writer.writeByte(self.id, True)


class VersionSend(Loader):
    id = id_iter.next()

    client = ord('-')
    version_major = -1
    version_minor = -1
    version_revision = -1
    version_info = 'None'

    def read(self, reader):
        self.client = reader.readByte(True)
        self.version_major = reader.readByte(True)
        self.version_minor = reader.readByte(True)
        self.version_revision = reader.readByte(True)
        self.version_info = reader.readString()

    def write(self, writer):
        writer.writeByte(self.id, True)


def apply_script(protocol, connection, config):
    class DetectclientConnection(connection):
        def loader_received(self, loader):
            if self.player_id is not None:
                if self.hp:  # atleast player spawned
                    data = ByteReader(loader.data)
                    packet_id = data.readByte(True)
                    if packet_id == HandShakeReturn.id:
                        handshake_return = HandShakeReturn()
                        handshake_return.read(data)
                        self.on_handshake_answer()
                        return None
                    elif packet_id == VersionSend.id:
                        version_send = VersionSend()
                        version_send.read(data)
                        self.on_version_answer(version_send)
                        return None
            return connection.loader_received(self, loader)

        def on_spawn(self, pos):
            self.protocol.send_contained(HandShakeInit(), save=True)
            self.handshake_timer = callLater(1.4, self.handshake_timeout)
            return connection.on_spawn(self, pos)

        def handshake_timeout(self):
            # just assume it's vanilla
            info = namedtuple(
                'Info',
                'client, version_major, version_minor, ' +
                'version_revision, version_info')
            info.client = ord('a')
            info.version_major = 0
            info.version_minor = 75
            info.version_revision = 0
            info.version_info = 'Windows'
            self.on_version_get(info)

        def on_handshake_answer(self):
            if self.handshake_timer.active():
                self.handshake_timer.cancel()
            self.protocol.send_contained(VersionGet(), save=True)

        def on_version_answer(self, info):
            self.on_version_get(info)

        def kick_non_os(self):
            self.kick(reason=S_VANILLAKICK, silent=False)

        def sendmsg_non_os(self):
            self.send_chat(S_VANILLAMSG2)
            self.send_chat(S_VANILLAMSG1)

        def globalcunt(self):
            schedule = Scheduler(protocol)
            schedule.call_later(15, self.send_chat("aSSy"))

        def on_version_get(self, info):
            if chr(info.client) != 'o':  # If you're not on OpenSpades, kill him, send a message and kick them(a = Ace Of Spades classic, o = OpenSpades)
                #victim = get_player(self.protocol, '#' + str(self.player_id))  # Get the player by its ID
                if V_EXPLAINFORKICK == True:
                    self.globalcunt()
                    #self.gaylol = task.deferLater(1, self.kill) # Kill the player over and over for a few times
                    #self.kill()
                    #threading.Timer(1.0, self.kill())
                    #threading.Timer(2.0, self.kill())
                    #threading.Timer(3.0, self.kill())
                    #threading.Timer(4.0, self.kill())

                    #schedule.reset()
                    #schedule = None
                    #self.evengayer = task.deferLater(5, self.kick_non_os) # Finally kick the player
                else:
                    self.kick_non_os()

    class DetectclientProtocol(protocol):
        def __init__(self, *arg, **kw):
            return protocol.__init__(self, *arg, **kw)

    return DetectclientProtocol, DetectclientConnection