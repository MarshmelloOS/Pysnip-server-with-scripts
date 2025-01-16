"""
/refresh r=None g=None b=None range=15 r2=None g2=None b2=None
/refresh2 range=15 r2=None g2=None b2=None
Must be loaded with "mapmakingtools.py".
Maintainer: crasive
"""

from pyspades.constants import *
from commands import add, admin, name, alias, join_arguments
from math import *
from twisted.internet.task import LoopingCall

TASK_INTERVAL = 0.1
TASK_QUANTITY = 5000
TASK_PROGRESS_INTERVAL = 5.0

PALETTE = [
    [15, 15, 15], [47, 47, 47], [79, 79, 79], [111, 111, 111], [143, 143, 143], [175, 175, 175], [207, 207, 207], [239, 239, 239],
    [31, 0, 0], [95, 0, 0], [159, 0, 0], [223, 0, 0], [255, 31, 31], [255, 95, 95], [255, 159, 159], [255, 223, 223],
    [31, 31, 0], [95, 95, 0], [159, 159, 0], [223, 223, 0], [255, 255, 31], [255, 255, 95], [255, 255, 159], [255, 255, 223],
    [0, 31, 0], [0, 95, 0], [0, 159, 0], [0, 223, 0], [31, 255, 31], [95, 255, 95], [159, 255, 159], [223, 255, 223],
    [0, 31, 31], [0, 95, 95], [0, 159, 159], [0, 223, 223], [31, 255, 255], [95, 255, 255], [159, 255, 255], [223, 255, 255],
    [0, 0, 31], [0, 0, 95], [0, 0, 159], [0, 0, 223], [31, 31, 255], [95, 95, 255], [159, 159, 255], [223, 223, 255],
    [31, 0, 31], [95, 0, 95], [159, 0, 159], [223, 0, 223], [255, 31, 255], [255, 95, 255], [255, 159, 255], [255, 223, 255],
    [31, 15, 0], [95, 47, 0], [159, 79, 0], [223, 111, 0], [255, 143, 31], [255, 175, 95], [255, 207, 159], [255, 239, 223]]

@alias('re2')
@name('refresh2')
@admin
def refresh2(*arguments):
    connection = arguments[0]
    connection.reset_build()
    connection.callback = refresh2_r
    connection.arguments = arguments
    connection.select = True
    connection.points = 2
    connection.send_chat('Color [%d %d %d] has been selected.' % (connection.color[0], connection.color[1], connection.color[2]))
    connection.send_chat('Select 2 blocks to determine the region to be refreshed')

add(refresh2)

def refresh2_r(connection, range=15, r2=None, g2=None, b2=None):
    connection.tasks.insert(0,RefreshTask(connection.protocol, 
        connection.block1_x, connection.block1_y, connection.block1_z,
        connection.block2_x, connection.block2_y, connection.block2_z,
        connection.color, range, [r2, g2, b2]))
    connection.refreshCycleStart()

@alias('re')
@name('refresh')
@admin
def refresh(*arguments):
    connection = arguments[0]
    connection.reset_build()
    connection.callback = refresh_r
    connection.arguments = arguments
    connection.select = True
    connection.points = 2
    connection.send_chat('Select 2 blocks to determine the region to be refreshed')

add(refresh)

def refresh_r(connection, r=None, g=None, b=None, range=15, r2=None, g2=None, b2=None):
    connection.tasks.insert(0,RefreshTask(connection.protocol, 
        connection.block1_x, connection.block1_y, connection.block1_z,
        connection.block2_x, connection.block2_y, connection.block2_z,
        [r, g, b], range, [r2, g2, b2]))
    connection.refreshCycleStart()

class RefreshTask:
    def __init__(self, protocol, x1, y1, z1, x2, y2, z2, color1, range, color2):
        self.protocol = protocol
        self.x1 = min(x1,x2)
        self.y1 = min(y1,y2)
        self.z1 = min(z1,z2)
        self.x2 = max(x1,x2)+1
        self.y2 = max(y1,y2)+1
        self.z2 = max(z1,z2)+1
        self.x = self.x1
        self.y = self.y1
        self.z = self.z1
        self.range=int(range)
        if None in color1:
            self.color1 = None
            self.color2 = None
        else:
            self.color1 = [int(color1[0]), int(color1[1]), int(color1[2])]
            if None in color2:
                self.color2 = self.color1
            else:
                self.color2 = [int(color2[0]), int(color2[1]), int(color2[2])]
    
    def execute(self):
        done = 0
        while( done < TASK_QUANTITY and self.x<self.x2 ):
            while( done < TASK_QUANTITY and self.y<self.y2 ):
                while( done < TASK_QUANTITY and self.z<self.z2 ):
                    if self.protocol.map.get_solid(self.x, self.y, self.z):
                        (r, g, b) = self.protocol.map.get_point(self.x, self.y, self.z)[1]
                        if self.color1 == None:
                            isInPalette=False
                            for color in PALETTE:
                                if abs(color[0]-r)<=self.range and abs(color[1]-g)<=self.range and abs(color[2]-b)<=self.range:
                                    (r, g, b) = (color[0], color[1], color[2])
                                    isInPalette=True
                                    break
                            if not isInPalette:
                                r = max(int((r+8)/16)*16-1,0)
                                g = max(int((g+8)/16)*16-1,0)
                                b = max(int((b+8)/16)*16-1,0)
                        else:
                            if abs(self.color1[0]-r)<=self.range and abs(self.color1[1]-g)<=self.range and abs(self.color1[2]-b)<=self.range:
                                (r, g, b) = (self.color2[0], self.color2[1], self.color2[2])
                        self.protocol.map.set_point(self.x, self.y, self.z, (r, g, b, 255))
                    done += 1
                    self.z+=1
                if self.z >= self.z2:
                    self.z = self.z1
                    self.y += 1
            if self.y >= self.y2:
                self.y = self.y1
                self.x += 1
        if self.x >= self.x2 :
            return True
        return False

def apply_script(protocol, connection, config):
    class RefreshConnection(connection):
        tasks = []
        task = None
        progress = 0
        progressCount = 0
        totalTask = 0
        cycle_loop = None
        
        def refreshCycle(self):
            if len(self.tasks) <= 0:
                self.cycle_loop.stop()
            else:
                self.task = self.tasks.pop()
                if self.task.x==self.task.x1 and self.task.y==self.task.y1 and self.task.z==self.task.z1:
                    self.send_chat('Started [refresh]')
                    self.progress = 0
                    self.progressCount = 0
                    self.totalTask = (self.task.x2-self.task.x1)*(self.task.y2-self.task.y1)*(self.task.z2-self.task.z1)
                if self.task.execute():
                    self.send_chat('Finished [refresh]')
                else:
                    self.progressCount += 1
                    self.progress += TASK_QUANTITY
                    if self.progressCount >= TASK_PROGRESS_INTERVAL/TASK_INTERVAL:
                        self.progressCount = 0
                        self.send_chat('%d%% [refresh]' % (100*self.progress/self.totalTask))
                    self.tasks.append(self.task)
        
        def refreshCycleStart(self):
            if self.cycle_loop == None:
                self.cycle_loop = LoopingCall(self.refreshCycle)
            if not(self.cycle_loop and self.cycle_loop.running):
                self.cycle_loop.start(TASK_INTERVAL)
        
    return protocol, RefreshConnection