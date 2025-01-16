"""
detectclient.py

Author: noway421
License: CC-BY-SA

"""

from pyspades.constants import *
from pyspades.loaders import Loader
from pyspades.bytes import ByteReader, ByteWriter
from commands import add, alias, admin, get_player
from twisted.internet.reactor import callLater

from collections import namedtuple
import itertools

id_iter = itertools.count(31)  # http://github.com/yvt/openspades/commit/aa62a0


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
        answer = reader.readInt(True)
        if answer == 42:
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


def formatted_client_info(self, whom):
    return "%s running %s v%d.%d.%d on %s" % (
        whom,
        ('Ace of Spades' if chr(self.client_info.client) == 'a' else
            'OpenSpades' if chr(self.client_info.client) == 'o' else
            'Unknown'),
        self.client_info.version_major,
        self.client_info.version_minor,
        self.client_info.version_revision,
        self.client_info.version_info)


@alias('clin')
@admin
def client_info(connection, player):
    player = get_player(connection.protocol, player)
    return formatted_client_info(player, player.name)
add(client_info)


def apply_script(protocol, connection, config):

    class DetectclientConnection(connection):
        def loader_received(self, loader):
            if self.player_id is not None:  # atleast player spawned
                if not self.completed_version_challenge:
                    data = ByteReader(loader.data)
                    packet_id = data.readByte(True)
                    if packet_id == HandShakeReturn.id:
                        handshake_return = HandShakeReturn()
                        handshake_return.read(data)
                        if handshake_return.challenge_passed == 1:
                            self.on_handshake_answer()
                        return None
                    elif packet_id == VersionSend.id:
                        versend = VersionSend()
                        versend.read(data)
                        self.on_version_answer(versend)
                        return None
            return connection.loader_received(self, loader)

        def on_connect(self):
            if not hasattr(self, 'client_info'):
                self.client_info = namedtuple(
                    'Info',
                    'client, version_major, version_minor, ' +
                    'version_revision, version_info')
                self.client_info.client = ord('-')
                self.client_info.version_major = -1
                self.client_info.version_minor = -1
                self.client_info.version_revision = -1
                self.client_info.version_info = 'Pending'

            self.completed_version_challenge = False
            return connection.on_connect(self)

        def on_spawn(self, pos):
            if not self.completed_version_challenge:
                self.send_contained(HandShakeInit())
                self.handshake_timer = callLater(1.4, self.handshake_timeout)
            return connection.on_spawn(self, pos)

        def handshake_timeout(self):
            # just assume it's vanilla
            self.client_info.client = ord('a')
            self.client_info.version_major = 0
            self.client_info.version_minor = 75
            self.client_info.version_revision = 0
            self.client_info.version_info = 'Windows'
            self.on_version_get()

        def on_handshake_answer(self):
            if self.handshake_timer.active():
                self.handshake_timer.cancel()
            self.send_contained(VersionGet())

        def on_version_answer(self, info):
            self.client_info.client = info.client
            self.client_info.version_major = info.version_major
            self.client_info.version_minor = info.version_minor
            self.client_info.version_revision = info.version_revision
            self.client_info.version_info = info.version_info
            self.on_version_get()

        def on_version_get(self):
            self.completed_version_challenge = True
            self.send_chat(formatted_client_info(self, "You're"))

    class DetectclientProtocol(protocol):
        def __init__(self, *arg, **kw):
            return protocol.__init__(self, *arg, **kw)

    return DetectclientProtocol, DetectclientConnection
