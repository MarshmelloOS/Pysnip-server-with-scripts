import math
import random
from pyspades.constants import *
from pyspades.common import make_color
from pyspades.contained import BlockAction, SetColor
from twisted.internet import task

# User Inputs
ANTI_LAG_LINE = True
ANTI_LAG_LIMIT = 5

PALETTE_TOGGLE = True
PALETTE_PLAYER = [
    (255, 31, 31),
    (255, 143, 31),
    (255, 255, 31),
    (31, 255, 31),
    (31, 255, 255),
    (31, 31, 255),
    (255, 31, 255)
]

GLOW_RECORDING = False
ALWAYS_GLOW = False

MAP_IS_GLOW = False
DISABLED_USERS_GLOW = []

VOXEL_PROC_GLOW = {}
STORED_COLORS = {}

# Functions
def empty_lights(a, b, c, map, is_palette):
    re, ge, be = map.get_color(a, b, c)
    if is_palette:
        sub = 1
    else:
        sub = 25
    add = (a, b, c)
    VOXEL_PROC_GLOW[add] = (re - sub, ge - sub, be - sub)
    if add not in STORED_COLORS:
        STORED_COLORS[add] = (re - sub, ge - sub, be - sub)

def process_voxels(map):
    entry_list = list(VOXEL_PROC_GLOW.items())
    randomVox = random.choice(entry_list)
    VOXEL_PROC_GLOW.pop(randomVox[0])
    p = randomVox[0]
    RGB = randomVox[1]
    if map.get_solid(p[0], p[1], p[2]):
        set_color = SetColor()
        set_color.value = make_color(RGB[0], RGB[1], RGB[2])
        set_color.player_id = 33
        map.change_blocks(p, p, set_color.value)
        map.queue_task(0.1, process_voxels, map)

def trigger(map, countType):
    for i in range(countType):
        map.queue_task(i * 0.005, process_voxels, map)

def apply_glow_block_user(protocol, a, b, c, value, tolerance, map):
    R1, G1, B1 = map.get_color(a, b, c)
    voxel_selection_user = []
    toleranceVal = 2

    for ac in range(a - tolerance, a + tolerance):
        for bc in range(b - tolerance, b + tolerance):
            for cc in range(c - tolerance, c + tolerance):
                chk = (ac, bc, cc)
                if chk in STORED_COLORS and 255 in STORED_COLORS[chk]:
                    toleranceVal += 1

    for a2 in range(a - value, a + value):
        for b2 in range(b - value, b + value):
            for c2 in range(c - value, c + value):
                if map.get_solid(a2, b2, c2):
                    result = (a2, b2, c2)
                    voxel_selection_user.append(result)

    for p in voxel_selection_user:
        R2, G2, B2 = map.get_color(p[0], p[1], p[2])
        distance = math.sqrt((p[0] - a) ** 2 + (p[1] - b) ** 2 + (p[2] - c) ** 2)
        if distance > value:
            continue
        if not map.is_surface(p[0], p[1], p[2]):
            continue
        else:
            if R2 == 0 and G2 == 0 and B2 == 0:
                R2, G2, B2 = (103, 64, 40)
            if p not in STORED_COLORS:
                STORED_COLORS[p] = (R2, G2, B2)
            if p in VOXEL_PROC_GLOW:
                R3 = int(VOXEL_PROC_GLOW[p][0] + (R1 - (distance / value) * R1) / toleranceVal - 1)
                G3 = int(VOXEL_PROC_GLOW[p][1] + (G1 - (distance / value) * G1) / toleranceVal - 1)
                B3 = int(VOXEL_PROC_GLOW[p][2] + (B1 - (distance / value) * B1) / toleranceVal - 1)
            else:
                R3 = int(R2 + (R1 - (distance / value) * R1) / toleranceVal - 1)
                G3 = int(G2 + (G1 - (distance / value) * G1) / toleranceVal - 1)
                B3 = int(B2 + (B1 - (distance / value) * B1) / toleranceVal - 1)
            if R3 > 254:
                R3 = 254
            if G3 > 254:
                G3 = 254
            if B3 > 254:
                B3 = 254
            if R3 < 0:
                R3 = 0
            if G3 < 0:
                G3 = 0
            if B3 < 0:
                B3 = 0
            if 255 not in map.get_color(p[0], p[1], p[2]):
                VOXEL_PROC_GLOW[p] = (R3, G3, B3)

def apply_script(connection_class, config):
    class GlowConnection(connection_class):
        def on_block_build(self, x, y, z):
            if MAP_IS_GLOW:
                map = self.protocol.map
                color = map.get_color(x, y, z)
                p2 = (x, y, z)
                if PALETTE_TOGGLE and color in PALETTE_PLAYER:
                    return connection_class.on_block_build(self, x, y, z)
                else:
                    if 255 in color:
                        STORED_COLORS[p2] = color
                        apply_glow_block_user(self.protocol, x, y, z, 7, 5, map)
                        return connection_class.on_block_build(self, x, y, z)
                    else:
                        STORED_COLORS[p2] = color
                        apply_glow_block_user(self.protocol, x, y, z, 7, 5, map)
                        return connection_class.on_block_build(self, x, y, z)
            else:
                return connection_class.on_block_build(self, x, y, z)

    return GlowConnection, config

